"""Stream extractor for premium Israeli channels, with automatic token refresh.

Sport 1-4 and a handful of other premium Israeli channels are not carried on
the public CloudFront CDN that serves the free-to-air channels. They are
resolved through a DaddyLive player page, which embeds the HLS URL as base64.

Flow:
  1. GET the player page with ``Referer: https://dlhd.st/`` — the page checks it.
  2. Extract ``window.atob('<base64>')`` and decode it → master playlist URL.
  3. Every following CDN request needs ``Referer: https://hamis.romponalis.st/``;
     without it the CDN answers ``403 Invalid Referer``.

The signed token's expiry is embedded in the URL path::

    https://<cdn>/three/secure/{md5}/{unix_expiry}/premium{id}/index.m3u8

so the cache refreshes on the real expiry (~3 hours) instead of guessing. Each
request mints a new token while previously issued ones keep working until they
expire, which is what makes refreshing mid-playback safe.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import re
import time
from dataclasses import dataclass

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Map our channel id → the numeric channel id used by the upstream player.
CHANNEL_IDS: dict[str, int] = {
    "yes1": 140,
    "yes2": 141,
    "yes3": 142,
    "yes4": 143,
    "sport_5_star": 147,
    "ch10": 547,
    "yes_movies_action": 543,
    "yes_movies_kids": 544,
    "sg_yes_network": 763,
}

_PLAYER_URL = "https://hamis.romponalis.st/premiumtv/daddy3.php?id={upstream_id}"

# The player page validates this Referer.
_PLAYER_REFERER = "https://dlhd.st/"

# The Referer the CDN validates on every playlist and segment request.
STREAM_REFERER = "https://hamis.romponalis.st/"

# Refresh this many seconds before the token's embedded expiry, so a playlist
# poll never lands on a token that expires while the response is in flight.
TOKEN_REFRESH_MARGIN = 300

# Used only when the URL carries no parsable expiry, so we still refresh.
FALLBACK_TOKEN_TTL = 2 * 3600

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": _PLAYER_REFERER,
}

_ATOB_RE = re.compile(r"window\.atob\(\s*['\"]([A-Za-z0-9+/=_-]+)['\"]\s*\)")
_EXPIRY_RE = re.compile(r"/secure/[^/]+/(\d{9,})/")


@dataclass
class _CacheEntry:
    """A resolved playlist URL and the wall-clock time its token expires."""

    url: str
    expires_at: float

    def is_fresh(self) -> bool:
        return time.time() < self.expires_at - TOKEN_REFRESH_MARGIN

    def seconds_left(self) -> int:
        return max(0, int(self.expires_at - time.time()))


# Module-level cache shared across all HA requests, plus one lock per channel so
# concurrent playlist polls near expiry refresh once instead of stampeding.
_cache: dict[str, _CacheEntry] = {}
_locks: dict[str, asyncio.Lock] = {}


async def get_stream_url(channel_id: str) -> str:
    """Return a valid (possibly cached) master playlist URL for the channel.

    Raises ValueError if the channel_id is unknown.
    Raises RuntimeError if the stream URL cannot be extracted.
    """
    upstream_id = CHANNEL_IDS.get(channel_id)
    if upstream_id is None:
        raise ValueError(f"Unknown channel: {channel_id}")

    entry = _cache.get(channel_id)
    if entry is not None and entry.is_fresh():
        return entry.url

    lock = _locks.setdefault(channel_id, asyncio.Lock())
    async with lock:
        # Another request may have refreshed while we waited for the lock.
        entry = _cache.get(channel_id)
        if entry is not None and entry.is_fresh():
            return entry.url

        url = await _extract(upstream_id)
        entry = _CacheEntry(url=url, expires_at=_parse_expiry(url))
        _cache[channel_id] = entry
        _LOGGER.debug(
            "Resolved %s (upstream %d), token valid for %ds",
            channel_id,
            upstream_id,
            entry.seconds_left(),
        )
        return entry.url


def invalidate_cache(channel_id: str) -> None:
    """Drop the cached token so the next request re-resolves it.

    Called when the CDN rejects a token we still believed was fresh.
    """
    if _cache.pop(channel_id, None) is not None:
        _LOGGER.debug("Token cache invalidated for %s", channel_id)


def _parse_expiry(url: str) -> float:
    """Return the token's expiry as a unix timestamp, read from the URL path."""
    match = _EXPIRY_RE.search(url)
    if match is None:
        _LOGGER.debug("No expiry in %s — falling back to a fixed TTL", url)
        return time.time() + FALLBACK_TOKEN_TTL
    return float(match.group(1))


async def _extract(upstream_id: int) -> str:
    """Fetch the player page and decode the embedded playlist URL."""
    player_url = _PLAYER_URL.format(upstream_id=upstream_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                player_url,
                headers=_HEADERS,
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=True,
            ) as resp:
                resp.raise_for_status()
                html = await resp.text()
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        raise RuntimeError(f"Failed to fetch {player_url}: {err}") from err

    match = _ATOB_RE.search(html)
    if match is None:
        raise RuntimeError(
            f"No stream URL found on {player_url}. "
            "The player page layout may have changed."
        )

    encoded = match.group(1)
    encoded += "=" * (-len(encoded) % 4)
    try:
        url = base64.b64decode(encoded).decode()
    except (ValueError, UnicodeDecodeError) as err:
        raise RuntimeError(f"Could not decode stream URL from {player_url}: {err}") from err

    if not url.startswith("http"):
        raise RuntimeError(f"Decoded stream URL is not usable: {url[:80]!r}")

    return url
