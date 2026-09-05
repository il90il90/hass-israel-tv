"""Local HLS proxy for channels that require server-side fetching.

Two channel types are routed through this proxy:

  daddylive — Premium Israeli channels (Sport 1-4, Yes Movies, …) resolved via
              an upstream player page. The signed token lives ~3 hours and the
              CDN rejects every request that lacks the right Referer.

  proxied   — Static channels whose CDN enforces CORS (e.g. Alkass) so the
              browser cannot fetch them directly. No token needed; the URL is
              taken straight from channels.py.

Both types solve the same two problems:
  1. No CORS errors (everything comes from http://localhost:8123).
  2. No ffmpeg extension restrictions (we proxy raw bytes ourselves).

Flow:
  Browser → GET /api/israel_tv/stream/{channel_id}/playlist.m3u8
           ↳  Proxy fetches the m3u8 from the CDN (with the required headers),
              rewrites segment URLs to /api/israel_tv/stream/{id}/seg/{b64}
              and returns the modified playlist.

  Browser → GET /api/israel_tv/stream/{channel_id}/seg/{encoded_url}
           ↳  Proxy fetches the segment from the CDN and streams it back.

Why DaddyLive master playlists are flattened
--------------------------------------------
A DaddyLive master playlist points at a media playlist whose own URL carries
the signed token. Handing that URL to the browser would freeze playback on
whichever token was current when it started, and the stream would stop dead
once that token expired. So we follow the master server-side and serve the
media playlist under our own stable, token-free playlist URL. The player
re-polls that same URL for live updates, so every poll picks up whatever token
is current and playback continues past expiry. Segment sequence numbering is
continuous across a token change, so the player does not see a discontinuity.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import re
from urllib.parse import urljoin

import aiohttp
from aiohttp import web

from homeassistant.components.http import HomeAssistantView

from . import daddylive
from .channels import CHANNELS_BY_ID

_LOGGER = logging.getLogger(__name__)

_BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}

# Headers for DaddyLive CDN requests (token-based, Referer enforced).
_DADDYLIVE_HEADERS = {**_BASE_HEADERS, "Referer": daddylive.STREAM_REFERER}

_PLAYLIST_URL = "/api/israel_tv/stream/{channel_id}/playlist.m3u8"
_SEGMENT_URL = "/api/israel_tv/stream/{channel_id}/seg/{encoded_url}"

_URI_ATTR_RE = re.compile(r'URI="([^"]+)"')
# Anchored on the attribute separator so it reads BANDWIDTH and not the
# AVERAGE-BANDWIDTH that usually precedes it on the same line.
_BANDWIDTH_RE = re.compile(r"[,:]BANDWIDTH=(\d+)")

_PLAYLIST_CONTENT_TYPE = "application/vnd.apple.mpegurl"
_PLAYLIST_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "no-cache",
}


def _encode_url(url: str) -> str:
    """Encode a CDN URL to a URL-safe base64 string (no padding)."""
    return base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


def _decode_url(encoded: str) -> str:
    """Decode a URL-safe base64 string back to the original CDN URL."""
    padded = encoded + "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(padded).decode()


def _proxied(channel_id: str, abs_url: str) -> str:
    """Return the local proxy URL that serves *abs_url*."""
    return _SEGMENT_URL.format(channel_id=channel_id, encoded_url=_encode_url(abs_url))


def _rewrite_playlist(playlist: str, channel_id: str, base_url: str) -> str:
    """Rewrite every URL in an m3u8 so it is fetched through this proxy.

    Covers plain URL lines (segments and sub-playlists) and ``URI="…"``
    attributes, which is how encryption keys and media renditions are declared.
    Relative paths are resolved against *base_url*, the directory of the
    playlist the lines came from.
    """
    lines: list[str] = []
    for line in playlist.splitlines():
        stripped = line.strip()

        if not stripped:
            lines.append(line)
            continue

        if stripped.startswith("#"):
            if "URI=" in stripped:
                line = _URI_ATTR_RE.sub(
                    lambda m: f'URI="{_proxied(channel_id, urljoin(base_url, m.group(1)))}"',
                    line,
                )
            lines.append(line)
            continue

        lines.append(_proxied(channel_id, urljoin(base_url, stripped)))

    return "\n".join(lines)


def _base_of(url: str) -> str:
    """Return the directory portion of *url*, for resolving relative paths."""
    return url.rsplit("/", 1)[0] + "/"


def _select_variant(playlist: str) -> str | None:
    """Return the URI of the highest-bandwidth variant in a master playlist.

    Returns None when *playlist* is a media playlist (no variants), which is
    the signal that its segments can be rewritten as-is.
    """
    lines = playlist.splitlines()
    best_bandwidth = -1
    best_uri: str | None = None

    for index, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF"):
            continue
        match = _BANDWIDTH_RE.search(line)
        bandwidth = int(match.group(1)) if match else 0
        # The variant URI is the next line that is neither blank nor a tag.
        for candidate in lines[index + 1:]:
            candidate = candidate.strip()
            if not candidate or candidate.startswith("#"):
                continue
            if bandwidth > best_bandwidth:
                best_bandwidth, best_uri = bandwidth, candidate
            break

    return best_uri


async def _fetch_text(
    session: aiohttp.ClientSession, url: str, headers: dict
) -> tuple[int, str]:
    """GET *url* and return (status, body). Body is empty on a non-OK status."""
    async with session.get(
        url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
    ) as resp:
        if not resp.ok:
            return resp.status, ""
        return resp.status, await resp.text(encoding="utf-8", errors="replace")


async def _resolve_daddylive_playlist(
    session: aiohttp.ClientSession, channel_id: str
) -> tuple[str, str]:
    """Return (playlist_text, base_url) for a DaddyLive channel.

    Follows the master playlist to the media playlist so the token never
    reaches the browser. A token we believed was fresh can still be rejected
    (the upstream may rotate its signing key) and the CDN can simply drop a
    connection, so any CDN-level failure is retried once with a freshly minted
    token. A failure to resolve the URL at all is raised straight to the caller,
    since re-reading the same player page would not change the outcome.
    """
    last_error = "unknown error"

    for attempt in (1, 2):
        try:
            url = await daddylive.get_stream_url(channel_id)
            status, body = await _fetch_text(session, url, _DADDYLIVE_HEADERS)

            if status == 200 and "#EXTM3U" in body:
                variant = _select_variant(body)
                if variant is None:
                    # Already a media playlist.
                    return body, _base_of(url)

                media_url = urljoin(_base_of(url), variant)
                media_status, media_body = await _fetch_text(
                    session, media_url, _DADDYLIVE_HEADERS
                )
                if media_status == 200 and "#EXTM3U" in media_body:
                    return media_body, _base_of(media_url)

                last_error = f"variant playlist returned HTTP {media_status}"
            elif status != 200:
                last_error = f"CDN returned HTTP {status}"
            else:
                # HTTP 200 with a non-HLS body is how the upstream reports a
                # channel that is off the air; it answers "Not found" with a 200.
                last_error = f"CDN returned no playlist ({body.strip()[:60]!r})"
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            last_error = f"{type(err).__name__}: {err}"

        if attempt == 1:
            _LOGGER.debug(
                "Playlist fetch failed for %s (%s) — retrying with a fresh token",
                channel_id,
                last_error,
            )
            daddylive.invalidate_cache(channel_id)

    raise RuntimeError(f"Could not load stream for {channel_id}: {last_error}")


def _headers_for(channel_id: str) -> dict:
    """Return the CDN request headers appropriate for *channel_id*."""
    channel = CHANNELS_BY_ID.get(channel_id)
    if channel is not None and channel.channel_type == "daddylive":
        return _DADDYLIVE_HEADERS
    return _BASE_HEADERS


def _playlist_response(text: str) -> web.Response:
    """Return an HLS playlist response with CORS and no-cache headers."""
    return web.Response(
        text=text,
        content_type=_PLAYLIST_CONTENT_TYPE,
        headers=_PLAYLIST_HEADERS,
    )


def _segment_content_type(data: bytes, upstream: str | None) -> str:
    """Return the media type to serve for a segment payload.

    The DaddyLive CDN disguises its MPEG-TS segments as images — the URLs end
    in ``.png`` and it answers ``Content-Type: image/png``. Passing that type
    through would tell the player its video is a picture, so the payload is
    sniffed instead: every MPEG-TS packet opens with the 0x47 sync byte, and
    fragmented MP4 opens with a box type at offset 4.
    """
    if data[:1] == b"\x47":
        return "video/MP2T"
    if data[4:8] in (b"ftyp", b"styp", b"moof", b"sidx"):
        return "video/mp4"
    if upstream and not upstream.startswith("image/"):
        return upstream
    return "video/MP2T"


class StreamPlaylistView(HomeAssistantView):
    """Serve a rewritten HLS playlist via the local proxy."""

    url = _PLAYLIST_URL
    name = "api:israel_tv:stream:playlist"
    requires_auth = False  # Browser HLS player needs unauthenticated access

    async def get(self, request: web.Request, channel_id: str) -> web.Response:
        """Fetch, rewrite, and return the HLS playlist for *channel_id*."""
        channel = CHANNELS_BY_ID.get(channel_id)
        if channel is None:
            return web.Response(status=404, text=f"Unknown channel: {channel_id}")

        try:
            async with aiohttp.ClientSession() as session:
                if channel.channel_type == "daddylive":
                    playlist, base_url = await _resolve_daddylive_playlist(
                        session, channel_id
                    )
                elif channel.channel_type == "proxied":
                    status, playlist = await _fetch_text(
                        session, channel.url, _BASE_HEADERS
                    )
                    if status != 200 or "#EXTM3U" not in playlist:
                        _LOGGER.warning(
                            "Proxy: CDN returned %s for %s", status, channel_id
                        )
                        return web.Response(status=502, text=f"CDN returned {status}")
                    base_url = _base_of(channel.url)
                else:
                    return web.Response(
                        status=400,
                        text=f"Channel {channel_id} is not routed through the proxy",
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Proxy: CDN fetch failed for %s: %s", channel_id, err)
            return web.Response(status=502, text=str(err))
        except Exception as err:  # noqa: BLE001 — surface any resolve failure to the player
            _LOGGER.error("Proxy: cannot resolve %s: %s", channel_id, err)
            return web.Response(status=502, text=str(err))

        rewritten = _rewrite_playlist(playlist, channel_id, base_url)
        _LOGGER.debug(
            "Proxy: serving playlist for %s (%d lines)",
            channel_id,
            len(rewritten.splitlines()),
        )
        return _playlist_response(rewritten)


class StreamSegmentView(HomeAssistantView):
    """Proxy a single HLS segment (or sub-playlist) to the browser.

    If the CDN returns a playlist, the URLs inside it are rewritten through the
    proxy just like the top-level playlist. That is required for multi-level
    HLS streams whose media playlists contain relative segment URLs.
    """

    url = _SEGMENT_URL
    name = "api:israel_tv:stream:segment"
    requires_auth = False

    async def get(
        self, request: web.Request, channel_id: str, encoded_url: str
    ) -> web.Response:
        """Fetch and stream a segment, or rewrite a sub-playlist, from the CDN."""
        try:
            seg_url = _decode_url(encoded_url)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Proxy: bad encoded URL: %s", err)
            return web.Response(status=400)

        headers = _headers_for(channel_id)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    seg_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if not resp.ok:
                        return web.Response(status=resp.status)

                    looks_like_playlist = (
                        "mpegurl" in (resp.content_type or "").lower()
                        or seg_url.split("?")[0].endswith(".m3u8")
                    )

                    if looks_like_playlist:
                        text = await resp.text(encoding="utf-8", errors="replace")
                        if "#EXTM3U" in text or "#EXT-X" in text:
                            rewritten = _rewrite_playlist(
                                text, channel_id, _base_of(seg_url)
                            )
                            _LOGGER.debug(
                                "Proxy: rewriting sub-playlist for %s (%d lines)",
                                channel_id,
                                len(rewritten.splitlines()),
                            )
                            return _playlist_response(rewritten)

                    # Binary segment — stream raw bytes.
                    data = await resp.read()
                    return web.Response(
                        body=data,
                        content_type=_segment_content_type(data, resp.content_type),
                        headers={"Access-Control-Allow-Origin": "*"},
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            # A timeout is not a ClientError, and letting either escape the
            # handler would turn a recoverable stall into an HTTP 500.
            _LOGGER.error("Proxy: segment fetch failed for %s: %s", seg_url[:80], err)
            return web.Response(status=502)
