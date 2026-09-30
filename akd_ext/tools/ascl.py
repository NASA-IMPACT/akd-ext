"""Astrophysics Source Code Library (ASCL) search tool.

Wraps https://ascl.net/api/search/ so agents can discover astrophysics codes
by name or capability. A single ASCL id lookup is also expressed through
this tool — pass the id as the query (e.g. '1303.002' or 'ascl:1303.002').

API docs: https://github.com/teuben/ascl-tools/tree/master/API
Metadata: https://ascl.net/wordpress/about-ascl/metadata-schema/
"""

from __future__ import annotations

import asyncio
import os
import re

import httpx
from pydantic import Field, computed_field

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig

from akd_ext.mcp import mcp_tool
from ._http import get_json


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


_ASCL_ID_PREFIXES = ("ascl:", "https://ascl.net/", "http://ascl.net/")


def _normalize_ascl_id(raw: str) -> str:
    """Strip common prefixes ('ascl:', full URL) from an ASCL id.

    Prefixes are matched case-insensitively and stripped repeatedly until none
    remain, with whitespace trimmed each pass, so doubled or spaced variants
    ('ascl:ascl:1303.002', 'ascl: 1303.002', 'ASCL:1303.002') all normalize to
    the bare id.
    """
    clean = raw.strip()
    changed = True
    while changed:
        changed = False
        for prefix in _ASCL_ID_PREFIXES:
            if clean.lower().startswith(prefix):
                clean = clean[len(prefix):].strip()
                changed = True
    return clean


def _quote_term(term: str) -> str:
    """Wrap a term in the double quotes the ASCL API requires.

    Embedded double quotes are dropped so they can't unbalance the wrapper and
    produce a malformed query.
    """
    return '"' + term.replace('"', "") + '"'


def _intersect_by_id(per_term: list[list[dict]]) -> list[dict]:
    """Intersect per-term ASCL result lists by ``ascl_id`` (order-independent AND).

    Keeps a record only if its ``ascl_id`` appears in every term's result set,
    preserving the ordering of the first term's list. An empty ``per_term`` or
    any term with no matches yields ``[]`` — the AND has no matches.
    """
    if not per_term:
        return []
    common = set.intersection(*({doc.get("ascl_id") for doc in docs} for docs in per_term))
    common.discard(None)
    seen: set[str] = set()
    result: list[dict] = []
    for doc in per_term[0]:
        ascl_id = doc.get("ascl_id")
        if ascl_id in common and ascl_id not in seen:
            seen.add(ascl_id)
            result.append(doc)
    return result


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
    views: int = Field(default=0, description="ASCL page view count.")

    @computed_field(description="Number of papers that used this code.")
    @property
    def used_in_count(self) -> int:
        return len(self.used_in)


class ASCLSearchToolInputSchema(InputSchema):
    """Parameters the LLM can set per query."""

    query: str = Field(
        ...,
        min_length=1,
        description=(
            "Search terms (code name, capability) or a specific ASCL id "
            "(e.g. '1303.002' or 'ascl:1303.002'). IDs are auto-detected "
            "and converted to an exact-match query. Multiple words are "
            "ANDed together (order-independent)."
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

    The ASCL API only exact-phrase matches a quoted query, so a multi-word
    free-text search is run as one quoted search per word and the results are
    intersected by ASCL id — matching every word in any order, rather than
    only the exact phrase.

    On failure, `error` is populated and `entries` is empty.
    """

    input_schema = ASCLSearchToolInputSchema
    output_schema = ASCLSearchToolOutputSchema
    config_schema = ASCLSearchToolConfig
    config: ASCLSearchToolConfig

    async def _ascl_search(self, client: httpx.AsyncClient, q: str) -> list[dict]:
        """Run one ASCL query and return its list of record dicts.

        The ASCL API requires the `q` parameter to be wrapped in quotes;
        callers pass an already-quoted `q`. A non-list body (the API's error
        shape) is raised so `_arun` reports it via `error`.
        """
        data = await get_json(self.config.base_url, client=client, params={"q": q})
        if not isinstance(data, list):
            raise ValueError(f"Unexpected ASCL response type: {type(data).__name__}")
        return [doc for doc in data if isinstance(doc, dict)]

    async def _arun(self, params: ASCLSearchToolInputSchema) -> ASCLSearchToolOutputSchema:
        normalized = _normalize_ascl_id(params.query)
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                if _ASCL_ID_RE.fullmatch(normalized):
                    # Exact id lookup.
                    docs = await self._ascl_search(client, f'ascl_id:"{normalized}"')
                else:
                    # Free-text: AND the words together, order-independent. One
                    # quoted search per word, then intersect by ascl_id — see
                    # _intersect_by_id. Split the *normalized* query so a stripped
                    # 'ascl:'/URL prefix can't leak back in as a required term;
                    # split() also drops surrounding whitespace, so a
                    # whitespace-only query yields no terms and no matches.
                    terms = normalized.split()
                    if not terms:
                        return ASCLSearchToolOutputSchema()
                    per_term = await asyncio.gather(
                        *(self._ascl_search(client, _quote_term(term)) for term in terms)
                    )
                    docs = _intersect_by_id(per_term)
            entries = [_parse_entry(doc) for doc in docs[: params.rows]]
            num_found = len(docs)
        except Exception as e:
            return ASCLSearchToolOutputSchema(error=f"ASCL query failed: {e}")

        return ASCLSearchToolOutputSchema(entries=entries, num_found=num_found)


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

    # `x or default` (not `.get(x, default)`) so an explicit null from ASCL maps
    # to the schema default instead of failing validation on a non-nullable field.
    # used_in_count is a computed_field derived from used_in, so it is not set here.
    return ASCLEntry(
        ascl_id=doc.get("ascl_id") or "",
        title=doc.get("title") or "",
        credit=doc.get("credit") or "",
        abstract=doc.get("abstract") or "",
        site_list=_parse_php_array(doc.get("site_list", "")),
        bibcode=doc.get("bibcode") or None,
        described_in=_parse_php_array(doc.get("described_in", "")),
        used_in=_parse_php_array(doc.get("used_in", "")),
        views=views,
    )
