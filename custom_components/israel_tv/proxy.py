"""Local HLS proxy for YES Sport channels.

YES Sport streams use non-standard segment extensions (.jpeg) that ffmpeg's
HLS demuxer refuses to download. We also need to inject a Referer header on
every CDN request. This module implements a lightweight aiohttp-based proxy
that the browser can fetch directly from localhost — solving both problems:

  1. No CORS errors (everything comes from http://localhost:8123).
  2. No ffmpeg extension restrictions (we proxy raw bytes ourselves).

Flow:
  Browser → GET /api/israel_tv/stream/{channel_id}/playlist.m3u8
           ↳  Proxy fetches m3u8 from CDN with Referer header
              Rewrites segment URLs to /api/israel_tv/stream/{id}/seg/{b64}
              Returns modified playlist to browser

  Browser → GET /api/israel_tv/stream/{channel_id}/seg/{encoded_url}
           ↳  Proxy fetches the segment from CDN with Referer header
              Streams raw bytes back to browser
"""

from __future__ import annotations

import base64
import logging
import re

import aiohttp
from aiohttp import web

from homeassistant.components.http import HomeAssistantView

from . import yes_sport

_LOGGER = logging.getLogger(__name__)

# Headers sent to the CDN for every request (playlist + segments)
_CDN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": yes_sport.STREAM_REFERER,
    "Accept": "*/*",
}

_PLAYLIST_URL = "/api/israel_tv/stream/{channel_id}/playlist.m3u8"
_SEGMENT_URL = "/api/israel_tv/stream/{channel_id}/seg/{encoded_url}"

# Pattern to detect absolute URLs in playlist lines
_ABS_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _encode_url(url: str) -> str:
    """Encode a CDN URL to a URL-safe base64 string (no padding)."""
    return base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


def _decode_url(encoded: str) -> str:
    """Decode a URL-safe base64 string back to the original CDN URL."""
    padding = 4 - len(encoded) % 4
    padded = encoded + ("=" * padding if padding < 4 else "")
    return base64.urlsafe_b64decode(padded).decode()


def _rewrite_playlist(playlist: str, channel_id: str, base_url: str) -> str:
    """Rewrite all segment/sub-playlist URLs in an m3u8 to go through our proxy."""
    lines: list[str] = []
    for line in playlist.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            # This is a URL line (segment or sub-playlist)
            if _ABS_URL_RE.match(stripped):
                abs_url = stripped
            else:
                # Resolve relative URL against the playlist base URL
                abs_url = base_url.rstrip("/") + "/" + stripped.lstrip("/")
            encoded = _encode_url(abs_url)
            line = _SEGMENT_URL.format(channel_id=channel_id, encoded_url=encoded)
        lines.append(line)
    return "\n".join(lines)


class YesSportPlaylistView(HomeAssistantView):
    """Serve a rewritten YES Sport HLS playlist via the local proxy."""

    url = _PLAYLIST_URL
    name = "api:israel_tv:stream:playlist"
    requires_auth = False  # Browser HLS player needs unauthenticated access

    async def get(self, request: web.Request, channel_id: str) -> web.Response:
        """Fetch, rewrite, and return the HLS master/media playlist."""
        try:
            cdn_url = await yes_sport.get_stream_url(channel_id)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Proxy: cannot resolve %s: %s", channel_id, err)
            return web.Response(status=500, text=str(err))

        # Derive the base URL for resolving relative segment paths
        base_url = cdn_url.rsplit("/", 1)[0] + "/"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    cdn_url,
                    headers=_CDN_HEADERS,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if not resp.ok:
                        _LOGGER.warning(
                            "Proxy: CDN returned %s for %s", resp.status, cdn_url
                        )
                        return web.Response(status=resp.status)
                    playlist = await resp.text()
        except aiohttp.ClientError as err:
            _LOGGER.error("Proxy: CDN fetch failed for %s: %s", channel_id, err)
            return web.Response(status=502, text=str(err))

        rewritten = _rewrite_playlist(playlist, channel_id, base_url)
        _LOGGER.debug("Proxy: serving playlist for %s (%d lines)", channel_id, len(rewritten.splitlines()))

        return web.Response(
            text=rewritten,
            content_type="application/vnd.apple.mpegurl",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
            },
        )


class YesSportSegmentView(HomeAssistantView):
    """Proxy a single YES Sport HLS segment to the browser."""

    url = _SEGMENT_URL
    name = "api:israel_tv:stream:segment"
    requires_auth = False

    async def get(self, request: web.Request, channel_id: str, encoded_url: str) -> web.Response:
        """Fetch and stream a media segment from the CDN."""
        try:
            seg_url = _decode_url(encoded_url)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Proxy: bad encoded URL: %s", err)
            return web.Response(status=400)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    seg_url,
                    headers=_CDN_HEADERS,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if not resp.ok:
                        return web.Response(status=resp.status)
                    data = await resp.read()
                    content_type = resp.content_type or "video/MP2T"
                    return web.Response(
                        body=data,
                        content_type=content_type,
                        headers={"Access-Control-Allow-Origin": "*"},
                    )
        except aiohttp.ClientError as err:
            _LOGGER.error("Proxy: segment fetch failed for %s: %s", seg_url[:80], err)
            return web.Response(status=502)
