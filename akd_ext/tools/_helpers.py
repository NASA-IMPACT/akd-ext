"""
Shared HTTP + text helpers for akd_ext tools.

Centralizes:
- Text/list truncation used by multiple search tools.
- Retry-aware HTTP GET that honors ``Retry-After`` on 429/503.
- Rate-limit header extraction (common ``X-RateLimit-*`` family).
"""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx
from loguru import logger


_RETRY_STATUS = (408, 425, 429, 500, 502, 503, 504)


def truncate_text(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending '...' if truncated. 0 disables."""
    if not text or max_chars <= 0:
        return text
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def limit_list(items: list[str], max_items: int) -> list[str]:
    """Limit a list, appending a '... and N more' marker when truncated. 0 disables."""
    if not items or max_items <= 0:
        return items
    if len(items) > max_items:
        return items[:max_items] + [f"... and {len(items) - max_items} more"]
    return items


def _parse_retry_after(value: str | None) -> float | None:
    """Parse Retry-After header (seconds-only form; HTTP-date form ignored)."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def extract_rate_limit(response: httpx.Response) -> dict[str, Any]:
    """Pull common rate-limit headers into a plain dict; returns {} if none present."""
    headers = response.headers
    out: dict[str, Any] = {}
    for src, dst in (
        ("X-RateLimit-Limit", "limit"),
        ("X-RateLimit-Remaining", "remaining"),
        ("X-RateLimit-Reset", "reset"),
    ):
        raw = headers.get(src)
        if raw is None:
            continue
        try:
            out[dst] = int(raw)
        except ValueError:
            out[dst] = raw
    return out


async def get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    max_retries: int = 3,
    base_backoff: float = 0.5,
) -> httpx.Response:
    """
    GET with retries on transient upstream failures.

    Retries on connection errors and on status codes in ``_RETRY_STATUS``.
    Honors ``Retry-After`` (seconds form) when present; otherwise uses
    exponential backoff with jitter. The final response is returned even on
    failure — the caller raises via ``raise_for_status()``.
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            response = await client.get(url, params=params, headers=headers)
        except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as exc:
            last_exc = exc
            if attempt == max_retries:
                raise
            sleep_for = base_backoff * (2**attempt) + random.uniform(0, base_backoff)
            logger.debug(f"HTTP connect error ({exc}); retrying in {sleep_for:.2f}s")
            await asyncio.sleep(sleep_for)
            continue

        if response.status_code not in _RETRY_STATUS or attempt == max_retries:
            return response

        retry_after = _parse_retry_after(response.headers.get("Retry-After"))
        sleep_for = (
            retry_after if retry_after is not None else base_backoff * (2**attempt) + random.uniform(0, base_backoff)
        )
        logger.debug(
            f"HTTP {response.status_code} on {url}; retrying in {sleep_for:.2f}s (attempt {attempt + 1}/{max_retries})"
        )
        await asyncio.sleep(sleep_for)

    # Unreachable — loop always returns or raises.
    if last_exc:
        raise last_exc
    raise RuntimeError("get_with_retry exhausted retries without a response")
