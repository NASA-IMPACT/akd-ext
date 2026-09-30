"""Shared HTTP helper for tool API calls."""

from __future__ import annotations

from typing import Any

import httpx


async def get_json(
    url: str,
    *,
    client: httpx.AsyncClient | None = None,
    headers: dict | None = None,
    params: dict | None = None,
    timeout: float = 30.0,
) -> Any:
    """GET ``url`` and return the parsed JSON body, raising on HTTP error.

    Pass ``client`` to reuse an existing ``AsyncClient`` across several requests;
    otherwise a short-lived one is created for this single call. Centralizes the
    GET + ``raise_for_status`` + ``json()`` boilerplate the ADS/ASCL tools share,
    so error handling and timeouts stay consistent in one place.
    """
    if client is not None:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    async with httpx.AsyncClient(timeout=timeout) as owned:
        response = await owned.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
