"""Async HTTP helpers and shared configuration for the PSI tools.

All PSI endpoints are public (no auth). DataCite is used for DOI lookups.
Every tool opens a short-lived ``httpx.AsyncClient`` per call, mirroring the
house pattern in ``sde_search.py``. Tests can inject an
``httpx.MockTransport`` by passing ``transport=...`` when constructing a tool
(extra kwargs become instance attributes on ``BaseTool``).
"""

import os
from urllib.parse import urlparse

import httpx
from pydantic import Field

from akd.tools import BaseToolConfig

USER_AGENT = os.getenv("PSI_USER_AGENT", "akd-ext-psi-tools/0.1")
DOWNLOAD_ALLOWED_HOSTS = {"psi.nasa.gov"}


class PsiToolConfig(BaseToolConfig):
    """Shared configuration for all PSI tools (endpoints and timeouts)."""

    psi_origin: str = Field(
        default=os.getenv("PSI_ORIGIN", "https://psi.nasa.gov"),
        description="Origin used to resolve relative PSI download URLs",
    )
    discovery_url: str = Field(
        default=os.getenv("PSI_DISCOVERY_URL", "https://psi.nasa.gov/geode-py/ws/api/investigations/metadata"),
        description="PSI endpoint listing all public investigations",
    )
    investigation_url_template: str = Field(
        default=os.getenv(
            "PSI_INVESTIGATION_URL_TEMPLATE",
            "https://psi.nasa.gov/geode-py/ws/repo/investigations/{investigation_id}",
        ),
        description="PSI endpoint template for one investigation's metadata",
    )
    file_search_url_template: str = Field(
        default=os.getenv(
            "PSI_FILE_SEARCH_URL_TEMPLATE",
            "https://psi.nasa.gov/geode-py/ws/api/investigations/files/search/{investigation_selector}",
        ),
        description="PSI endpoint template for file search by investigation selector",
    )
    connect_timeout_seconds: float = Field(default=5.0, description="HTTP connect timeout in seconds")
    read_timeout_seconds: float = Field(default=30.0, description="HTTP read timeout in seconds")


class DownloadUrlExpiredError(RuntimeError):
    """Raised when PSI answers 401/403 for a download URL (signed URLs expire)."""


def make_async_client(config: PsiToolConfig, transport: httpx.AsyncBaseTransport | None = None) -> httpx.AsyncClient:
    """Build the async HTTP client used by every PSI tool call."""
    timeout = httpx.Timeout(
        connect=config.connect_timeout_seconds,
        read=config.read_timeout_seconds,
        write=config.read_timeout_seconds,
        pool=config.connect_timeout_seconds,
    )
    return httpx.AsyncClient(
        timeout=timeout,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        follow_redirects=True,
        transport=transport,
    )


async def get_json(client: httpx.AsyncClient, url: str, params: dict | None = None) -> object:
    """GET a JSON document, mapping failures to informative exceptions.

    Note: PSI answers 403 (not 404) for nonexistent or non-public
    investigation ids, so the 4xx message calls that out for the LLM.
    """
    try:
        response = await client.get(url, params=params)
    except httpx.TimeoutException as exc:
        raise TimeoutError(f"PSI request timed out: {url}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"PSI request failed for {url}: {exc}") from exc

    status = response.status_code
    if status == 404:
        raise RuntimeError(f"Upstream resource not found (404): {response.url}")
    if status == 429:
        raise RuntimeError(f"Upstream rate limit hit (429) for {url}; retry later.")
    if status >= 500:
        raise RuntimeError(f"Upstream service unavailable ({status}) for {url}; retry later.")
    if status >= 400:
        raise RuntimeError(
            f"Upstream error ({status}) for {url}. PSI returns 403 for nonexistent or non-public "
            f"investigations. Body: {response.text[:500]}"
        )
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"Upstream response from {url} was not valid JSON.") from exc


def ensure_allowed_download_url(url: str) -> None:
    """Refuse to download from anywhere but the PSI host (defense in depth)."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in DOWNLOAD_ALLOWED_HOSTS:
        raise ValueError(f"Refusing to download from non-PSI URL: {url}")
