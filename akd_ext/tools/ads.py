"""
NASA Astrophysics Data System (ADS) tools.

Two tools wrapping the ADS API for astrophysics paper search and link resolution:

1. ADSSearchTool — search for papers by query, returning metadata including bibcodes,
   titles, abstracts, linked data archives, and GitHub URLs extracted from full text.
2. ADSLinksResolverTool — resolve a bibcode to data archives, code repositories,
   electronic sources, and associated works.

Both share a single config (base_url, api_token, timeout) since they hit
the same API at https://api.adsabs.harvard.edu/v1.

API docs: https://github.com/adsabs/adsabs-dev-api
Resolver docs: https://github.com/adsabs/resolver_service
"""

import asyncio
import os
import re
from typing import Literal
from urllib.parse import quote, urljoin

import httpx
from loguru import logger
from pydantic import Field

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig

from akd_ext.mcp import mcp_tool


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


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _truncate_text(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, appending '...' if truncated."""
    if not text or max_chars <= 0:
        return text
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def _limit_list(items: list[str], max_items: int) -> list[str]:
    """Limit a list to max_items, appending a count suffix if truncated."""
    if not items or max_items <= 0:
        return items
    if len(items) > max_items:
        return items[:max_items] + [f"... and {len(items) - max_items} more"]
    return items


def _extract_github_urls(highlights: list[str]) -> list[str]:
    """Extract GitHub URLs from ADS highlight snippets."""
    github_urls: list[str] = []
    for snippet in highlights:
        clean = snippet.replace("<em>", "").replace("</em>", "")
        found = re.findall(r"https?://github\.com/[^\s,;)\"'<>]+", clean)
        github_urls.extend(url.rstrip(".") for url in found)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for url in github_urls:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def _build_base_url(config: ADSToolConfig) -> str:
    """Ensure trailing slash so urljoin treats it as a directory."""
    return config.base_url.rstrip("/") + "/"


# ---------------------------------------------------------------------------
# ADSSearchTool
# ---------------------------------------------------------------------------


ADS_FIELD_PRESETS: dict[str, str] = {
    "minimal": "bibcode,title,first_author,year,citation_count",
    "standard": "bibcode,title,first_author,author,year,pubdate,citation_count,doi,pub,abstract,data",
    "extended": "bibcode,title,first_author,author,year,pubdate,citation_count,doi,pub,volume,page,keyword,abstract,data,esources,property",
    "full": "bibcode,title,first_author,author,year,pubdate,citation_count,doi,pub,volume,page,keyword,abstract,data,esources,property,identifier,aff",
}


class ADSSearchToolConfig(ADSToolConfig):
    """Configuration for the ADS Search Tool."""

    truncate_abstract: int = Field(
        default=300,
        description="Truncate abstracts to this many characters (0 = no truncation). Reduces token usage.",
    )
    max_authors: int = Field(
        default=10,
        description="Maximum number of authors to return per paper (0 = all authors). Reduces token usage.",
    )
    max_results: int = Field(
        default=5,
        description="Maximum number of papers to return. Limits output size for token efficiency.",
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
        description="GitHub URLs found in the paper's full text",
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
    rows: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    field_preset: Literal["minimal", "standard", "extended", "full"] | None = Field(
        default=None,
        description=(
            "Field preset for token efficiency. "
            "'minimal': bibcode, title, first_author, year, citations. "
            "'standard': + authors, date, DOI, journal, abstract, data. "
            "'extended': + volume, page, keywords, esources, property. "
            "'full': all fields including identifiers and affiliations. "
            "If None, uses 'standard' preset."
        ),
    )
    fl: str | None = Field(
        default=None,
        description="Custom comma-separated fields to return. Overrides field_preset if provided.",
    )
    sort: str = Field(default="score desc", description="Sort order (e.g., 'score desc', 'citation_count desc')")
    fq: str | None = Field(default=None, description="Filter query to narrow results (e.g., 'property:refereed')")


class ADSSearchToolOutputSchema(OutputSchema):
    """Output schema for ADS paper search results."""

    papers: list[ADSPaper] = Field(..., description="List of matching papers from ADS")
    num_found: int = Field(default=0, description="Total number of matching papers in ADS")
    fields_returned: str = Field(default="", description="Fields that were requested from ADS")


@mcp_tool
class ADSSearchTool(BaseTool[ADSSearchToolInputSchema, ADSSearchToolOutputSchema]):
    """
    Search NASA's Astrophysics Data System (ADS) for scientific papers.

    ADS is the primary search engine for astronomy and astrophysics literature,
    indexing papers, bibcodes, DOIs, and links to observation data archives
    (HEASARC, MAST, Chandra, XMM, etc.) and code repositories (GitHub, Zenodo).

    Supports field presets for token efficiency:
    - "minimal": 5 fields — bibcode, title, first_author, year, citations
    - "standard": 11 fields — adds authors, date, DOI, journal, abstract, data archives
    - "extended": 15 fields — adds volume, page, keywords, esources, properties
    - "full": all available fields

    Input parameters (query-time, LLM-controllable):
    - query: ADS search query with field-specific syntax support
    - rows: Number of results (1-50, default: 10)
    - field_preset: Preset name for token efficiency (default: standard)
    - fl: Custom fields override (comma-separated)
    - sort: Sort order
    - fq: Filter query

    Returns papers with metadata and a list of linked data archive names.
    """

    input_schema = ADSSearchToolInputSchema
    output_schema = ADSSearchToolOutputSchema
    config_schema = ADSSearchToolConfig

    def _post_init(self) -> None:
        """Validate required configuration at instantiation time."""
        super()._post_init()
        if not self.config.api_token:
            msg = (
                "ADS_API_TOKEN environment variable is not set. "
                "Get a token from https://ui.adsabs.harvard.edu/user/settings/token"
            )
            raise RuntimeError(msg)

    def _parse_paper(self, doc: dict, github_urls: list[str] | None = None) -> ADSPaper:
        """Parse a single document from the ADS API response."""
        title_list = doc.get("title", [])
        title = title_list[0] if title_list else ""

        doi_list = doc.get("doi", [])
        doi = doi_list[0] if doi_list else None

        abstract = _truncate_text(doc.get("abstract", ""), self.config.truncate_abstract)
        authors = _limit_list(doc.get("author", []), self.config.max_authors)

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

    async def _arun(self, params: ADSSearchToolInputSchema) -> ADSSearchToolOutputSchema:
        """Execute ADS search query and return formatted results."""
        search_url = urljoin(_build_base_url(self.config), "search/query")

        if params.fl:
            fields = params.fl
        else:
            preset = params.field_preset or "standard"
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

        headers = {"Authorization": f"Bearer {self.config.api_token}"}

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.get(search_url, params=query_params, headers=headers)
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

            response_data = data.get("response", {})
            docs = response_data.get("docs", [])
            num_found = response_data.get("numFound", 0)

            top_docs = docs[: self.config.max_results]

            # For each top paper, search its full text for GitHub URLs (in parallel)
            github_urls_by_bibcode: dict[str, list[str]] = {}
            if top_docs:
                bibcodes = [doc.get("bibcode", "") for doc in top_docs if doc.get("bibcode")]

                async def _fetch_github_urls(bibcode: str) -> tuple[str, list[str]]:
                    try:
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
                        code_response = await client.get(search_url, params=code_params, headers=headers)
                        code_response.raise_for_status()
                        code_data = code_response.json()
                        highlighting = code_data.get("highlighting", {})
                        code_docs = code_data.get("response", {}).get("docs", [])
                        doc_id = str(code_docs[0].get("id", "")) if code_docs else ""
                        if doc_id and doc_id in highlighting:
                            all_snippets: list[str] = []
                            for field_snippets in highlighting[doc_id].values():
                                all_snippets.extend(field_snippets)
                            return bibcode, _extract_github_urls(all_snippets)
                    except Exception:
                        logger.debug(f"Failed to search GitHub URLs for {bibcode}")
                    return bibcode, []

                results = await asyncio.gather(*[_fetch_github_urls(b) for b in bibcodes])
                for bibcode, urls in results:
                    if urls:
                        github_urls_by_bibcode[bibcode] = urls

        papers = []
        for doc in top_docs:
            bibcode = doc.get("bibcode", "")
            github_urls = github_urls_by_bibcode.get(bibcode, [])
            papers.append(self._parse_paper(doc, github_urls=github_urls))

        return ADSSearchToolOutputSchema(papers=papers, num_found=num_found, fields_returned=fields)


# ---------------------------------------------------------------------------
# ADSLinksResolverTool
# ---------------------------------------------------------------------------


class ADSLinksResolverToolConfig(ADSToolConfig):
    """Configuration for the ADS Links Resolver Tool.

    Inherits base_url, api_token, and timeout from ADSToolConfig.
    No additional fields needed.
    """


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


@mcp_tool
class ADSLinksResolverTool(BaseTool[ADSLinksResolverInputSchema, ADSLinksResolverOutputSchema]):
    """
    Resolve data links, code repositories, and associated resources for an ADS bibcode.

    Given a paper's bibcode, returns links to external resources such as:
    - Data archives: HEASARC, MAST, Chandra, XMM, NICER, SIMBAD, NED, etc.
    - Code repositories: GitHub, Zenodo
    - Electronic sources: publisher PDFs, preprints, HTML versions
    - Associated works: related papers, data products

    Input parameters (query-time, LLM-controllable):
    - bibcode: ADS bibcode identifier (required)
    - link_type: Optional filter for specific link type ('data', 'associated', 'esource', or None for all)

    Returns a list of links with URL, title, type, and record count.
    """

    input_schema = ADSLinksResolverInputSchema
    output_schema = ADSLinksResolverOutputSchema
    config_schema = ADSLinksResolverToolConfig

    def _post_init(self) -> None:
        """Validate required configuration at instantiation time."""
        super()._post_init()
        if not self.config.api_token:
            msg = (
                "ADS_API_TOKEN environment variable is not set. "
                "Get a token from https://ui.adsabs.harvard.edu/user/settings/token"
            )
            raise RuntimeError(msg)

    @staticmethod
    def _parse_links(data: dict) -> list[ADSLink]:
        """Parse links from the ADS resolver response."""
        links: list[ADSLink] = []

        records = data.get("links", {}).get("records", [])
        if records:
            for record in records:
                url = record.get("url", "")
                title = record.get("title", "") or record.get("data", "") or ""
                link_type = record.get("link_type", "") or record.get("type", "") or ""
                count = record.get("count", 0) or 0
                if url:
                    links.append(ADSLink(url=url, title=title, link_type=link_type, count=count))
            return links

        link_type = data.get("link_type", "") or data.get("service", "") or ""
        url = data.get("action", "")
        count = data.get("links", {}).get("count", 0) if isinstance(data.get("links"), dict) else 0

        if url and url.startswith("http"):
            links.append(ADSLink(url=url, title="", link_type=link_type, count=count))

        return links

    async def _arun(self, params: ADSLinksResolverInputSchema) -> ADSLinksResolverOutputSchema:
        """Resolve links for a given ADS bibcode."""
        base = _build_base_url(self.config)
        url = urljoin(base, f"resolver/{quote(params.bibcode, safe='')}")
        if params.link_type:
            url = urljoin(url + "/", quote(params.link_type, safe=""))

        logger.debug(f"ADS Resolver request: {url}")

        headers = {"Authorization": f"Bearer {self.config.api_token}"}

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
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

        links = self._parse_links(data)

        return ADSLinksResolverOutputSchema(links=links, bibcode=params.bibcode)
