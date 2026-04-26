"""Internal HLS proxy view for channels that require a Referer header.

YES Sport channels on lacasada.site/zbahistv11.com block requests that do not
carry the correct Referer. HA's ffmpeg-based stream component fetches the
source URL without any Referer header, so playback fails.

This module registers a lightweight aiohttp view inside HA's HTTP server.
The view forwards GET requests to the real CDN while injecting the required
Referer, then streams the response back to the caller (ffmpeg / browser).

Endpoint pattern:
  /api/israel_tv/hls/{channel_id}          → m3u8 playlist
  /api/israel_tv/hls/{channel_id}/segment  → TS segment (if needed)
"""

from __future__ import annotations

import logging

import aiohttp
from aiohttp import web

from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Headers injected into every upstream CDN request
_PROXY_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://nextbet7.tv/",
    "Accept": "*/*",
    "Origin": "https://nextbet7.tv",
}


class IsraelTVHLSProxyView(HomeAssistantView):
    """Proxy an HLS playlist URL, injecting the required Referer header.

    The real stream URL is stored in a shared dict keyed by channel_id and
    updated by media_source.py every time a fresh token is extracted.
    """

    url = "/api/israel_tv/hls/{channel_id}"
    name = "api:israel_tv:hls"
    requires_auth = False  # ffmpeg fetches this internally on the same host

    def __init__(self, stream_urls: dict[str, str]) -> None:
        """Initialize with a reference to the shared URL store."""
        self._stream_urls = stream_urls

    async def get(self, request: web.Request, channel_id: str) -> web.Response:
        """Fetch the m3u8 from the CDN and return it to the caller."""
        real_url = self._stream_urls.get(channel_id)
        if not real_url:
            return web.Response(status=404, text="No stream URL cached for channel")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    real_url,
                    headers=_PROXY_HEADERS,
                    timeout=aiohttp.ClientTimeout(total=10),
                    allow_redirects=True,
                ) as resp:
                    if resp.status != 200:
                        _LOGGER.warning(
                            "CDN returned HTTP %s for channel %s", resp.status, channel_id
                        )
                        return web.Response(status=resp.status, text="CDN error")

                    content = await resp.read()
                    content_type = resp.content_type or "application/vnd.apple.mpegurl"
                    _LOGGER.debug(
                        "Proxied %d bytes for channel %s", len(content), channel_id
                    )
                    return web.Response(
                        body=content,
                        content_type=content_type,
                        headers={"Access-Control-Allow-Origin": "*"},
                    )

        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Proxy request failed for %s: %s", channel_id, err)
            return web.Response(status=502, text=str(err))
