"""Tests for the transient-failure retry helper.

Run: python -m pytest tests/test_retry.py -v

These tests deliberately avoid Home Assistant and aiohttp imports so the
retry policy can be verified in isolation, without the full HA stack.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "israel_tv"))

from retry import is_transient_status, retry_async  # noqa: E402


class _Boom(Exception):
    """Stand-in for a transient network error (e.g. a dropped connection)."""


def _run(coro):
    return asyncio.run(coro)


# ── is_transient_status ──────────────────────────────────────────────────────

def test_server_errors_are_transient():
    for status in (500, 502, 503, 504):
        assert is_transient_status(status) is True


def test_forbidden_and_rate_limited_are_transient():
    # The CDN briefly answers 403/429 when a token is momentarily out of sync.
    assert is_transient_status(403) is True
    assert is_transient_status(429) is True


def test_success_and_client_errors_are_not_transient():
    for status in (200, 206, 301, 404, 416):
        assert is_transient_status(status) is False


# ── retry_async: result-based retry ──────────────────────────────────────────

def test_returns_immediately_on_good_result():
    calls = 0

    async def op():
        nonlocal calls
        calls += 1
        return 200

    result = _run(
        retry_async(
            op,
            attempts=3,
            delay=0,
            retry_on_result=is_transient_status,
            retry_on_exception=(_Boom,),
        )
    )
    assert result == 200
    assert calls == 1


def test_retries_transient_result_then_succeeds():
    statuses = iter([502, 502, 200])
    calls = 0

    async def op():
        nonlocal calls
        calls += 1
        return next(statuses)

    result = _run(
        retry_async(
            op,
            attempts=3,
            delay=0,
            retry_on_result=is_transient_status,
            retry_on_exception=(_Boom,),
        )
    )
    assert result == 200
    assert calls == 3


def test_returns_last_result_when_all_attempts_transient():
    calls = 0

    async def op():
        nonlocal calls
        calls += 1
        return 502

    result = _run(
        retry_async(
            op,
            attempts=3,
            delay=0,
            retry_on_result=is_transient_status,
            retry_on_exception=(_Boom,),
        )
    )
    assert result == 502
    assert calls == 3


# ── retry_async: exception-based retry ───────────────────────────────────────

def test_retries_exception_then_succeeds():
    calls = 0

    async def op():
        nonlocal calls
        calls += 1
        if calls < 2:
            raise _Boom("dropped")
        return 200

    result = _run(
        retry_async(
            op,
            attempts=3,
            delay=0,
            retry_on_result=is_transient_status,
            retry_on_exception=(_Boom,),
        )
    )
    assert result == 200
    assert calls == 2


def test_reraises_after_final_attempt():
    calls = 0

    async def op():
        nonlocal calls
        calls += 1
        raise _Boom("still dropped")

    try:
        _run(
            retry_async(
                op,
                attempts=3,
                delay=0,
                retry_on_result=is_transient_status,
                retry_on_exception=(_Boom,),
            )
        )
    except _Boom:
        pass
    else:
        raise AssertionError("expected _Boom to propagate after the final attempt")
    assert calls == 3


def test_unlisted_exception_is_not_retried():
    calls = 0

    async def op():
        nonlocal calls
        calls += 1
        raise ValueError("not a network error")

    try:
        _run(
            retry_async(
                op,
                attempts=3,
                delay=0,
                retry_on_result=is_transient_status,
                retry_on_exception=(_Boom,),
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError to propagate immediately")
    assert calls == 1
