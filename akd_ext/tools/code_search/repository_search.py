import asyncio
import os
from typing import Literal
from urllib.parse import urlparse

import httpx
from loguru import logger
from pydantic import Field, ValidationError, computed_field, model_validator
from tenacity import retry, stop_after_attempt

from akd.structures import SearchResultItem
from akd.tools.misc import HttpUrlAdapter
from akd.tools.search import (
    SearchTool,
    SearchToolConfig,
    SearchToolInputSchema,
    SearchToolOutputSchema,
)

from akd_ext.mcp import mcp_tool
from .utils import RepositoryMetadata, fetch_github_metadata, calculate_reliability_score


# Schemas (formerly inherited from akd.tools.search.code_search; ported locally
# after that module was removed upstream — see akd commit 771d7c3.)
class CodeSearchToolInputSchema(SearchToolInputSchema):
    """Input schema for code search; exposes ``top_k`` as an alias for ``max_results``."""

    @computed_field
    def top_k(self) -> int:
        return self.max_results


class CodeSearchToolOutputSchema(SearchToolOutputSchema):
    """Output schema for code search."""


class RepositorySearchResultItem(SearchResultItem):
    """
    Search result item with added github repository metadata and computed reliability score.
    """

    reliability_score: float | None = Field(
        default=None,
        description="Computed reliability score based on github repository metadata. If none, treat it neutrally as if there is no reliability score.",
    )
    repository_metadata: RepositoryMetadata = Field(
        default_factory=RepositoryMetadata,
        description="Github repository metadata. includes number of stars, forks, open issues, open pull requests, and closed pull requests.",
    )

    @model_validator(mode="before")
    @classmethod
    def convert_parent_instance(cls, data):
        """
        While we call super()._arun(params), the parent pydantic validation runs on the parents output schema.
        The data of the parent instance is SearchResultItem. However, the data of this cls is RepositorySearchResultItem.
        To avoid this pydantic validation inconsistency on results, we need to return the model dump of the parent instance.
        TODO: fix this issue in the core
        """
        if isinstance(data, SearchResultItem) and not isinstance(data, cls):
            return data.model_dump()
        return data


# Tool input and output schemas
class RepositorySearchToolInputSchema(CodeSearchToolInputSchema):
    """
    Input query for the repository search tool. Its a text based query that initializes the relevant code search tool.
    """


class RepositorySearchToolOutputSchema(CodeSearchToolOutputSchema):
    """
    Output schema for the repository search tool.
    """

    results: list[RepositorySearchResultItem] = Field(
        ...,
        description="List of search result items with added github repository metadata and computed reliability score.",
    )


# Tool config schema
class RepositorySearchToolConfig(SearchToolConfig):
    """
    Config schema for the repository search tool.
    """

    # SDE search backend (formerly inherited from SDECodeSearchToolConfig).
    base_url: str = Field(
        default_factory=lambda: os.getenv("SDE_BASE_URL", "https://dyejsbdumgpqz.cloudfront.net/api/code/search"),
        description="SDE code search REST endpoint.",
    )
    page_size: int = Field(default=10, description="Number of results per page from the SDE API.")
    max_pages: int = Field(default=1, description="Maximum number of pages to fetch per query.")
    headers: dict = Field(
        default_factory=lambda: {"Content-Type": "application/json", "Accept": "application/json"},
        description="HTTP headers sent to the SDE API.",
    )
    search_mode: Literal["hybrid", "vector", "keyword"] = Field(default="hybrid", description="SDE search mode.")
    min_score: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Minimum relevance score a document must reach to be returned. Sent on every request "
            "because the endpoint applies a server-side default of 0.55 when the field is omitted, "
            "which is above the score most documents receive and silently drops them."
        ),
    )

    # URL is the only stable identity signal for code repositories, so RRF and
    # deduplication are restricted to it (vs the upstream default of doi/title/url).
    rrf_keys: list[str] = Field(default_factory=lambda: ["url"])
    deduplication_keys: list[str] = Field(default_factory=lambda: ["url"])
    # SDE results don't carry resolvable DOIs; skip the resolver pass.
    result_normalization: bool = Field(default=False)

    access_token: str | None = Field(
        default_factory=lambda: os.getenv("GITHUB_ACCESS_TOKEN", None),
        description="GitHub access token.",
    )


# Tool implementation
@mcp_tool
class RepositorySearchTool(SearchTool):
    """
    Search for relevant code and implementations within specialized science repositories.

    This tool performs a targeted search across curated scientific codebases to find
    relevant GitHub repositories with README. It enriches the search results with
    GitHub metadata such as stars, forks, and development activity, which are then
    used to compute a reliability score for each item.

    The reliability score (0-100) is a weighted average of repository maturity, activity, and community trust.

    The formula: Score = (Age * 0.20) + (Activity * 0.25) + (Stars * 0.25) + (Forks * 0.15) + (History * 0.15)

    How components are calculated:
      - Age (20%): Higher for older repos; reaches 100% after 4 years.
      - Activity (25%): Starts at 100% and drops to 0% if the repo hasn't been updated in a year.
      - Stars (25%): Logarithmic scale where ~1,000 stars = 100%.
      - Forks (15%): Logarithmic scale where ~500 forks = 100%.
      - History (15%): Based on the span between the first commit and now; reaches 100% after 4 years.
    """

    input_schema = RepositorySearchToolInputSchema
    output_schema = RepositorySearchToolOutputSchema
    config_schema = RepositorySearchToolConfig

    @retry(stop=stop_after_attempt(2))
    async def _sde_search(self, client: httpx.AsyncClient, page: int, query: str) -> list[dict]:
        """POST a single SDE code-search request and return the ``documents`` list."""
        payload = {
            "page": page,
            "pageSize": self.config.page_size,
            "search_term": query,
            "search_type": self.config.search_mode,
            "min_score": self.config.min_score,
        }
        if self.debug:
            logger.debug(f"SDE payload: {payload}")
        response = await client.post(self.config.base_url, headers=self.config.headers, json=payload)
        # Surface HTTP errors (and let @retry act on transient 5xx) instead of
        # silently treating an error body as "no results".
        response.raise_for_status()
        return response.json()["documents"]

    async def _arun_single_query(
        self,
        query: str,
        max_results: int,
        **kwargs,
    ) -> SearchToolOutputSchema:
        """Fetch a single query's worth of results from the SDE code search API."""
        query_results: list[dict] = []
        # One client reused across pages (and @retry attempts) instead of one per request.
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            for page in range(1, self.config.max_pages + 1):
                try:
                    page_results = await self._sde_search(client, page=page, query=query)
                except Exception as e:
                    logger.error(f"Error during SDE search for '{query}' page {page}: {e}")
                    continue
                if not page_results:
                    break
                for result in page_results:
                    result["query"] = query
                query_results.extend(page_results)

        # Filter to valid URLs first, then cap at max_results, so a skipped bad row
        # backfills from later results rather than shrinking the returned count.
        formatted: list[SearchResultItem] = []
        for result in query_results:
            if len(formatted) >= max_results:
                break
            raw_url = result.pop("url", "")
            try:
                url = HttpUrlAdapter.validate_python(raw_url)
            except ValidationError:
                logger.debug(f"Skipping SDE result with invalid URL {raw_url!r}")
                continue
            formatted.append(
                SearchResultItem(
                    title=raw_url.rstrip("/").split("/")[-1],
                    url=url,
                    content=result.pop("full_text", ""),
                    query=result.pop("query", ""),
                    extra=result,
                )
            )
        return SearchToolOutputSchema(results=formatted)

    async def _arun(self, params: RepositorySearchToolInputSchema) -> RepositorySearchToolOutputSchema:
        search_result: SearchToolOutputSchema = await super()._arun(params)
        tasks = [
            self._enrich_code_search_with_metadata(repository_item) for repository_item in search_result.results
        ]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        # A single enrichment failure must not sink the whole result set: keep the
        # result with empty metadata rather than propagating the exception.
        enriched_results: list[RepositorySearchResultItem] = []
        for item, outcome in zip(search_result.results, outcomes):
            if isinstance(outcome, Exception):
                logger.error(f"Metadata enrichment failed for {item.url}: {outcome}")
                enriched_results.append(RepositorySearchResultItem(**item.model_dump()))
            else:
                enriched_results.append(outcome)
        repository_search_result: RepositorySearchToolOutputSchema = RepositorySearchToolOutputSchema(
            results=enriched_results, extra=search_result.extra
        )
        return repository_search_result

    @staticmethod
    def _github_repo_name(url: str) -> str | None:
        """Return ``owner/repo`` for a GitHub URL, or None when the URL isn't one.

        The SDE code index is overwhelmingly GitHub repositories, but a result URL is
        not guaranteed to carry an owner and repo path segment (org pages, other hosts),
        so callers must handle None rather than index blindly.
        """
        parsed = urlparse(url)
        if parsed.netloc.lower().removeprefix("www.") != "github.com":
            return None
        parts = [segment for segment in parsed.path.split("/") if segment]
        if len(parts) < 2:
            return None
        return f"{parts[0]}/{parts[1]}"

    async def _enrich_code_search_with_metadata(self, repository_item: SearchResultItem) -> RepositorySearchResultItem:
        repo_name: str | None = self._github_repo_name(str(repository_item.url))
        if repo_name is None:
            # Non-GitHub / non-owner-repo URL: return it with empty metadata and a null
            # reliability score rather than raising and sinking the whole gather.
            return RepositorySearchResultItem(**repository_item.model_dump())
        repository_metadata: RepositoryMetadata = await fetch_github_metadata(repo_name, self.config.access_token)
        reliability_score: float | None = calculate_reliability_score(repository_metadata)
        return RepositorySearchResultItem(
            **{
                **repository_item.model_dump(),
                "repository_metadata": repository_metadata,
                "reliability_score": reliability_score,
            }
        )


if __name__ == "__main__":
    import asyncio
    import sys

    config = RepositorySearchToolConfig(page_size=2)
    query = "indus pipeline code"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    tool = RepositorySearchTool(config=config)
    result = asyncio.run(tool.arun(RepositorySearchToolInputSchema(queries=[query])))
    logger.info(result.model_dump())
