"""YES Sport stream extractor with automatic token refresh.

YES Sport channels (yes-1 through yes-4) are served via nextbet7.tv.
Each page embeds an HLS playlist URL containing a short-lived token
(expires ~5-10 minutes). This module scrapes the page to extract a
fresh token and caches it to avoid unnecessary round-trips.

Flow:
  1. On first play, scrape the channel page and cache the URL.
  2. On subsequent plays, return the cached URL if it is still fresh.
  3. If the token has expired (or the player reports an error), a fresh
     scrape is performed transparently — no user action required.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Seconds before we proactively refresh the token.
# Tokens expire in ~5-10 min; refresh at 4 min to stay ahead.
TOKEN_TTL = 240

# nextbet7.tv page for each channel
CHANNEL_PAGES: dict[str, str] = {
    "yes1": "https://nextbet7.tv/kanal-izle/yes-1",
    "yes2": "https://nextbet7.tv/kanal-izle/yes-2",
    "yes3": "https://nextbet7.tv/kanal-izle/yes-3",
    "yes4": "https://nextbet7.tv/kanal-izle/yes-4",
}

# Headers that mimic a real browser — required by Cloudflare WAF
_SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
}

# The Referer that the CDN validates on every playlist/segment request
STREAM_REFERER = "https://nextbet7.tv/"

# Regex to extract <source src="..." type="application/x-mpegURL">
_SOURCE_RE = re.compile(
    r'<source\s+src="([^"]+)"[^>]*type="application/x-mpegURL"',
    re.IGNORECASE,
)


@dataclass
class _CacheEntry:
    url: str
    fetched_at: float = field(default_factory=time.monotonic)

    def is_fresh(self) -> bool:
        return time.monotonic() - self.fetched_at < TOKEN_TTL


# Module-level cache shared across all HA service calls
_cache: dict[str, _CacheEntry] = {}


async def get_stream_url(channel_id: str) -> str:
    """Return a valid (possibly cached) HLS playlist URL for the channel.

    Raises ValueError if the channel_id is unknown.
    Raises RuntimeError if the stream URL cannot be extracted.
    """
    if channel_id not in CHANNEL_PAGES:
        raise ValueError(f"Unknown YES Sport channel: {channel_id}")

    entry = _cache.get(channel_id)
    if entry and entry.is_fresh():
        _LOGGER.debug("Token cache hit for %s (age=%.0fs)", channel_id, time.monotonic() - entry.fetched_at)
        return entry.url

    _LOGGER.debug("Fetching fresh token for %s", channel_id)
    url = await _scrape(channel_id)
    _cache[channel_id] = _CacheEntry(url=url)
    return url


def invalidate_cache(channel_id: str) -> None:
    """Force a fresh scrape on the next play request (call on 403/404 errors)."""
    _cache.pop(channel_id, None)
    _LOGGER.debug("Token cache invalidated for %s", channel_id)


async def _scrape(channel_id: str) -> str:
    """Scrape the channel page and extract the HLS source URL."""
    page_url = CHANNEL_PAGES[channel_id]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                page_url,
                headers=_SCRAPE_HEADERS,
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=True,
            ) as resp:
                resp.raise_for_status()
                html = await resp.text()
    except aiohttp.ClientError as err:
        raise RuntimeError(f"Failed to fetch {page_url}: {err}") from err

    match = _SOURCE_RE.search(html)
    if not match:
        raise RuntimeError(
            f"Could not find HLS source URL in {page_url}. "
            "The page structure may have changed."
        )

    stream_url = match.group(1)
    _LOGGER.info("Extracted YES Sport stream for %s: %s", channel_id, stream_url)
    return stream_url
