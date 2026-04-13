"""
Astrophysics Source Code Library (ASCL) tools.

Two tools wrapping the ASCL API for astrophysics code discovery:

1. ASCLSearchTool — search for codes by name or capability keywords, returning
   curated code URLs, ADS bibcodes, and usage metadata.
2. ASCLGetTool — fetch a single code entry by its ASCL identifier.

Both share a single config (base_url, timeout, retries) and the same entry parser
since they hit the same API at https://ascl.net/api/search/.

ASCL is a curated registry of ~4000 astrophysics source codes. Unlike ADS (which
is paper-first), ASCL is code-first: every entry has a canonical code URL in its
site_list field, plus ADS bibcodes for the code paper (described_in) and papers
that used the code (used_in).

Key API quirk: list-valued fields (site_list, described_in, used_in, keywords) are
returned as PHP-serialized strings, not JSON arrays. This module handles the
deserialization transparently via _parse_php_array().

API docs: https://github.com/teuben/ascl-tools/tree/master/API
ASCL schema: https://ascl.net/wordpress/about-ascl/metadata-schema/
"""

from __future__ import annotations

import os
import re
from enum import StrEnum
from typing import Any

import httpx
from loguru import logger
from pydantic import Field

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig

from akd_ext.mcp import mcp_tool
from akd_ext.tools._helpers import extract_rate_limit, get_with_retry, truncate_text


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------


class ASCLToolConfig(BaseToolConfig):
    """Shared configuration for all ASCL tools."""

    base_url: str = Field(
        default_factory=lambda: os.getenv("ASCL_API_URL", "https://ascl.net/api/search/"),
        description="Base URL for the ASCL search API",
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


# ---------------------------------------------------------------------------
# Host classification (single source of truth)
# ---------------------------------------------------------------------------


class ASCLHostClass(StrEnum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    CODEBERG = "codeberg"
    SRHT = "srht"
    DOI = "doi"
    DOCS = "docs"
    ANY = "any"


# Ordered — earlier entries win in primary-URL selection.
_HOST_PATTERNS: dict[ASCLHostClass, re.Pattern] = {
    ASCLHostClass.GITHUB: re.compile(r"https?://(www\.)?github\.com/"),
    ASCLHostClass.GITLAB: re.compile(r"https?://(www\.)?gitlab\.com/"),
    ASCLHostClass.BITBUCKET: re.compile(r"https?://(www\.)?bitbucket\.org/"),
    ASCLHostClass.CODEBERG: re.compile(r"https?://(www\.)?codeberg\.org/"),
    ASCLHostClass.SRHT: re.compile(r"https?://sr\.ht/"),
    ASCLHostClass.DOI: re.compile(r"https?://(dx\.)?doi\.org/10\.|https?://zenodo\.org/record"),
    ASCLHostClass.DOCS: re.compile(r"https?://.*readthedocs\.io|https?://.*\.github\.io"),
}


# ---------------------------------------------------------------------------
# PHP deserialization + URL ranking helpers
# ---------------------------------------------------------------------------

# Matches PHP-serialized string entries: s:39:"https://..."
_PHP_STRING_RE = re.compile(r's:\d+:"([^"]*)"')


def _parse_php_array(php_str: str) -> list[str]:
    """Extract strings from a PHP-serialized array.

    The ASCL API returns list-valued fields as PHP-serialized strings like::

        a:1:{i:0;s:39:"https://emcee.readthedocs.io/en/v3.1.3/";}
    """
    if not php_str or php_str == "a:0:{}":
        return []
    return _PHP_STRING_RE.findall(php_str)


def _pick_primary_url(urls: list[str]) -> str | None:
    """Select the best code URL via host priority; falls back to first entry."""
    if not urls:
        return None
    for pattern in _HOST_PATTERNS.values():
        for url in urls:
            if pattern.search(url):
                return url
    return urls[0]


def _url_matches_host_class(url: str | None, host_class: ASCLHostClass) -> bool:
    if not url:
        return False
    if host_class == ASCLHostClass.ANY:
        return True
    pattern = _HOST_PATTERNS.get(host_class)
    return bool(pattern and pattern.search(url))


def _parse_credit(credit: str) -> list[str]:
    """Parse semicolon-separated ASCL credit string into author list."""
    if not credit:
        return []
    return [name.strip() for name in credit.split(";") if name.strip()]


# ---------------------------------------------------------------------------
# Shared output schema
# ---------------------------------------------------------------------------


class ASCLEntry(OutputSchema):
    """A single code entry from the Astrophysics Source Code Library."""

    ascl_id: str = Field(..., description="ASCL identifier (e.g. '1303.002')")
    title: str = Field(default="", description="Code title (e.g. 'emcee: The MCMC Hammer')")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    abstract: str = Field(default="", description="Code description / abstract")
    primary_url: str | None = Field(
        default=None,
        description="Preferred code URL (GitHub > GitLab > DOI/Zenodo > homepage)",
    )
    all_urls: list[str] = Field(
        default_factory=list,
        description="All URLs from the ASCL site_list field",
    )
    ads_bibcode: str | None = Field(default=None, description="ADS bibcode for this ASCL entry")
    ads_abs_url: str | None = Field(
        default=None,
        description="Direct ADS abstract URL (e.g. https://ui.adsabs.harvard.edu/abs/...)",
    )
    described_in: list[str] = Field(
        default_factory=list,
        description="ADS URLs for the paper(s) describing this code ('code paper')",
    )
    used_in: list[str] = Field(
        default_factory=list,
        description="ADS URLs for papers that used this code",
    )
    used_in_count: int = Field(default=0, description="Number of papers that used this code")
    views: int = Field(default=0, description="ASCL page view count (popularity signal)")
    citation_method: str = Field(default="", description="Preferred citation method")
    ascl_url: str = Field(default="", description="Canonical ASCL page URL")


# ---------------------------------------------------------------------------
# Shared entry parser
# ---------------------------------------------------------------------------


def _parse_entry(doc: dict, truncate_abstract: int = 0, max_authors: int = 0) -> ASCLEntry:
    """Parse a single entry from the ASCL API response."""
    ascl_id = doc.get("ascl_id", "")

    site_urls = _parse_php_array(doc.get("site_list", ""))
    described_in = _parse_php_array(doc.get("described_in", ""))
    used_in = _parse_php_array(doc.get("used_in", ""))

    authors = _parse_credit(doc.get("credit", ""))
    if max_authors > 0 and len(authors) > max_authors:
        authors = authors[:max_authors] + [f"... and {len(authors) - max_authors} more"]

    primary_url = _pick_primary_url(site_urls)

    bibcode = doc.get("bibcode", "")
    ads_abs_url = f"https://ui.adsabs.harvard.edu/abs/{bibcode}" if bibcode else None

    # Views comes back as a string from the API.
    try:
        views = int(doc.get("views", 0))
    except (ValueError, TypeError):
        views = 0

    return ASCLEntry(
        ascl_id=ascl_id,
        title=doc.get("title", ""),
        authors=authors,
        abstract=truncate_text(doc.get("abstract", ""), truncate_abstract),
        primary_url=primary_url,
        all_urls=site_urls,
        ads_bibcode=bibcode or None,
        ads_abs_url=ads_abs_url,
        described_in=described_in,
        used_in=used_in,
        used_in_count=len(used_in),
        views=views,
        citation_method=doc.get("citation_method", ""),
        ascl_url=f"https://ascl.net/{ascl_id}" if ascl_id else "",
    )


# ---------------------------------------------------------------------------
# Field presets (single source of truth)
# ---------------------------------------------------------------------------


class ASCLFieldPreset(StrEnum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    EXTENDED = "extended"


ASCL_FIELD_PRESETS: dict[ASCLFieldPreset, str] = {
    ASCLFieldPreset.MINIMAL: "ascl_id,title,site_list",
    ASCLFieldPreset.STANDARD: "ascl_id,title,credit,abstract,site_list,bibcode,described_in,used_in,views",
    ASCLFieldPreset.EXTENDED: (
        "ascl_id,title,credit,abstract,site_list,bibcode,described_in,used_in,"
        "views,citation_method,time_updated,keywords"
    ),
}


# ---------------------------------------------------------------------------
# Base class with shared HTTP plumbing
# ---------------------------------------------------------------------------


class _ASCLHttpMixin:
    """Mixin providing a lazy per-instance httpx.AsyncClient.

    Not a BaseTool subclass (so the metaclass schema check is bypassed). Expects
    ``self.config`` to satisfy the ``ASCLToolConfig`` protocol (timeout).
    """

    config: ASCLToolConfig
    _client: httpx.AsyncClient | None

    async def _get_client(self) -> httpx.AsyncClient:
        if getattr(self, "_client", None) is None:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        assert self._client is not None
        return self._client

    async def aclose(self) -> None:
        client = getattr(self, "_client", None)
        if client is not None:
            await client.aclose()
            self._client = None


# ---------------------------------------------------------------------------
# ASCLSearchTool
# ---------------------------------------------------------------------------


class ASCLSearchToolConfig(ASCLToolConfig):
    """Configuration for the ASCL Search Tool."""

    truncate_abstract: int = Field(
        default=300,
        description="Default abstract char cap (0 = no truncation). Overridable per-call via input.",
    )
    max_authors: int = Field(
        default=10,
        description="Default max authors per entry (0 = all). Overridable per-call via input.",
    )


class ASCLSearchToolInputSchema(InputSchema):
    """Input schema for ASCL code search queries."""

    query: str = Field(
        ...,
        description=(
            "Search query for astrophysics codes. Supports code names (e.g. 'emcee', "
            "'RADMC-3D'), capability keywords (e.g. 'Monte Carlo radiative transfer'), "
            'and field-specific syntax (e.g. title:"emcee", abstract:"dust")'
        ),
    )
    rows: int = Field(
        default=10,
        ge=1,
        le=50,
        description=(
            "Maximum entries to return. Enforced client-side after host-class filtering — "
            "the ASCL API itself does not accept a row limit parameter."
        ),
    )
    field_preset: ASCLFieldPreset | None = Field(
        default=None,
        description=(
            "Field preset for token efficiency. "
            "'minimal': ascl_id, title, code URLs. "
            "'standard': + authors, abstract, ADS bibcode, described_in, used_in, views. "
            "'extended': all fields including citation_method, time_updated, keywords. "
            "If None, uses 'standard'."
        ),
    )
    require_code_host: ASCLHostClass | None = Field(
        default=None,
        description=(
            "Filter to entries whose primary URL matches the given host class. "
            "One of: github, gitlab, bitbucket, codeberg, srht, doi, docs, any."
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


class ASCLSearchToolOutputSchema(OutputSchema):
    """Output schema for ASCL code search results."""

    entries: list[ASCLEntry] = Field(..., description="List of matching ASCL code entries")
    num_found: int = Field(
        default=0,
        description="Total entries matched by ASCL before host-class filtering / row-cap",
    )
    num_returned: int = Field(
        default=0,
        description="Number of entries actually returned in this response",
    )
    fields_returned: str = Field(default="", description="Fields that were requested from ASCL")
    rate_limit: dict[str, Any] = Field(
        default_factory=dict,
        description="Rate-limit headers from the ASCL response, if present",
    )


@mcp_tool
class ASCLSearchTool(_ASCLHttpMixin, BaseTool[ASCLSearchToolInputSchema, ASCLSearchToolOutputSchema]):
    """
    Search the Astrophysics Source Code Library (ASCL) for codes by name or capability.

    ASCL is a curated registry of ~4000 astrophysics source codes. Each entry has
    a canonical code URL, the ADS bibcode for the code paper, and ADS bibcodes for
    papers that used the code.

    Use this for:
    - Finding a specific code by name (emcee, RADMC-3D, HEALPix, MESA, AstroPy)
    - Finding codes that perform a specific task (radiative transfer, SED fitting, MCMC)
    - Getting the canonical URL and citation for an astrophysics code

    Complements ads_search_tool: ADS finds papers mentioning code; this finds codes directly.

    Output splits ``num_found`` (total matches from ASCL) from ``num_returned``
    (entries actually in this page after host-class filter + row cap), keeping the
    semantics aligned with ``ads_search_tool``.
    """

    input_schema = ASCLSearchToolInputSchema
    output_schema = ASCLSearchToolOutputSchema
    config_schema = ASCLSearchToolConfig
    config: ASCLSearchToolConfig

    async def _arun(self, params: ASCLSearchToolInputSchema) -> ASCLSearchToolOutputSchema:
        """Execute ASCL search query and return formatted results."""
        preset = params.field_preset or ASCLFieldPreset.STANDARD
        fields = ASCL_FIELD_PRESETS[preset]

        # ASCL API requires q wrapped in double quotes. The API rejects unknown query
        # parameters (including ``rows``), so the row cap is enforced client-side below.
        query_params: dict[str, str] = {
            "q": f'"{params.query}"',
            "fl": fields,
        }

        logger.debug(f"ASCL API request: {query_params}")

        client = await self._get_client()

        try:
            response = await get_with_retry(
                client,
                self.config.base_url,
                params=query_params,
                max_retries=self.config.max_retries,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as e:
            msg = f"ASCL API request timed out after {self.config.timeout}s"
            raise TimeoutError(msg) from e
        except httpx.HTTPStatusError as e:
            msg = f"ASCL API returned error status {e.response.status_code}: {e.response.text}"
            raise RuntimeError(msg) from e
        except Exception as e:
            msg = f"Failed to query ASCL API: {e}"
            raise RuntimeError(msg) from e

        rate_limit = extract_rate_limit(response)

        if not isinstance(data, list):
            logger.warning(f"ASCL API returned unexpected payload type: {type(data).__name__}")
            data = []

        total_matched = len(data)

        truncate_abstract = (
            params.truncate_abstract if params.truncate_abstract is not None else self.config.truncate_abstract
        )
        max_authors = params.max_authors if params.max_authors is not None else self.config.max_authors

        entries: list[ASCLEntry] = []
        for doc in data:
            entry = _parse_entry(doc, truncate_abstract, max_authors)
            if params.require_code_host and not _url_matches_host_class(entry.primary_url, params.require_code_host):
                continue
            entries.append(entry)
            if len(entries) >= params.rows:
                break

        return ASCLSearchToolOutputSchema(
            entries=entries,
            num_found=total_matched,
            num_returned=len(entries),
            fields_returned=fields,
            rate_limit=rate_limit,
        )


# ---------------------------------------------------------------------------
# ASCLGetTool
# ---------------------------------------------------------------------------


class ASCLGetToolConfig(ASCLToolConfig):
    """Configuration for the ASCL Get Tool.

    Inherits base_url, timeout, and max_retries from ASCLToolConfig.
    Defaults to no truncation for single lookups (full detail).
    """

    truncate_abstract: int = Field(
        default=0,
        description="Default abstract char cap (0 = no truncation). Overridable per-call via input.",
    )
    max_authors: int = Field(
        default=0,
        description="Default max authors (0 = all). Overridable per-call via input.",
    )


class ASCLGetInputSchema(InputSchema):
    """Input schema for ASCL entry lookup."""

    ascl_id: str = Field(
        ...,
        description=(
            "ASCL identifier to look up. Accepts formats: '1303.002', 'ascl:1303.002'. "
            "The ASCL id encodes the year and month of registration (YYMM.NNN)."
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


class ASCLGetOutputSchema(OutputSchema):
    """Output schema for ASCL entry lookup."""

    entry: ASCLEntry | None = Field(default=None, description="The ASCL entry if found, or null")
    found: bool = Field(default=False, description="Whether the entry was found")
    rate_limit: dict[str, Any] = Field(
        default_factory=dict,
        description="Rate-limit headers from the ASCL response, if present",
    )


@mcp_tool
class ASCLGetTool(_ASCLHttpMixin, BaseTool[ASCLGetInputSchema, ASCLGetOutputSchema]):
    """
    Fetch a single ASCL entry by its identifier.

    Use this when you already have an ASCL id — for example from an ADS paper
    that mentions [ascl:1303.002] in its full text, or from a previous
    ascl_search_tool result.

    Accepts id formats: '1303.002' or 'ascl:1303.002'.
    """

    input_schema = ASCLGetInputSchema
    output_schema = ASCLGetOutputSchema
    config_schema = ASCLGetToolConfig
    config: ASCLGetToolConfig

    @staticmethod
    def _normalize_id(ascl_id: str) -> str:
        """Normalize ASCL id by stripping common prefixes."""
        clean = ascl_id.strip()
        for prefix in ("ascl:", "ASCL:", "https://ascl.net/"):
            if clean.startswith(prefix):
                clean = clean[len(prefix) :]
        return clean.strip()

    async def _arun(self, params: ASCLGetInputSchema) -> ASCLGetOutputSchema:
        """Fetch a single ASCL entry by id."""
        normalized_id = self._normalize_id(params.ascl_id)

        query_params: dict[str, str] = {
            "q": f'ascl_id:"{normalized_id}"',
        }

        logger.debug(f"ASCL API get request: {query_params}")

        client = await self._get_client()

        try:
            response = await get_with_retry(
                client,
                self.config.base_url,
                params=query_params,
                max_retries=self.config.max_retries,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as e:
            msg = f"ASCL API request timed out after {self.config.timeout}s"
            raise TimeoutError(msg) from e
        except httpx.HTTPStatusError as e:
            msg = f"ASCL API returned error status {e.response.status_code}: {e.response.text}"
            raise RuntimeError(msg) from e
        except Exception as e:
            msg = f"Failed to query ASCL API: {e}"
            raise RuntimeError(msg) from e

        rate_limit = extract_rate_limit(response)

        if not isinstance(data, list) or len(data) == 0:
            return ASCLGetOutputSchema(entry=None, found=False, rate_limit=rate_limit)

        truncate_abstract = (
            params.truncate_abstract if params.truncate_abstract is not None else self.config.truncate_abstract
        )
        max_authors = params.max_authors if params.max_authors is not None else self.config.max_authors

        # Prefer exact ascl_id match; fall back to first result
        for doc in data:
            if doc.get("ascl_id") == normalized_id:
                entry = _parse_entry(doc, truncate_abstract, max_authors)
                return ASCLGetOutputSchema(entry=entry, found=True, rate_limit=rate_limit)

        entry = _parse_entry(data[0], truncate_abstract, max_authors)
        return ASCLGetOutputSchema(entry=entry, found=True, rate_limit=rate_limit)
