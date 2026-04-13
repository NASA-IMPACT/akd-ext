"""
NASA Astrophysics Data System (ADS) tools.

Two tools wrapping the ADS API for astrophysics paper search and link resolution:

1. ADSSearchTool — search for papers by query, returning metadata including bibcodes,
   titles, abstracts, linked data archives, and optionally GitHub URLs extracted
   from full text.
2. ADSLinksResolverTool — resolve a bibcode to data archives, code repositories,
   electronic sources, and associated works.

Both share a single config (base_url, api_token, timeout, retries) since they hit
the same API at https://api.adsabs.harvard.edu/v1.

API docs: https://github.com/adsabs/adsabs-dev-api
Resolver docs: https://github.com/adsabs/resolver_service
"""

from __future__ import annotations

import asyncio
import os
import re
from enum import StrEnum
from typing import Any
from urllib.parse import quote, urljoin

import httpx
from loguru import logger
from pydantic import Field, model_validator

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig

from akd_ext.mcp import mcp_tool
from akd_ext.tools._helpers import (
    extract_rate_limit,
    get_with_retry,
    limit_list,
    truncate_text,
)


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------


class ADSToolConfig(BaseToolConfig):
    """Shared configuration for all ADS tools."""

    base_url: str = Field(
        default="https://api.adsabs.harvard.edu/v1",
        description="Base URL for the ADS API",
    )
    api_token: str = Field(
        default_factory=lambda: os.environ.get("ADS_API_TOKEN", ""),
        description="ADS API bearer token for authentication",
    )
    timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=6,
        description="Maximum retries on transient upstream failures (429/5xx, connection errors)",
    )

    @model_validator(mode="after")
    def _require_api_token(self) -> "ADSToolConfig":
        if not self.api_token:
            msg = (
                "ADS_API_TOKEN environment variable is not set. "
                "Get a token from https://ui.adsabs.harvard.edu/user/settings/token"
            )
            raise ValueError(msg)
        return self


# ---------------------------------------------------------------------------
# Shared helpers (ADS-specific)
# ---------------------------------------------------------------------------


_GITHUB_URL_RE = re.compile(r"https?://github\.com/[^\s,;)\"'<>]+")


def _extract_github_urls(highlights: list[str]) -> list[str]:
    """Extract unique GitHub URLs from ADS highlight snippets (order-preserving)."""
    seen: set[str] = set()
    unique: list[str] = []
    for snippet in highlights:
        clean = snippet.replace("<em>", "").replace("</em>", "")
        for match in _GITHUB_URL_RE.findall(clean):
            url = match.rstrip(".")
            if url not in seen:
                seen.add(url)
                unique.append(url)
    return unique


def _build_base_url(config: ADSToolConfig) -> str:
    """Ensure trailing slash so urljoin treats it as a directory."""
    return config.base_url.rstrip("/") + "/"


# ---------------------------------------------------------------------------
# Base class with shared HTTP + lifecycle plumbing
# ---------------------------------------------------------------------------


class _ADSHttpMixin:
    """Mixin providing a lazy per-instance httpx.AsyncClient + auth headers.

    Not a BaseTool subclass (so the metaclass schema check is bypassed). Expects
    ``self.config`` to satisfy the ``ADSToolConfig`` protocol (timeout, api_token).
    """

    config: ADSToolConfig
    _client: httpx.AsyncClient | None

    async def _get_client(self) -> httpx.AsyncClient:
        if getattr(self, "_client", None) is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        assert self._client is not None
        return self._client

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.config.api_token}"}

    async def aclose(self) -> None:
        """Close the underlying HTTP client. Safe to call multiple times."""
        client = getattr(self, "_client", None)
        if client is not None:
            await client.aclose()
            self._client = None


# ---------------------------------------------------------------------------
# ADSSearchTool
# ---------------------------------------------------------------------------


class ADSFieldPreset(StrEnum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    EXTENDED = "extended"
    FULL = "full"


ADS_FIELD_PRESETS: dict[ADSFieldPreset, str] = {
    ADSFieldPreset.MINIMAL: "bibcode,title,first_author,year,citation_count",
    ADSFieldPreset.STANDARD: "bibcode,title,first_author,author,year,pubdate,citation_count,doi,pub,abstract,data",
    ADSFieldPreset.EXTENDED: (
        "bibcode,title,first_author,author,year,pubdate,citation_count,doi,pub,"
        "volume,page,keyword,abstract,data,esources,property"
    ),
    ADSFieldPreset.FULL: (
        "bibcode,title,first_author,author,year,pubdate,citation_count,doi,pub,"
        "volume,page,keyword,abstract,data,esources,property,identifier,aff"
    ),
}


class ADSSearchToolConfig(ADSToolConfig):
    """Configuration for the ADS Search Tool."""

    truncate_abstract: int = Field(
        default=300,
        description="Default abstract char cap (0 = no truncation). Overridable per-call via input.",
    )
    max_authors: int = Field(
        default=10,
        description="Default max authors per paper (0 = all). Overridable per-call via input.",
    )


class ADSPaper(OutputSchema):
    """A single paper result from ADS search."""

    bibcode: str = Field(..., description="ADS bibcode identifier")
    title: str = Field(default="", description="Paper title")
    first_author: str = Field(default="", description="First author name")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    abstract: str = Field(default="", description="Paper abstract")
    year: str | None = Field(default=None, description="Publication year")
    pubdate: str | None = Field(default=None, description="Publication date")
    doi: str | None = Field(default=None, description="Digital Object Identifier")
    pub: str | None = Field(default=None, description="Journal or publication name")
    citation_count: int = Field(default=0, description="Number of citations")
    keywords: list[str] = Field(default_factory=list, description="Paper keywords")
    data: list[str] = Field(
        default_factory=list,
        description="Linked data archive names (e.g., 'Chandra', 'MAST', 'HEASARC', 'SIMBAD')",
    )
    esources: list[str] = Field(
        default_factory=list,
        description="Electronic sources (e.g., 'PUB_HTML', 'EPRINT_HTML', 'PUB_PDF')",
    )
    property: list[str] = Field(
        default_factory=list,
        description="Paper properties (e.g., 'REFEREED', 'ARTICLE', 'OPENACCESS')",
    )
    github_urls: list[str] = Field(
        default_factory=list,
        description="GitHub URLs found in the paper's full text (only populated when fetch_github_urls=True)",
    )


class ADSSearchToolInputSchema(InputSchema):
    """Input schema for ADS paper search queries."""

    query: str = Field(
        ...,
        description=(
            "ADS search query. Supports free text and field-specific syntax "
            "(e.g., 'abs:\"ultra-fast outflow\" keyword:quasar', 'doi:10.3847/1538-4357/adb39c')"
        ),
    )
    rows: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of results to return. Authoritative — the tool will not truncate below this.",
    )
    field_preset: ADSFieldPreset | None = Field(
        default=None,
        description=(
            "Field preset for token efficiency. "
            "'minimal': bibcode, title, first_author, year, citations. "
            "'standard': + authors, date, DOI, journal, abstract, data. "
            "'extended': + volume, page, keywords, esources, property. "
            "'full': all fields including identifiers and affiliations. "
            "If None, uses 'standard'."
        ),
    )
    fl: str | None = Field(
        default=None,
        description="Custom comma-separated fields to return. Overrides field_preset if provided.",
    )
    sort: str = Field(default="score desc", description="Sort order (e.g., 'score desc', 'citation_count desc')")
    fq: str | None = Field(default=None, description="Filter query to narrow results (e.g., 'property:refereed')")
    fetch_github_urls: bool = Field(
        default=False,
        description=(
            "If True, issue a secondary highlight query per result to extract GitHub URLs "
            "from the full text. Costs 1 extra ADS quota unit per returned paper. Off by default."
        ),
    )
    truncate_abstract: int | None = Field(
        default=None,
        description="Per-call override for abstract truncation (0 = no truncation). Falls back to config default.",
    )
    max_authors: int | None = Field(
        default=None,
        description="Per-call override for max authors (0 = all). Falls back to config default.",
    )


class ADSSearchToolOutputSchema(OutputSchema):
    """Output schema for ADS paper search results."""

    papers: list[ADSPaper] = Field(..., description="List of matching papers from ADS")
    num_found: int = Field(
        default=0,
        description="Total matches in ADS (Solr numFound), independent of rows cap",
    )
    num_returned: int = Field(
        default=0,
        description="Number of papers actually returned in this response",
    )
    fields_returned: str = Field(default="", description="Fields that were requested from ADS")
    rate_limit: dict[str, Any] = Field(
        default_factory=dict,
        description="ADS rate-limit headers (limit/remaining/reset) from the primary response, if present",
    )
    enrichment_errors: list[str] = Field(
        default_factory=list,
        description="Per-bibcode errors encountered while fetching GitHub URLs (empty on success or when disabled)",
    )


@mcp_tool
class ADSSearchTool(_ADSHttpMixin, BaseTool[ADSSearchToolInputSchema, ADSSearchToolOutputSchema]):
    """
    Search NASA's Astrophysics Data System (ADS) for scientific papers.

    ADS is the primary search engine for astronomy and astrophysics literature,
    indexing papers, bibcodes, DOIs, and links to observation data archives
    (HEASARC, MAST, Chandra, XMM, etc.) and code repositories (GitHub, Zenodo).

    Field presets trade detail for token budget:
    - "minimal": 5 fields — bibcode, title, first_author, year, citations
    - "standard": 11 fields — adds authors, date, DOI, journal, abstract, data archives
    - "extended": 15 fields — adds volume, page, keywords, esources, properties
    - "full": all available fields

    GitHub URL extraction is **opt-in** (``fetch_github_urls=True``) because it
    issues one extra ADS call per returned paper. Failures are reported via
    ``enrichment_errors`` rather than being silently dropped.

    Returns papers plus ``num_found`` (Solr total), ``num_returned`` (this page),
    and ``rate_limit`` telemetry from ADS response headers.
    """

    input_schema = ADSSearchToolInputSchema
    output_schema = ADSSearchToolOutputSchema
    config_schema = ADSSearchToolConfig
    config: ADSSearchToolConfig

    def _parse_paper(
        self,
        doc: dict,
        github_urls: list[str] | None,
        truncate_abstract: int,
        max_authors: int,
    ) -> ADSPaper:
        """Parse a single document from the ADS API response."""
        title_list = doc.get("title", [])
        title = title_list[0] if title_list else ""

        doi_list = doc.get("doi", [])
        doi = doi_list[0] if doi_list else None

        abstract = truncate_text(doc.get("abstract", ""), truncate_abstract)
        authors = limit_list(doc.get("author", []), max_authors)

        return ADSPaper(
            bibcode=doc.get("bibcode", ""),
            title=title,
            first_author=doc.get("first_author", ""),
            authors=authors,
            abstract=abstract,
            year=doc.get("year"),
            pubdate=doc.get("pubdate"),
            doi=doi,
            pub=doc.get("pub"),
            citation_count=doc.get("citation_count", 0),
            keywords=doc.get("keyword", []),
            data=doc.get("data", []),
            esources=doc.get("esources", []),
            property=doc.get("property", []),
            github_urls=github_urls or [],
        )

    async def _fetch_github_urls_for(
        self,
        client: httpx.AsyncClient,
        search_url: str,
        bibcode: str,
    ) -> tuple[str, list[str], str | None]:
        """Fetch GitHub URLs from the full text for a single bibcode.

        Returns (bibcode, urls, error_message). error_message is None on success.
        """
        code_params: dict[str, str] = {
            "q": f'full:"github.com" bibcode:"{bibcode}"',
            "fl": "bibcode,id",
            "rows": "1",
            "hl": "true",
            "hl.fl": "title,abstract,body,ack",
            "hl.maxAnalyzedChars": "150000",
            "hl.requireFieldMatch": "true",
            "hl.usePhraseHighlighter": "true",
        }
        try:
            response = await get_with_retry(
                client,
                search_url,
                params=code_params,
                headers=self._auth_headers(),
                max_retries=self.config.max_retries,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            return bibcode, [], f"{bibcode}: {exc}"

        highlighting = data.get("highlighting", {})
        code_docs = data.get("response", {}).get("docs", [])
        doc_id = str(code_docs[0].get("id", "")) if code_docs else ""
        if not doc_id or doc_id not in highlighting:
            return bibcode, [], None

        snippets: list[str] = []
        for field_snippets in highlighting[doc_id].values():
            snippets.extend(field_snippets)
        return bibcode, _extract_github_urls(snippets), None

    async def _arun(self, params: ADSSearchToolInputSchema) -> ADSSearchToolOutputSchema:
        """Execute ADS search query and return formatted results."""
        search_url = urljoin(_build_base_url(self.config), "search/query")

        if params.fl:
            fields = params.fl
        else:
            preset = params.field_preset or ADSFieldPreset.STANDARD
            fields = ADS_FIELD_PRESETS[preset]

        query_params: dict[str, str] = {
            "q": params.query,
            "fl": fields,
            "rows": str(params.rows),
            "sort": params.sort,
        }
        if params.fq:
            query_params["fq"] = params.fq

        logger.debug(f"ADS API request: {query_params}")

        client = await self._get_client()

        try:
            response = await get_with_retry(
                client,
                search_url,
                params=query_params,
                headers=self._auth_headers(),
                max_retries=self.config.max_retries,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as e:
            msg = f"ADS API request timed out after {self.config.timeout}s"
            raise TimeoutError(msg) from e
        except httpx.HTTPStatusError as e:
            msg = f"ADS API returned error status {e.response.status_code}: {e.response.text}"
            raise RuntimeError(msg) from e
        except Exception as e:
            msg = f"Failed to query ADS API: {e}"
            raise RuntimeError(msg) from e

        rate_limit = extract_rate_limit(response)
        response_data = data.get("response", {})
        docs: list[dict] = response_data.get("docs", [])
        num_found = response_data.get("numFound", 0)

        github_urls_by_bibcode: dict[str, list[str]] = {}
        enrichment_errors: list[str] = []
        if params.fetch_github_urls and docs:
            bibcodes = [doc.get("bibcode", "") for doc in docs if doc.get("bibcode")]
            results = await asyncio.gather(*[self._fetch_github_urls_for(client, search_url, b) for b in bibcodes])
            for bibcode, urls, err in results:
                if urls:
                    github_urls_by_bibcode[bibcode] = urls
                if err:
                    enrichment_errors.append(err)

        truncate_abstract = (
            params.truncate_abstract if params.truncate_abstract is not None else self.config.truncate_abstract
        )
        max_authors = params.max_authors if params.max_authors is not None else self.config.max_authors

        papers = [
            self._parse_paper(
                doc,
                github_urls_by_bibcode.get(doc.get("bibcode", "")),
                truncate_abstract,
                max_authors,
            )
            for doc in docs
        ]

        return ADSSearchToolOutputSchema(
            papers=papers,
            num_found=num_found,
            num_returned=len(papers),
            fields_returned=fields,
            rate_limit=rate_limit,
            enrichment_errors=enrichment_errors,
        )


# ---------------------------------------------------------------------------
# ADSLinksResolverTool
# ---------------------------------------------------------------------------


class ADSLinksResolverToolConfig(ADSToolConfig):
    """Configuration for the ADS Links Resolver Tool. Inherits base_url/api_token/timeout/max_retries."""


class ADSLinksResolverInputSchema(InputSchema):
    """Input schema for ADS links resolver."""

    bibcode: str = Field(..., description="ADS bibcode to resolve links for (e.g., '2016ApJ...824...53C')")
    link_type: str | None = Field(
        default=None,
        description=(
            "Specific link type to fetch. Common types: "
            "'associated' (related works/data), "
            "'esource' (electronic full-text sources), "
            "'data' (linked archive data like HEASARC, MAST, Chandra, XMM). "
            "If None, returns all available links."
        ),
    )


class ADSLink(OutputSchema):
    """A single resolved link from ADS."""

    url: str = Field(..., description="URL of the linked resource")
    title: str = Field(default="", description="Title or label of the link")
    link_type: str = Field(default="", description="Type of link (e.g., 'ESOURCE', 'DATA', 'ASSOCIATED')")
    count: int = Field(default=0, description="Number of records at this link (for data archives)")


class ADSLinksResolverOutputSchema(OutputSchema):
    """Output schema for ADS links resolver."""

    links: list[ADSLink] = Field(default_factory=list, description="List of resolved links for the bibcode")
    bibcode: str = Field(..., description="The bibcode that was resolved")
    rate_limit: dict[str, Any] = Field(
        default_factory=dict,
        description="ADS rate-limit headers (limit/remaining/reset) from the response, if present",
    )


@mcp_tool
class ADSLinksResolverTool(
    _ADSHttpMixin,
    BaseTool[ADSLinksResolverInputSchema, ADSLinksResolverOutputSchema],
):
    """
    Resolve data links, code repositories, and associated resources for an ADS bibcode.

    Given a paper's bibcode, returns links to external resources such as:
    - Data archives: HEASARC, MAST, Chandra, XMM, NICER, SIMBAD, NED, etc.
    - Code repositories: GitHub, Zenodo
    - Electronic sources: publisher PDFs, preprints, HTML versions
    - Associated works: related papers, data products

    Returns a list of links plus ADS rate-limit telemetry.
    """

    input_schema = ADSLinksResolverInputSchema
    output_schema = ADSLinksResolverOutputSchema
    config_schema = ADSLinksResolverToolConfig
    config: ADSLinksResolverToolConfig

    # ADS resolver returns site-relative paths (e.g. "/link_gateway/...") for some link
    # types; callers expect absolute URLs. Resolve against the public ADS host.
    _UI_BASE = "https://ui.adsabs.harvard.edu"

    @classmethod
    def _absolutize(cls, url: str) -> str:
        if not url:
            return url
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if url.startswith("/"):
            return cls._UI_BASE + url
        return url

    @classmethod
    def _parse_links(cls, data: dict) -> list[ADSLink]:
        """Parse links from the ADS resolver response."""
        links: list[ADSLink] = []

        records = data.get("links", {}).get("records", [])
        if records:
            for record in records:
                url = cls._absolutize(record.get("url", ""))
                title = record.get("title", "") or record.get("data", "") or ""
                link_type = record.get("link_type", "") or record.get("type", "") or ""
                count = record.get("count", 0) or 0
                if url:
                    links.append(ADSLink(url=url, title=title, link_type=link_type, count=count))
            return links

        link_type = data.get("link_type", "") or data.get("service", "") or ""
        url = cls._absolutize(data.get("action", ""))
        count = data.get("links", {}).get("count", 0) if isinstance(data.get("links"), dict) else 0

        if url.startswith("http"):
            links.append(ADSLink(url=url, title="", link_type=link_type, count=count))

        return links

    async def _arun(self, params: ADSLinksResolverInputSchema) -> ADSLinksResolverOutputSchema:
        """Resolve links for a given ADS bibcode."""
        base = _build_base_url(self.config)
        url = urljoin(base, f"resolver/{quote(params.bibcode, safe='')}")
        if params.link_type:
            url = urljoin(url + "/", quote(params.link_type, safe=""))

        logger.debug(f"ADS Resolver request: {url}")

        client = await self._get_client()

        try:
            response = await get_with_retry(
                client,
                url,
                headers=self._auth_headers(),
                max_retries=self.config.max_retries,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as e:
            msg = f"ADS Resolver request timed out after {self.config.timeout}s"
            raise TimeoutError(msg) from e
        except httpx.HTTPStatusError as e:
            msg = f"ADS Resolver returned error status {e.response.status_code}: {e.response.text}"
            raise RuntimeError(msg) from e
        except Exception as e:
            msg = f"Failed to query ADS Resolver: {e}"
            raise RuntimeError(msg) from e

        return ADSLinksResolverOutputSchema(
            links=self._parse_links(data),
            bibcode=params.bibcode,
            rate_limit=extract_rate_limit(response),
        )
