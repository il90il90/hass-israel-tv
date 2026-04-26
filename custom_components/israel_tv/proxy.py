"""Internal HLS proxy view for channels that require a Referer header.

YES Sport channels on lacasada.site block requests that do not carry the exact
Referer of the nextbet7.tv channel page (e.g. https://nextbet7.tv/kanal-izle/yes-1).
HA's ffmpeg-based stream component fetches the source URL without any Referer
header, so playback fails with HTTP 403/404.

This module registers a lightweight aiohttp view inside HA's HTTP server.
The view forwards GET requests to the real CDN while injecting the correct
Referer and Origin headers, then streams the response back to the caller.

Endpoint: /api/israel_tv/hls/{channel_id}

The shared store holds: channel_id → (real_cdn_url, source_page_url)
"""

from __future__ import annotations

import logging

import aiohttp
from aiohttp import web

from homeassistant.components.http import HomeAssistantView

_LOGGER = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class IsraelTVHLSProxyView(HomeAssistantView):
    """Proxy an HLS playlist URL, injecting the required Referer header.

    The shared store (keyed by channel_id) holds a tuple:
      (real_cdn_url, source_page_url)
    where source_page_url is the nextbet7.tv page URL used as Referer.
    """

    url = "/api/israel_tv/hls/{channel_id}"
    name = "api:israel_tv:hls"
    requires_auth = False  # ffmpeg fetches this internally on the same host

    def __init__(self, stream_urls: dict[str, tuple[str, str]]) -> None:
        """Initialize with a reference to the shared URL store."""
        self._stream_urls = stream_urls

    async def get(self, request: web.Request, channel_id: str) -> web.Response:
        """Fetch the m3u8 from the CDN with the correct Referer and return it."""
        entry = self._stream_urls.get(channel_id)
        if not entry:
            return web.Response(status=404, text="No stream URL cached for channel")

        real_url, page_url = entry

        # The CDN validates that Referer matches the embedding nextbet7.tv page.
        # Origin must also be set for the CORS pre-check the CDN performs.
        headers = {
            "User-Agent": _USER_AGENT,
            "Referer": page_url,
            "Origin": "https://nextbet7.tv",
            "Accept": "*/*",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    real_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                    allow_redirects=True,
                ) as resp:
                    if resp.status != 200:
                        _LOGGER.warning(
                            "CDN returned HTTP %s for channel %s (url=%s)",
                            resp.status,
                            channel_id,
                            real_url,
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
