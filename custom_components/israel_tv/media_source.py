"""Media Source implementation for Israel TV."""

from __future__ import annotations

import asyncio
import logging
import re

import aiohttp

from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant

from .channels import CATEGORY_LABELS, CHANNELS_BY_ID, Channel, get_channels_by_category
from .const import DOMAIN, HLS_MIME_TYPE, ROOT_ID

_LOGGER = logging.getLogger(__name__)

# Cache: channel_id → pinned low-bitrate URL, expires after this many seconds
_CACHE_TTL = 300
_url_cache: dict[str, tuple[str, float]] = {}


async def async_get_media_source(hass: HomeAssistant) -> IsraelTVMediaSource:
    """Return the Israel TV media source."""
    return IsraelTVMediaSource(hass)


async def _resolve_lowest_bitrate(master_url: str) -> str:
    """Fetch the master playlist and return the URL for the lowest-bitrate rendition.

    Pinning to a single low-bitrate rendition prevents the player from switching
    to a higher quality stream mid-playback, which is the main cause of stutter
    when CDN throughput barely matches the stream bitrate.
    Falls back to the master URL if parsing fails.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(master_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return master_url
                text = await resp.text()

        # Parse BANDWIDTH values and their associated URIs from the EXT-X-STREAM-INF lines
        entries: list[tuple[int, str]] = []
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-STREAM-INF"):
                match = re.search(r"BANDWIDTH=(\d+)", line)
                if match and i + 1 < len(lines):
                    bandwidth = int(match.group(1))
                    uri = lines[i + 1].strip()
                    if uri and not uri.startswith("#"):
                        entries.append((bandwidth, uri))

        if not entries:
            return master_url

        # Pick the rendition with the lowest bandwidth
        lowest_url = min(entries, key=lambda x: x[0])[1]
        _LOGGER.debug("Pinned to lowest rendition: %s", lowest_url)
        return lowest_url

    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        _LOGGER.warning("Could not resolve lowest bitrate for %s: %s", master_url, err)
        return master_url


class IsraelTVMediaSource(MediaSource):
    """Expose Israeli live TV channels through the HA Media Browser."""

    name = "Israel TV"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve a channel to its lowest-bitrate HLS rendition URL."""
        import time

        channel_id = item.identifier
        channel = CHANNELS_BY_ID.get(channel_id)
        if channel is None:
            raise ValueError(f"Unknown channel: {channel_id}")

        now = time.monotonic()
        cached = _url_cache.get(channel_id)
        if cached and now - cached[1] < _CACHE_TTL:
            url = cached[0]
            _LOGGER.debug("Cache hit for %s → %s", channel_id, url)
        else:
            url = await _resolve_lowest_bitrate(channel.url)
            _url_cache[channel_id] = (url, now)

        return PlayMedia(url, HLS_MIME_TYPE)

    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        """Browse categories or channels within a category."""
        identifier = item.identifier or ROOT_ID

        if identifier == ROOT_ID:
            return self._build_root()

        # identifier is a category key
        if identifier in CATEGORY_LABELS:
            return self._build_category(identifier)

        raise ValueError(f"Unknown media source path: {identifier}")

    # ── Builders ───────────────────────────────────────────────────────────────

    def _build_root(self) -> BrowseMediaSource:
        """Return the root node with one child per category."""
        children = [
            self._build_category_stub(cat, label)
            for cat, label in CATEGORY_LABELS.items()
            if get_channels_by_category(cat)  # skip empty categories
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
