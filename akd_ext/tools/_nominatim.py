"""Shared Nominatim (OpenStreetMap) plumbing for the geocode tools.

Nominatim's usage policy allows at most 1 request/second from a single source.
``nominatim_get`` applies a process-wide throttle (a lock + last-request
timestamp) shared by both ``geocode`` and ``reverse_geocode`` so that
concurrent, stateless tool calls do not burst the service and risk a ban.

The throttle gates *before* the request (start-to-start spacing) rather than
sleeping afterward, so failures don't pay a flat penalty and the rate is
genuinely capped under concurrency.
"""

from __future__ import annotations

import threading
import time

import requests

HEADERS = {"User-Agent": "prithvi-workshop-agent/1.0"}
_MIN_INTERVAL_S = 1.0  # Nominatim: max 1 request/second

_lock = threading.Lock()
_last_request_ts = 0.0


def nominatim_get(url: str, params: dict, timeout: float = 10.0) -> requests.Response:
    """Rate-limited GET against Nominatim.

    Blocks until at least 1 second has passed since the previous request
    (across all callers), then fires. Holding the lock for the request
    serializes calls, which is exactly what the 1 req/sec policy requires.
    """
    global _last_request_ts
    with _lock:
        wait = _MIN_INTERVAL_S - (time.monotonic() - _last_request_ts)
        if wait > 0:
            time.sleep(wait)
        _last_request_ts = time.monotonic()
        return requests.get(url, params=params, headers=HEADERS, timeout=timeout)
