"""NASA Astrophysics Data System (ADS) tools.

Two tools wrapping the ADS API:

- ADSSearchTool:         search the literature for papers matching a query.
- ADSLinksResolverTool:  given a bibcode, list the 'associated' bibcodes
                          (ADS's "Described in" relationship). This is how
                          we recover the canonical method papers for an ASCL
                          record, which ASCL itself often under-reports.

API docs: https://ui.adsabs.harvard.edu/help/api/api-docs.html
Dev API:  https://github.com/adsabs/adsabs-dev-api
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

from pydantic import Field

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig

from akd_ext.mcp import mcp_tool
from ._http import get_json


# Fields requested from ADS. This fixed set covers the common needs for
# scientific code discovery: identification (bibcode, doi), metadata (title,
# authors, year, publication), relevance (abstract, citation_count), and
# linked resources (data archive names via `data`, access via `esources`,
# flags like REFEREED via `property`).
_ADS_FIELDS = (
    "bibcode,title,first_author,author,abstract,year,pubdate,"
    "citation_count,doi,pub,data,esources,property"
)

# ADS requires a bearer token. Missing-token is reported per call (see each
# tool's `_arun`) rather than raised at config construction — the MCP server
# instantiates every tool at import time, so a raising validator here would
# take down the whole server when ADS_API_TOKEN is unset.
_NO_TOKEN_ERROR = (
    "ADS_API_TOKEN is not set. Get a token from https://ui.adsabs.harvard.edu/user/settings/token"
)


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------


class ADSToolConfig(BaseToolConfig):
    """Shared configuration for all ADS tools.

    Both the search tool and the links-resolver tool hit the same API and
    need the same values (base URL, bearer token, timeout), so they share
    this single config.
    """

    base_url: str = Field(
        default="https://api.adsabs.harvard.edu/v1",
        description="Base URL for the ADS API.",
    )

    api_token: str = Field(
        default_factory=lambda: os.environ.get("ADS_API_TOKEN", ""),
        description="ADS API bearer token. Defaults to the ADS_API_TOKEN env var.",
    )

    timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds.",
    )


# ---------------------------------------------------------------------------
# ADSSearchTool
# ---------------------------------------------------------------------------


class ADSPaper(OutputSchema):
    """A single paper returned by ADS search."""

    bibcode: str = Field(..., description="ADS bibcode (unique paper identifier).")
    title: str = Field(default="", description="Paper title.")
    first_author: str = Field(default="", description="First author name.")
    authors: list[str] = Field(default_factory=list, description="All author names.")
    abstract: str = Field(default="", description="Paper abstract.")
    year: str | None = Field(default=None, description="Publication year.")
    pubdate: str | None = Field(default=None, description="Publication date.")
    citation_count: int = Field(default=0, description="Number of citations.")
    doi: str | None = Field(default=None, description="DOI if available.")
    pub: str | None = Field(default=None, description="Journal or publication name.")
    data: list[str] = Field(
        default_factory=list,
        description="Names of linked data archives (e.g. 'HEASARC', 'MAST', 'Chandra').",
    )
    esources: list[str] = Field(
        default_factory=list,
        description="Electronic source types (e.g. 'PUB_HTML', 'EPRINT_HTML').",
    )
    property: list[str] = Field(
        default_factory=list,
        description="Paper properties (e.g. 'REFEREED', 'OPENACCESS').",
    )


class ADSSearchToolInputSchema(InputSchema):
    """Parameters the LLM can set per query."""

    query: str = Field(
        ...,
        description=(
            "ADS search query. Supports free text and Solr field syntax — examples: "
            "'dark matter', 'title:\"emcee\"', 'abs:\"ultra-fast outflow\"', "
            "'bibcode:\"2013PASP..125..306F\"'."
        ),
    )
    rows: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max number of papers to return.",
    )
    fq: str | None = Field(
        default=None,
        description="Optional filter query, e.g. 'property:refereed'.",
    )


class ADSSearchToolOutputSchema(OutputSchema):
    """What the tool returns to the caller."""

    papers: list[ADSPaper] = Field(default_factory=list, description="Matching papers.")
    num_found: int = Field(
        default=0,
        description="Total matches in ADS (may exceed rows).",
    )
    error: str | None = Field(
        default=None,
        description="Error message when the query failed; null on success.",
    )


@mcp_tool
class ADSSearchTool(BaseTool[ADSSearchToolInputSchema, ADSSearchToolOutputSchema]):
    """Search NASA's Astrophysics Data System (ADS) for scientific papers.

    Returns a list of papers with bibcode, title, authors, abstract, citation
    count, DOI, and names of linked data archives. On failure, `error` is
    populated and `papers` is empty.
    """

    input_schema = ADSSearchToolInputSchema
    output_schema = ADSSearchToolOutputSchema
    config_schema = ADSToolConfig
    config: ADSToolConfig

    async def _arun(self, params: ADSSearchToolInputSchema) -> ADSSearchToolOutputSchema:
        if not self.config.api_token:
            return ADSSearchToolOutputSchema(error=_NO_TOKEN_ERROR)
        url = f"{self.config.base_url.rstrip('/')}/search/query"
        headers = {"Authorization": f"Bearer {self.config.api_token}"}
        query_params: dict[str, str] = {
            "q": params.query,
            "fl": _ADS_FIELDS,
            "rows": str(params.rows),
        }
        if params.fq:
            query_params["fq"] = params.fq

        try:
            data = await get_json(url, headers=headers, params=query_params, timeout=self.config.timeout)
            # Parse inside the try so a malformed-but-200 body is reported via
            # `error` rather than raising out of the tool. `x or {}` also guards
            # against an explicit {"response": null}, which .get(k, {}) would not.
            response_data = data.get("response") or {}
            docs: list[dict] = response_data.get("docs", [])
            papers = [_parse_paper(doc) for doc in docs if isinstance(doc, dict)]
            num_found = response_data.get("numFound", 0)
        except Exception as e:
            return ADSSearchToolOutputSchema(error=f"ADS query failed: {e}")

        return ADSSearchToolOutputSchema(papers=papers, num_found=num_found)


def _first_str(value: Any) -> str:
    """Unwrap an ADS field that is usually a single-element list.

    ADS normally returns `title`/`doi` as `["..."]`, but a bare scalar string
    can appear with API/version variance or a proxied response. Return the
    string either way, and "" for anything else — never index into a bare
    string (which would silently yield its first character).
    """
    if isinstance(value, list):
        return value[0] if value and isinstance(value[0], str) else ""
    return value if isinstance(value, str) else ""


def _parse_paper(doc: dict) -> ADSPaper:
    """Turn one ADS response document into an ADSPaper."""
    # `x or default` (not `.get(x, default)`) so an explicit null from ADS maps
    # to the schema default instead of failing validation on a non-nullable field.
    return ADSPaper(
        bibcode=doc.get("bibcode") or "",
        title=_first_str(doc.get("title")),
        first_author=doc.get("first_author") or "",
        authors=doc.get("author") or [],
        abstract=doc.get("abstract") or "",
        year=doc.get("year"),
        pubdate=doc.get("pubdate"),
        citation_count=doc.get("citation_count") or 0,
        doi=_first_str(doc.get("doi")) or None,
        pub=doc.get("pub"),
        data=doc.get("data") or [],
        esources=doc.get("esources") or [],
        property=doc.get("property") or [],
    )


# ---------------------------------------------------------------------------
# ADSLinksResolverTool
# ---------------------------------------------------------------------------
#
# ADS maintains an "associated" relationship between records that the search
# index does not expose. For an ASCL record bibcode (e.g. 2010ascl.soft10082F),
# the associated bibcodes are the code's canonical method/description papers.
# This is the only reliable way to recover the high-citation canonical paper
# when ASCL's own `described_in` field is incomplete — which it often is: the
# FLASH ASCL record lists only the 2005 update paper, and the canonical
# Fryxell+ 2000 paper is reachable only via this resolver.
#
# Endpoint: GET /v1/resolver/{bibcode}/associated
# curl -H "Authorization: Bearer API_KEY" \
# "https://api.adsabs.harvard.edu/v1/resolver/2010ascl.soft10082F/associated" | python3 -m json.tool


class ADSLinksResolverInputSchema(InputSchema):
    """Parameters the LLM can set per lookup."""

    bibcode: str = Field(
        ...,
        description=(
            "ADS bibcode to resolve associated works for. Typically an ASCL "
            "record bibcode (e.g. '2010ascl.soft10082F'), for which the "
            "associated bibcodes are the code's description papers."
        ),
    )


class ADSLinksResolverOutputSchema(OutputSchema):
    """What the resolver returns to the caller."""

    bibcode: str = Field(..., description="The bibcode that was resolved.")
    associated_bibcodes: list[str] = Field(
        default_factory=list,
        description="Bibcodes of papers ADS lists as associated with the input bibcode.",
    )
    error: str | None = Field(
        default=None,
        description="Error message if the lookup failed; null on success.",
    )


@mcp_tool
class ADSLinksResolverTool(BaseTool[ADSLinksResolverInputSchema, ADSLinksResolverOutputSchema]):
    """Resolve an ADS bibcode to its 'associated' bibcodes.

    For ASCL record bibcodes (format: YYYYascl.softNNNNNN), the associated
    bibcodes are the code's canonical description papers — these are the
    papers ADS shows under "Described in" on the record page, and they are
    the authoritative source for `describing_bibcodes` in agent output.

    On failure, `error` is populated and `associated_bibcodes` is empty.
    """

    input_schema = ADSLinksResolverInputSchema
    output_schema = ADSLinksResolverOutputSchema
    config_schema = ADSToolConfig
    config: ADSToolConfig

    async def _arun(self, params: ADSLinksResolverInputSchema) -> ADSLinksResolverOutputSchema:
        if not self.config.api_token:
            return ADSLinksResolverOutputSchema(bibcode=params.bibcode, error=_NO_TOKEN_ERROR)
        # Bibcodes can contain characters that must be percent-encoded in
        # the URL path (e.g. '&' in '2005Ap&SS.298..341W'). Pass `safe=""`
        # to quote() so nothing is left unescaped.
        encoded_bibcode = quote(params.bibcode, safe="")
        url = f"{self.config.base_url.rstrip('/')}/resolver/{encoded_bibcode}/associated"
        headers = {"Authorization": f"Bearer {self.config.api_token}"}

        try:
            data = await get_json(url, headers=headers, timeout=self.config.timeout)
            # `x or {}` guards against an explicit null (e.g. {"links": null}),
            # which .get(k, {}) would not; parse inside the try so any shape
            # surprise is reported via `error` instead of raising.
            records = (data.get("links") or {}).get("records") or []
            bibcodes = [r["bibcode"] for r in records if isinstance(r, dict) and r.get("bibcode")]
        except Exception as e:
            return ADSLinksResolverOutputSchema(
                bibcode=params.bibcode,
                error=f"ADS resolver failed: {e}",
            )

        return ADSLinksResolverOutputSchema(
            bibcode=params.bibcode,
            associated_bibcodes=bibcodes,
        )
