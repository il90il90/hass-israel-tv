"""Media Source implementation for Israel TV."""

from __future__ import annotations

import logging

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
from . import yes_sport

_LOGGER = logging.getLogger(__name__)

# HA shows a built-in MDI icon automatically based on MediaClass.
# Map each category to the most representative class.
_CATEGORY_MEDIA_CLASS: dict[str, MediaClass] = {
    "broadcast":    MediaClass.CHANNEL,
    "sport":        MediaClass.CHANNEL,
    "sport_global": MediaClass.CHANNEL,
    "viva":         MediaClass.TV_SHOW,
    "reality":      MediaClass.TV_SHOW,
    "music":        MediaClass.MUSIC,
    "kids":         MediaClass.TV_SHOW,
    "lifestyle":    MediaClass.TV_SHOW,
    "movies":       MediaClass.MOVIE,
}


async def async_get_media_source(hass: HomeAssistant) -> IsraelTVMediaSource:
    """Return the Israel TV media source."""
    return IsraelTVMediaSource(hass)


class IsraelTVMediaSource(MediaSource):
    """Expose Israeli live TV channels through the HA Media Browser."""

    name = "Israel TV"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve a channel to a playable HLS URL.

        - Static channels (Sport 5, broadcasts, etc.) return the direct
          CloudFront CDN URL which is publicly accessible.
        - YES Sport channels are scraped from nextbet7.tv on demand, with
          the token cached for 4 minutes and refreshed transparently.
        """
        channel_id = item.identifier
        channel = CHANNELS_BY_ID.get(channel_id)
        if channel is None:
            raise ValueError(f"Unknown channel: {channel_id}")

        if channel.channel_type == "yes_sport":
            return await self._resolve_yes_sport(channel)

        return await self._resolve_static(channel)

    async def _resolve_yes_sport(self, channel: Channel) -> PlayMedia:
        """Resolve a YES Sport channel to our local HLS proxy URL.

        The local proxy at /api/israel_tv/stream/{id}/playlist.m3u8 fetches
        the CDN playlist with the required Referer header and rewrites all
        segment URLs to go through the proxy as well — bypassing both CORS
        restrictions and ffmpeg's non-standard extension filter.
        """
        proxy_url = f"/api/israel_tv/stream/{channel.id}/playlist.m3u8"
        _LOGGER.debug("YES Sport %s → local proxy %s", channel.id, proxy_url)
        return PlayMedia(proxy_url, HLS_MIME_TYPE)

    async def _resolve_static(self, channel: Channel) -> PlayMedia:
        """Return the direct CDN URL for playback.

        The free-TV CDN (CloudFront) is publicly accessible without special
        headers, so returning the URL directly is simpler and more reliable
        than routing through HA's ffmpeg stream proxy.
        """
        _LOGGER.debug("Serving static channel %s → %s", channel.id, channel.url)
        return PlayMedia(channel.url, HLS_MIME_TYPE)

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
        """Return a non-expanded category node (used inside the root listing).

        Uses a content-specific MediaClass so HA's frontend displays the
        matching MDI icon automatically — no external image needed.
        """
        media_class = _CATEGORY_MEDIA_CLASS.get(category, MediaClass.DIRECTORY)
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=category,
            media_class=media_class,
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
