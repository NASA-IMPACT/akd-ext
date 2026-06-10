"""Hit each remote MCP URL once to absorb cold-start latency.

Two entry points share one implementation:

- CLI:    ``uv run python -m ieso_w_geoui.warm_mcps``
          (used by ``start.sh`` at notebook launch)
- Python: ``from ieso_w_geoui.warm_mcps import warm``
          (used by the marimo "Warm MCPs" button)

URLs are derived from the agent's own capability list so this stays
in sync as MCPs are added or removed.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx
from pydantic_ai.capabilities import MCP

from ieso_w_geoui.agent import get_default_ieso_worldview_geoui_capabilities

_WARM_TIMEOUT_S = 15.0


@dataclass(frozen=True)
class WarmResult:
    """Outcome of a single warm-up request.

    Either ``status`` is set (an HTTP response came back — any status
    proves the container woke up) or ``error`` is set (transport
    failure: DNS, timeout, connection refused).
    """

    url: str
    status: int | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is not None


def _remote_mcp_urls() -> list[str]:
    """Collect every HTTP(S) MCP URL from the agent's default capabilities.

    The ``startswith`` filter excludes stdio capabilities whose ``url``
    field is a placeholder (e.g. ``stdio://playwright-mcp``).
    """
    return [
        cap.url
        for cap in get_default_ieso_worldview_geoui_capabilities()
        if isinstance(cap, MCP) and cap.url.startswith(("http://", "https://"))
    ]


async def _warm_one(client: httpx.AsyncClient, url: str) -> WarmResult:
    try:
        resp = await client.get(url, timeout=_WARM_TIMEOUT_S)
        return WarmResult(url=url, status=resp.status_code)
    except httpx.HTTPError as exc:
        return WarmResult(url=url, error=type(exc).__name__)


async def warm() -> list[WarmResult]:
    """Warm every remote MCP in the agent's default capability list.

    Returns one result per URL, in the order they appear in
    ``get_default_ieso_worldview_geoui_capabilities``. The marimo
    "Warm MCPs" cell consumes this directly; the CLI entry point
    formats it for console output.
    """
    urls = _remote_mcp_urls()
    if not urls:
        return []
    async with httpx.AsyncClient() as client:
        return await asyncio.gather(*(_warm_one(client, url) for url in urls))


def _print_results(results: list[WarmResult]) -> None:
    if not results:
        print("No remote MCP URLs to warm.")
        return
    print(f"Warming {len(results)} MCP endpoint(s)...")
    for r in results:
        if r.ok:
            print(f"  {r.url} -> HTTP {r.status}")
        else:
            print(f"  {r.url} -> warm failed ({r.error})")


if __name__ == "__main__":
    _print_results(asyncio.run(warm()))
