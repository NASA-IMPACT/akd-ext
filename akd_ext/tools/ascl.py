"""Astrophysics Source Code Library (ASCL) search tool.

Wraps https://ascl.net/api/search/ so agents can discover astrophysics codes
by name or capability. A single ASCL id lookup is also expressed through
this tool — pass the id as the query (e.g. '1303.002' or 'ascl:1303.002').

API docs: https://github.com/teuben/ascl-tools/tree/master/API
Metadata: https://ascl.net/wordpress/about-ascl/metadata-schema/
"""

from __future__ import annotations

import os
import re

import httpx
from pydantic import Field

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig

from akd_ext.mcp import mcp_tool


# Matches any ASCL id formatted as YYMM.### or YYMM.####. We use this to
# detect when the user's query is actually an id lookup so we can format the
# query as `ascl_id:"..."` for an exact match.
_ASCL_ID_RE = re.compile(r"\d{4}\.\d{3,4}")

# PHP-serialized string entries look like: s:39:"https://example.com"
# ASCL stores its list-valued fields (site_list, described_in, used_in,
# keywords) as PHP-serialized strings, so we extract the inner string values
# with this pattern. Verified against live API responses.
_PHP_STRING_RE = re.compile(r's:\d+:"([^"]*)"')


def _parse_php_array(php_str: str) -> list[str]:
    """Pull string entries out of a PHP-serialized array.

    ASCL returns list fields like::

        a:1:{i:0;s:39:"https://emcee.readthedocs.io/en/v3.1.3/";}

    For empty lists ASCL may return either "a:0:{}" or an empty string, so
    both yield [].
    """
    if not php_str or php_str == "a:0:{}":
        return []
    return _PHP_STRING_RE.findall(php_str)


def _normalize_ascl_id(raw: str) -> str:
    """Strip common prefixes ('ascl:', 'ASCL:', full URL) from an ASCL id."""
    clean = raw.strip()
    for prefix in ("ascl:", "ASCL:", "https://ascl.net/", "http://ascl.net/"):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    return clean.strip()


class ASCLSearchToolConfig(BaseToolConfig):
    """Configuration for the ASCL search tool."""

    base_url: str = Field(
        default_factory=lambda: os.getenv("ASCL_API_URL", "https://ascl.net/api/search/"),
        description="ASCL search endpoint URL.",
    )
    timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds.",
    )


class ASCLEntry(OutputSchema):
    """A single code entry from the Astrophysics Source Code Library."""

    ascl_id: str = Field(..., description="ASCL identifier (e.g. '1303.002').")
    title: str = Field(default="", description="Code title.")
    credit: str = Field(
        default="",
        description="Author list as a semicolon-separated string (ASCL's native format).",
    )
    abstract: str = Field(default="", description="Code description.")
    site_list: list[str] = Field(
        default_factory=list,
        description="URLs associated with the code (GitHub, project site, docs, etc.).",
    )
    bibcode: str | None = Field(default=None, description="ADS bibcode for this ASCL record.")
    described_in: list[str] = Field(
        default_factory=list,
        description="ADS URLs for papers that describe/introduce this code.",
    )
    used_in: list[str] = Field(
        default_factory=list,
        description="ADS URLs for papers that used this code.",
    )
    used_in_count: int = Field(default=0, description="Number of papers that used this code.")
    views: int = Field(default=0, description="ASCL page view count.")


class ASCLSearchToolInputSchema(InputSchema):
    """Parameters the LLM can set per query."""

    query: str = Field(
        ...,
        description=(
            "Search terms (code name, capability) or a specific ASCL id "
            "(e.g. '1303.002' or 'ascl:1303.002'). IDs are auto-detected "
            "and converted to an exact-match query."
        ),
    )
    rows: int = Field(
        default=10,
        ge=1,
        le=50,
        description=(
            "Max entries to return. Enforced client-side — the ASCL API "
            "itself does not accept a row limit."
        ),
    )


class ASCLSearchToolOutputSchema(OutputSchema):
    """What the tool returns to the caller."""

    entries: list[ASCLEntry] = Field(default_factory=list, description="Matching ASCL entries.")
    num_found: int = Field(default=0, description="Total matches from ASCL (pre row-cap).")
    error: str | None = Field(
        default=None,
        description="Error message if the query failed; null on success.",
    )


@mcp_tool
class ASCLSearchTool(BaseTool[ASCLSearchToolInputSchema, ASCLSearchToolOutputSchema]):
    """Search the Astrophysics Source Code Library (ASCL) for codes.

    ASCL is a curated registry of ~4000 astrophysics codes. Each entry has a
    canonical code URL, the ADS bibcode for the code's ASCL record, and ADS
    URLs for papers that describe and use the code.

    Use the `query` field for either:
    - a scientific task or capability keyword (e.g. 'radiative transfer'), or
    - a specific ASCL id (e.g. '1303.002') — the tool will format it as an
      exact-match query automatically.

    On failure, `error` is populated and `entries` is empty.
    """

    input_schema = ASCLSearchToolInputSchema
    output_schema = ASCLSearchToolOutputSchema
    config_schema = ASCLSearchToolConfig
    config: ASCLSearchToolConfig

    async def _arun(self, params: ASCLSearchToolInputSchema) -> ASCLSearchToolOutputSchema:
        # Decide between exact-id lookup and free-text search. The ASCL API
        # requires the `q` parameter to be wrapped in quotes either way;
        # omitting them returns a 404.
        normalized = _normalize_ascl_id(params.query)
        if _ASCL_ID_RE.fullmatch(normalized):
            q = f'ascl_id:"{normalized}"'
        else:
            q = f'"{params.query}"'

        query_params = {"q": q}

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(self.config.base_url, params=query_params)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            return ASCLSearchToolOutputSchema(error=f"ASCL query failed: {e}")

        # The API returns a JSON array of entries. If we ever get something
        # else back, surface it as an error rather than silently producing []
        # entries.
        if not isinstance(data, list):
            return ASCLSearchToolOutputSchema(
                error=f"Unexpected ASCL response type: {type(data).__name__}",
            )

        return ASCLSearchToolOutputSchema(
            entries=[_parse_entry(doc) for doc in data[: params.rows]],
            num_found=len(data),
        )


def _parse_entry(doc: dict) -> ASCLEntry:
    """Turn one raw ASCL record into an ASCLEntry.

    Handles two API quirks:
    - list-valued fields (site_list, described_in, used_in) come as PHP-
      serialized strings and need parsing.
    - `views` comes back as a string and needs int conversion; invalid values
      fall back to 0.
    """
    try:
        views = int(doc.get("views", 0))
    except (ValueError, TypeError):
        views = 0

    used_in = _parse_php_array(doc.get("used_in", ""))

    return ASCLEntry(
        ascl_id=doc.get("ascl_id", ""),
        title=doc.get("title", ""),
        credit=doc.get("credit", ""),
        abstract=doc.get("abstract", ""),
        site_list=_parse_php_array(doc.get("site_list", "")),
        bibcode=doc.get("bibcode") or None,
        described_in=_parse_php_array(doc.get("described_in", "")),
        used_in=used_in,
        used_in_count=len(used_in),
        views=views,
    )
