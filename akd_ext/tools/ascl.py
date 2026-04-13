"""
Astrophysics Source Code Library (ASCL) tools.

Two tools wrapping the ASCL API for astrophysics code discovery:

1. ASCLSearchTool — search for codes by name or capability keywords, returning
   curated code URLs, ADS bibcodes, and usage metadata.
2. ASCLGetTool — fetch a single code entry by its ASCL identifier.

Both share a single config (base_url, timeout) and the same entry parser since
they hit the same API at https://ascl.net/api/search/.

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

import os
import re
from typing import Literal

import httpx
from loguru import logger
from pydantic import Field

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig

from akd_ext.mcp import mcp_tool


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------


class ASCLToolConfig(BaseToolConfig):
    """Shared configuration for all ASCL tools."""

    base_url: str = Field(
        default=os.getenv("ASCL_API_URL", "https://ascl.net/api/search/"),
        description="Base URL for the ASCL search API",
    )
    timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
    )


# ---------------------------------------------------------------------------
# PHP deserialization + URL ranking helpers
# ---------------------------------------------------------------------------

# Matches PHP-serialized string entries: s:39:"https://..."
_PHP_STRING_RE = re.compile(r's:\d+:"([^"]*)"')

# URL host priority for primary URL selection (order matters)
_CODE_HOST_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("github", re.compile(r"https?://(www\.)?github\.com/")),
    ("gitlab", re.compile(r"https?://(www\.)?gitlab\.com/")),
    ("bitbucket", re.compile(r"https?://(www\.)?bitbucket\.org/")),
    ("codeberg", re.compile(r"https?://(www\.)?codeberg\.org/")),
    ("srht", re.compile(r"https?://sr\.ht/")),
    ("doi", re.compile(r"https?://(dx\.)?doi\.org/10\.|https?://zenodo\.org/record")),
    ("docs", re.compile(r"https?://.*readthedocs\.io|https?://.*\.github\.io")),
]


def _parse_php_array(php_str: str) -> list[str]:
    """Extract strings from a PHP-serialized array.

    The ASCL API returns list-valued fields as PHP-serialized strings like::

        a:1:{i:0;s:39:"https://emcee.readthedocs.io/en/v3.1.3/";}

    This extracts the string values into a plain Python list.
    """
    if not php_str or php_str == "a:0:{}":
        return []
    return _PHP_STRING_RE.findall(php_str)


def _pick_primary_url(urls: list[str]) -> str | None:
    """Select the best code URL from a list of site URLs.

    Priority: GitHub > GitLab > Bitbucket > Codeberg > sr.ht > DOI/Zenodo
    > ReadTheDocs/GitHub Pages > first entry.
    """
    if not urls:
        return None
    for _host_class, pattern in _CODE_HOST_PATTERNS:
        for url in urls:
            if pattern.search(url):
                return url
    return urls[0]


def _url_matches_host_class(url: str | None, host_class: str) -> bool:
    """Check if a URL matches a host class filter (github, gitlab, doi, any)."""
    if not url:
        return False
    if host_class == "any":
        return True
    for name, pattern in _CODE_HOST_PATTERNS:
        if name == host_class:
            return bool(pattern.search(url))
    return False


def _parse_credit(credit: str) -> list[str]:
    """Parse semicolon-separated ASCL credit string into author list."""
    if not credit:
        return []
    return [name.strip() for name in credit.split(";") if name.strip()]


def _truncate_text(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending '...' if truncated."""
    if not text or max_chars <= 0:
        return text
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


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
    """Parse a single entry from the ASCL API response.

    Handles PHP-serialized fields (site_list, described_in, used_in) and
    normalizes them into clean Python types.

    Args:
        doc: Raw dict from the ASCL API JSON response.
        truncate_abstract: Max abstract chars (0 = no truncation).
        max_authors: Max authors to return (0 = all).
    """
    ascl_id = doc.get("ascl_id", "")

    # Parse PHP-serialized list fields
    site_urls = _parse_php_array(doc.get("site_list", ""))
    described_in = _parse_php_array(doc.get("described_in", ""))
    used_in = _parse_php_array(doc.get("used_in", ""))

    # Parse credit string into author list
    authors = _parse_credit(doc.get("credit", ""))
    if max_authors > 0 and len(authors) > max_authors:
        authors = authors[:max_authors] + [f"... and {len(authors) - max_authors} more"]

    # Pick primary URL using host priority ranking
    primary_url = _pick_primary_url(site_urls)

    # Build ADS abstract URL from bibcode
    bibcode = doc.get("bibcode", "")
    ads_abs_url = f"https://ui.adsabs.harvard.edu/abs/{bibcode}" if bibcode else None

    # Views comes back as a string from the API
    try:
        views = int(doc.get("views", 0))
    except (ValueError, TypeError):
        views = 0

    return ASCLEntry(
        ascl_id=ascl_id,
        title=doc.get("title", ""),
        authors=authors,
        abstract=_truncate_text(doc.get("abstract", ""), truncate_abstract),
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
# Field presets (token efficiency)
# ---------------------------------------------------------------------------

ASCL_FIELD_PRESETS: dict[str, str] = {
    "minimal": "ascl_id,title,site_list",
    "standard": "ascl_id,title,credit,abstract,site_list,bibcode,described_in,used_in,views",
    "extended": "ascl_id,title,credit,abstract,site_list,bibcode,described_in,used_in,views,citation_method,time_updated,keywords",
}


# ---------------------------------------------------------------------------
# ASCLSearchTool
# ---------------------------------------------------------------------------


class ASCLSearchToolConfig(ASCLToolConfig):
    """Configuration for the ASCL Search Tool."""

    truncate_abstract: int = Field(
        default=300,
        description="Truncate abstracts to this many characters (0 = no truncation). Reduces token usage.",
    )
    max_authors: int = Field(
        default=10,
        description="Maximum number of authors to return per entry (0 = all). Reduces token usage.",
    )


class ASCLSearchToolInputSchema(InputSchema):
    """Input schema for ASCL code search queries."""

    query: str = Field(
        ...,
        description=(
            "Search query for astrophysics codes. Supports code names (e.g. 'emcee', "
            "'RADMC-3D'), capability keywords (e.g. 'Monte Carlo radiative transfer'), "
            "and field-specific syntax (e.g. title:\"emcee\", abstract:\"dust\")"
        ),
    )
    rows: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    field_preset: Literal["minimal", "standard", "extended"] | None = Field(
        default=None,
        description=(
            "Field preset for token efficiency. "
            "'minimal': ascl_id, title, code URLs. "
            "'standard': + authors, abstract, ADS bibcode, described_in, used_in, views. "
            "'extended': all fields including citation_method, time_updated, keywords. "
            "If None, uses 'standard' preset."
        ),
    )
    require_code_host: Literal["github", "gitlab", "doi", "any"] | None = Field(
        default=None,
        description="Filter to entries whose primary URL matches the given host class",
    )


class ASCLSearchToolOutputSchema(OutputSchema):
    """Output schema for ASCL code search results."""

    entries: list[ASCLEntry] = Field(..., description="List of matching ASCL code entries")
    num_found: int = Field(default=0, description="Number of entries returned")
    fields_returned: str = Field(default="", description="Fields that were requested from ASCL")


@mcp_tool
class ASCLSearchTool(BaseTool[ASCLSearchToolInputSchema, ASCLSearchToolOutputSchema]):
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

    Input parameters (query-time, LLM-controllable):
    - query: Code name or capability keywords
    - rows: Number of results (1-50, default: 10)
    - field_preset: Preset name for token efficiency (default: standard)
    - require_code_host: Filter by URL host type (github, gitlab, doi, any)

    Returns code entries with curated URLs, ADS bibcodes, and usage metadata.
    """

    input_schema = ASCLSearchToolInputSchema
    output_schema = ASCLSearchToolOutputSchema
    config_schema = ASCLSearchToolConfig

    async def _arun(self, params: ASCLSearchToolInputSchema) -> ASCLSearchToolOutputSchema:
        """Execute ASCL search query and return formatted results."""
        preset = params.field_preset or "standard"
        fields = ASCL_FIELD_PRESETS[preset]

        # ASCL API requires q value wrapped in double quotes
        query_params: dict[str, str] = {
            "q": f'"{params.query}"',
            "fl": fields,
        }

        logger.debug(f"ASCL API request: {query_params}")

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.get(self.config.base_url, params=query_params)
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

        if not isinstance(data, list):
            data = []

        entries: list[ASCLEntry] = []
        for doc in data:
            entry = _parse_entry(doc, self.config.truncate_abstract, self.config.max_authors)
            if params.require_code_host and not _url_matches_host_class(entry.primary_url, params.require_code_host):
                continue
            entries.append(entry)
            if len(entries) >= params.rows:
                break

        return ASCLSearchToolOutputSchema(
            entries=entries,
            num_found=len(entries),
            fields_returned=fields,
        )


# ---------------------------------------------------------------------------
# ASCLGetTool
# ---------------------------------------------------------------------------


class ASCLGetToolConfig(ASCLToolConfig):
    """Configuration for the ASCL Get Tool.

    Inherits base_url and timeout from ASCLToolConfig.
    Defaults to no truncation for single lookups (full detail).
    """

    truncate_abstract: int = Field(
        default=0,
        description="Truncate abstract to this many characters (0 = no truncation). Full text by default for single lookups.",
    )
    max_authors: int = Field(
        default=0,
        description="Maximum number of authors (0 = all). All authors by default for single lookups.",
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


class ASCLGetOutputSchema(OutputSchema):
    """Output schema for ASCL entry lookup."""

    entry: ASCLEntry | None = Field(default=None, description="The ASCL entry if found, or null")
    found: bool = Field(default=False, description="Whether the entry was found")


@mcp_tool
class ASCLGetTool(BaseTool[ASCLGetInputSchema, ASCLGetOutputSchema]):
    """
    Fetch a single ASCL entry by its identifier.

    Use this when you already have an ASCL id — for example from an ADS paper
    that mentions [ascl:1303.002] in its full text, or from a previous
    ascl_search_tool result.

    Accepts id formats: '1303.002' or 'ascl:1303.002'.

    Input parameters (query-time, LLM-controllable):
    - ascl_id: ASCL identifier (required)

    Returns the full entry with code URLs, ADS bibcodes, and usage metadata,
    or found=False if the id does not exist.
    """

    input_schema = ASCLGetInputSchema
    output_schema = ASCLGetOutputSchema
    config_schema = ASCLGetToolConfig

    @staticmethod
    def _normalize_id(ascl_id: str) -> str:
        """Normalize ASCL id by stripping common prefixes."""
        clean = ascl_id.strip()
        for prefix in ("ascl:", "ASCL:", "https://ascl.net/"):
            if clean.startswith(prefix):
                clean = clean[len(prefix):]
        return clean.strip()

    async def _arun(self, params: ASCLGetInputSchema) -> ASCLGetOutputSchema:
        """Fetch a single ASCL entry by id."""
        normalized_id = self._normalize_id(params.ascl_id)

        query_params: dict[str, str] = {
            "q": f'ascl_id:"{normalized_id}"',
        }

        logger.debug(f"ASCL API get request: {query_params}")

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.get(self.config.base_url, params=query_params)
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

        if not isinstance(data, list) or len(data) == 0:
            return ASCLGetOutputSchema(entry=None, found=False)

        # Prefer exact ascl_id match; fall back to first result
        for doc in data:
            if doc.get("ascl_id") == normalized_id:
                entry = _parse_entry(doc, self.config.truncate_abstract, self.config.max_authors)
                return ASCLGetOutputSchema(entry=entry, found=True)

        entry = _parse_entry(data[0], self.config.truncate_abstract, self.config.max_authors)
        return ASCLGetOutputSchema(entry=entry, found=True)
