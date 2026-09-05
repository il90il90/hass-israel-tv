"""Integration tests for StreamSegmentView's retry behaviour.

Run: python -m pytest tests/test_segment_proxy.py -v

aiohttp has no wheel for this Python and Home Assistant is not installed, so the
network boundary (aiohttp) and the HA base class are replaced with faithful
minimal stubs. Everything under test — the retry wiring, status handling,
sub-playlist rewriting and content-type sniffing — is the real proxy.py code;
only the socket I/O is faked, which is exactly the seam that should be faked.
"""

from __future__ import annotations

import asyncio
import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# ── Stub the network boundary and HA base class before importing proxy ───────

def _install_stubs() -> None:
    aiohttp = types.ModuleType("aiohttp")

    class ClientError(Exception):
        """Mirrors aiohttp.ClientError (base of connection/transport errors)."""

    class ClientTimeout:
        def __init__(self, total=None):
            self.total = total

    class _Placeholder:  # replaced per-test via monkeypatching
        pass

    web = types.ModuleType("aiohttp.web")

    class Response:
        """Minimal stand-in for aiohttp.web.Response, capturing what was sent."""

        def __init__(self, *, status=200, text=None, body=None,
                     content_type=None, headers=None):
            self.status = status
            self.text = text
            self.body = body
            self.content_type = content_type
            self.headers = headers or {}

    class Request:
        pass

    web.Response = Response
    web.Request = Request

    aiohttp.ClientError = ClientError
    aiohttp.ClientTimeout = ClientTimeout
    aiohttp.ClientSession = _Placeholder
    aiohttp.web = web

    sys.modules["aiohttp"] = aiohttp
    sys.modules["aiohttp.web"] = web

    ha = types.ModuleType("homeassistant")
    ha_components = types.ModuleType("homeassistant.components")
    ha_http = types.ModuleType("homeassistant.components.http")

    class HomeAssistantView:
        pass

    ha_http.HomeAssistantView = HomeAssistantView
    ha.components = ha_components
    ha_components.http = ha_http
    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.components"] = ha_components
    sys.modules["homeassistant.components.http"] = ha_http

    # Register the package with a real __path__ but WITHOUT running its
    # __init__.py (which imports the full HA stack).
    cc = types.ModuleType("custom_components")
    cc.__path__ = [str(ROOT / "custom_components")]
    israel = types.ModuleType("custom_components.israel_tv")
    israel.__path__ = [str(ROOT / "custom_components" / "israel_tv")]
    sys.modules["custom_components"] = cc
    sys.modules["custom_components.israel_tv"] = israel


_install_stubs()
proxy = importlib.import_module("custom_components.israel_tv.proxy")
proxy._SEGMENT_RETRY_DELAY = 0  # no real sleeping between retries in tests

_TS_BODY = b"\x47" + b"\x00" * 32  # an MPEG-TS packet opens with the 0x47 sync byte


# ── Fake aiohttp session driven by a scripted list of outcomes ───────────────

class _Resp:
    def __init__(self, status, content_type, body):
        self.status = status
        self.content_type = content_type
        self._body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def read(self):
        return self._body


class _Raiser:
    def __init__(self, exc):
        self._exc = exc

    async def __aenter__(self):
        raise self._exc

    async def __aexit__(self, *exc):
        return False


class _Controller:
    """Hands out fake sessions that pop shared, scripted outcomes in order."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def __call__(self):  # used as aiohttp.ClientSession()
        return _FakeSession(self)


class _FakeSession:
    def __init__(self, controller):
        self._c = controller

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def get(self, url, headers=None, timeout=None):
        self._c.calls += 1
        outcome = self._c.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            return _Raiser(outcome)
        return outcome


def _drive(outcomes, seg_url):
    """Run StreamSegmentView.get against *outcomes*; return (response, controller)."""
    controller = _Controller(outcomes)
    proxy.aiohttp.ClientSession = controller
    view = proxy.StreamSegmentView()
    encoded = proxy._encode_url(seg_url)
    response = asyncio.run(view.get(None, "yes2", encoded))
    return response, controller


# ── Tests ────────────────────────────────────────────────────────────────────

def test_recovers_after_two_transient_502s():
    resp, ctrl = _drive(
        [
            _Resp(502, "image/png", b""),
            _Resp(502, "image/png", b""),
            _Resp(200, "image/png", _TS_BODY),
        ],
        "https://cdn.example/abc.pdf",
    )
    assert resp.status == 200
    assert resp.body == _TS_BODY
    assert resp.content_type == "video/MP2T"  # sniffed past the image/png disguise
    assert ctrl.calls == 3


def test_recovers_after_dropped_connection():
    resp, ctrl = _drive(
        [
            proxy.aiohttp.ClientError("connection reset"),
            _Resp(200, "image/png", _TS_BODY),
        ],
        "https://cdn.example/def.pdf",
    )
    assert resp.status == 200
    assert resp.body == _TS_BODY
    assert ctrl.calls == 2


def test_gives_up_after_persistent_502():
    resp, ctrl = _drive(
        [_Resp(502, "text/plain", b"")] * 3,
        "https://cdn.example/ghi.pdf",
    )
    assert resp.status == 502
    assert ctrl.calls == 3  # exhausted all attempts, did not retry forever


def test_gives_up_after_persistent_drops_returns_502():
    resp, ctrl = _drive(
        [proxy.aiohttp.ClientError("boom")] * 3,
        "https://cdn.example/jkl.pdf",
    )
    assert resp.status == 502
    assert ctrl.calls == 3


def test_real_error_status_is_passed_through_without_retry():
    resp, ctrl = _drive(
        [_Resp(404, "text/plain", b"not found")],
        "https://cdn.example/mno.pdf",
    )
    assert resp.status == 404
    assert ctrl.calls == 1  # 404 is a real answer, never retried


def test_subplaylist_is_rewritten_through_proxy():
    body = (
        b"#EXTM3U\n"
        b"#EXT-X-VERSION:3\n"
        b"#EXTINF:10.000,\n"
        b"https://cdn.example/segment0.ts\n"
    )
    resp, ctrl = _drive(
        [_Resp(200, "application/vnd.apple.mpegurl", body)],
        "https://cdn.example/media.m3u8",
    )
    assert resp.content_type == proxy._PLAYLIST_CONTENT_TYPE
    assert "/api/israel_tv/stream/yes2/seg/" in resp.text
    assert "https://cdn.example/segment0.ts" not in resp.text
    assert ctrl.calls == 1
