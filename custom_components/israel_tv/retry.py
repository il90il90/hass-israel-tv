"""Retry a transient network operation a few times before giving up.

Segment fetches in the HLS proxy hit an upstream CDN that occasionally drops a
connection or answers a momentary 403/5xx while a signed token is rotating.
Unlike Home Assistant's ffmpeg-backed camera path — which buffers and retries
on its own — the Media Browser player fetches each segment directly through the
proxy, so a single transient failure stops playback. Retrying the fetch
server-side hides these blips from the player.

This module deliberately imports nothing beyond the standard library so the
retry policy can be unit-tested without the Home Assistant or aiohttp stack.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

# Statuses the CDN returns transiently: server errors, plus 403/429 that appear
# for a moment while a token rotates. A 404/416 is a real answer — never retried.
_TRANSIENT_STATUSES = frozenset({403, 429, 500, 502, 503, 504})


def is_transient_status(status: int) -> bool:
    """Return True if *status* is worth retrying rather than surfacing."""
    return status in _TRANSIENT_STATUSES


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    delay: float,
    retry_on_result: Callable[[T], bool],
    retry_on_exception: tuple[type[BaseException], ...],
) -> T:
    """Run *operation*, retrying on a transient result or a listed exception.

    Makes at most *attempts* tries, sleeping *delay* seconds between them. The
    final try's result is returned as-is and its exception is re-raised, so the
    caller always sees the last outcome once the retries are spent. Exceptions
    not in *retry_on_exception* propagate immediately.
    """
    for attempt in range(1, attempts + 1):
        final = attempt == attempts
        try:
            result = await operation()
        except retry_on_exception:
            if final:
                raise
            await asyncio.sleep(delay)
            continue

        if final or not retry_on_result(result):
            return result
        await asyncio.sleep(delay)

    raise AssertionError("retry_async: loop exited without returning")  # pragma: no cover
