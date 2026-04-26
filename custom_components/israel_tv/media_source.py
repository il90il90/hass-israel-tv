"""Media Source implementation for Israel TV."""

from __future__ import annotations

import asyncio
import logging
import re
import time

import aiohttp

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.components.stream import create_stream
from homeassistant.core import HomeAssistant

from .channels import CATEGORY_LABELS, CHANNELS_BY_ID, Channel, get_channels_by_category
from .const import DOMAIN, HLS_MIME_TYPE, ROOT_ID

_LOGGER = logging.getLogger(__name__)

# How long (seconds) a resolved YES Sport URL stays valid before re-extraction.
# Tokens from nextbet7.tv last ~2-4 hours; 90 minutes gives a safe margin.
_EXTRACTION_CACHE_TTL = 90 * 60

# cache: channel_id → (hls_url, timestamp)
_extraction_cache: dict[str, tuple[str, float]] = {}

# Browser-like headers required by nextbet7.tv to return the source tag
_NEXTBET_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,he;q=0.8",
    "Referer": "https://nextbet7.tv/",
}

# Regex patterns to find the HLS URL inside the page HTML
_SRC_PATTERNS = [
    re.compile(r'<source\s+src="([^"]+)"[^>]*type="application/x-mpegURL"', re.I),
    re.compile(r'type="application/x-mpegURL"[^>]*src="([^"]+)"', re.I),
    re.compile(r"['\"]?(https?://[^'\"]+\.m3u8[^'\"]*)['\"]?", re.I),
]


async def async_get_media_source(hass: HomeAssistant) -> IsraelTVMediaSource:
    """Return the Israel TV media source."""
    return IsraelTVMediaSource(hass)


async def _extract_hls_from_page(page_url: str) -> str | None:
    """Fetch a nextbet7.tv page and extract the embedded HLS stream URL.

    Returns the HLS URL string, or None if extraction fails.
    """
    try:
        async with aiohttp.ClientSession(headers=_NEXTBET_HEADERS) as session:
            async with session.get(
                page_url, timeout=aiohttp.ClientTimeout(total=12)
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning(
                        "Extraction page returned HTTP %s for %s", resp.status, page_url
                    )
                    return None
                html = await resp.text()

        for pattern in _SRC_PATTERNS:
            match = pattern.search(html)
            if match:
                url = match.group(1)
                _LOGGER.debug("Extracted HLS URL from %s: %s", page_url, url)
                return url

        _LOGGER.warning("No HLS source found in page: %s", page_url)
        return None

    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        _LOGGER.warning("Extraction request failed for %s: %s", page_url, err)
        return None


async def _get_channel_url(channel: Channel, *, force_refresh: bool = False) -> str:
    """Return the playable HLS URL for a channel.

    For regular channels returns the static CDN URL immediately.
    For extraction channels (needs_extraction=True):
      - Returns the cached URL if it is still within _EXTRACTION_CACHE_TTL.
      - Fetches a fresh URL from the source page otherwise.
      - force_refresh=True skips the cache (used for auto-recovery).
    """
    if not channel.needs_extraction:
        return channel.url

    now = time.monotonic()
    cached = _extraction_cache.get(channel.id)

    if not force_refresh and cached and (now - cached[1]) < _EXTRACTION_CACHE_TTL:
        _LOGGER.debug("Cache hit for %s (age=%.0fs)", channel.id, now - cached[1])
        return cached[0]

    _LOGGER.debug("Extracting fresh URL for %s", channel.id)
    fresh_url = await _extract_hls_from_page(channel.url)

    if fresh_url:
        _extraction_cache[channel.id] = (fresh_url, now)
        return fresh_url

    # Extraction failed — fall back to stale cache if available
    if cached:
        _LOGGER.warning(
            "Extraction failed for %s, using stale cached URL", channel.id
        )
        return cached[0]

    raise ValueError(f"Could not extract HLS URL for channel {channel.id}")


class IsraelTVMediaSource(MediaSource):
    """Expose Israeli live TV channels through the HA Media Browser."""

    name = "Israel TV"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve a channel to a locally buffered HLS stream.

        Flow:
          1. Get the channel's HLS URL (from cache or by extracting it fresh).
          2. Route it through HA's stream proxy (ffmpeg) so the browser receives
             locally buffered segments instead of fetching directly from the CDN.
          3. If the stream proxy fails (e.g. expired token mid-stream), force a
             fresh extraction and retry once before giving up.
          4. If the proxy is unavailable, fall back to the direct HLS URL.
        """
        channel_id = item.identifier
        channel = CHANNELS_BY_ID.get(channel_id)
        if channel is None:
            raise ValueError(f"Unknown channel: {channel_id}")

        hls_url = await _get_channel_url(channel)

        try:
            return await self._start_stream(channel, hls_url)
        except Exception:  # noqa: BLE001
            if channel.needs_extraction:
                # Token may have expired — force a fresh extraction and retry once
                _LOGGER.info(
                    "Stream failed for %s, refreshing token and retrying", channel.id
                )
                try:
                    hls_url = await _get_channel_url(channel, force_refresh=True)
                    return await self._start_stream(channel, hls_url)
                except Exception:  # noqa: BLE001
                    _LOGGER.warning(
                        "Retry also failed for %s, falling back to direct URL", channel.id
                    )
                    return PlayMedia(hls_url, HLS_MIME_TYPE)
            # Non-extraction channel — direct fallback
            _LOGGER.warning(
                "Stream proxy failed for %s, falling back to direct CDN URL", channel.id
            )
            return PlayMedia(hls_url, HLS_MIME_TYPE)

    async def _start_stream(self, channel: Channel, hls_url: str) -> PlayMedia:
        """Create an HA stream proxy for the given HLS URL and return its PlayMedia."""
        stream = create_stream(
            self.hass,
            hls_url,
            # 5-second output segments → ~15 s of browser buffer (3 segments).
            options={"segment_duration": 5},
            stream_label=channel.name_en,
        )
        url = await stream.async_url()
        _LOGGER.debug("Stream proxy active for %s → %s", channel.id, url)
        return PlayMedia(url, HLS_MIME_TYPE)

    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        """Browse categories or channels within a category."""
        identifier = item.identifier or ROOT_ID

        if identifier == ROOT_ID:
            return self._build_root()

        if identifier in CATEGORY_LABELS:
            return self._build_category(identifier)

        raise ValueError(f"Unknown media source path: {identifier}")

    # ── Builders ───────────────────────────────────────────────────────────────

    def _build_root(self) -> BrowseMediaSource:
        """Return the root node with one child per category."""
        children = [
            self._build_category_stub(cat, label)
            for cat, label in CATEGORY_LABELS.items()
            if get_channels_by_category(cat)
        ]
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=ROOT_ID,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.CHANNEL,
            title="Israel TV",
            can_play=False,
            can_expand=True,
            thumbnail="https://raw.githubusercontent.com/il90il90/hass-israel-tv/main/custom_components/israel_tv/icon.png",
            children=children,
        )

    def _build_category_stub(self, category: str, label: str) -> BrowseMediaSource:
        """Return a non-expanded category node (used inside the root listing)."""
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=category,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.CHANNEL,
            title=label,
            can_play=False,
            can_expand=True,
        )

    def _build_category(self, category: str) -> BrowseMediaSource:
        """Return a fully expanded category node with channel children."""
        label = CATEGORY_LABELS[category]
        channels = get_channels_by_category(category)
        children = [self._build_channel(ch) for ch in channels]
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=category,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.CHANNEL,
            title=label,
            can_play=False,
            can_expand=True,
            children=children,
        )

    def _build_channel(self, channel: Channel) -> BrowseMediaSource:
        """Return a leaf node for a single channel."""
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=channel.id,
            media_class=MediaClass.CHANNEL,
            media_content_type=MediaType.VIDEO,
            title=channel.name,
            can_play=True,
            can_expand=False,
            thumbnail=channel.thumbnail,
        )
