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
from urllib.parse import quote

import httpx
from pydantic import Field, model_validator

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig

from akd_ext.mcp import mcp_tool


# Fields requested from ADS. This fixed set covers the common needs for
# scientific code discovery: identification (bibcode, doi), metadata (title,
# authors, year, publication), relevance (abstract, citation_count), and
# linked resources (data archive names via `data`, access via `esources`,
# flags like REFEREED via `property`).
_ADS_FIELDS = (
    "bibcode,title,first_author,author,abstract,year,pubdate,"
    "citation_count,doi,pub,data,esources,property"
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

    @model_validator(mode="after")
    def _require_api_token(self) -> "ADSToolConfig":
        # ADS requires authentication. Fail fast at config creation if no token
        # is available, rather than surfacing a 401 at query time.
        if not self.api_token:
            raise ValueError(
                "ADS_API_TOKEN environment variable is not set. "
                "Get a token from https://ui.adsabs.harvard.edu/user/settings/token"
            )
        return self


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
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(url, params=query_params, headers=headers)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            return ADSSearchToolOutputSchema(error=f"ADS query failed: {e}")

        response_data = data.get("response", {})
        docs: list[dict] = response_data.get("docs", [])

        return ADSSearchToolOutputSchema(
            papers=[_parse_paper(doc) for doc in docs],
            num_found=response_data.get("numFound", 0),
        )


def _parse_paper(doc: dict) -> ADSPaper:
    """Turn one ADS response document into an ADSPaper.

    ADS returns `title` and `doi` as single-element lists, so we unwrap them.
    Everything else maps directly.
    """
    title_list = doc.get("title") or []
    doi_list = doc.get("doi") or []
    return ADSPaper(
        bibcode=doc.get("bibcode", ""),
        title=title_list[0] if title_list else "",
        first_author=doc.get("first_author", ""),
        authors=doc.get("author", []),
        abstract=doc.get("abstract", ""),
        year=doc.get("year"),
        pubdate=doc.get("pubdate"),
        citation_count=doc.get("citation_count", 0),
        doi=doi_list[0] if doi_list else None,
        pub=doc.get("pub"),
        data=doc.get("data", []),
        esources=doc.get("esources", []),
        property=doc.get("property", []),
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
        # Bibcodes can contain characters that must be percent-encoded in
        # the URL path (e.g. '&' in '2005Ap&SS.298..341W'). Pass `safe=""`
        # to quote() so nothing is left unescaped.
        encoded_bibcode = quote(params.bibcode, safe="")
        url = f"{self.config.base_url.rstrip('/')}/resolver/{encoded_bibcode}/associated"
        headers = {"Authorization": f"Bearer {self.config.api_token}"}

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            return ADSLinksResolverOutputSchema(
                bibcode=params.bibcode,
                error=f"ADS resolver failed: {e}",
            )

        records = data.get("links", {}).get("records", [])
        bibcodes = [r["bibcode"] for r in records if r.get("bibcode")]

        return ADSLinksResolverOutputSchema(
            bibcode=params.bibcode,
            associated_bibcodes=bibcodes,
        )
