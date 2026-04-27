import asyncio
import json
import os
from typing import Literal
from urllib.parse import urlparse

import requests
from loguru import logger
from pydantic import Field, computed_field, model_validator
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
        default_factory=lambda: os.getenv("SDE_BASE_URL", "https://d2kqty7z3q8ugg.cloudfront.net/api/code/search"),
        description="SDE code search REST endpoint.",
    )
    page_size: int = Field(default=10, description="Number of results per page from the SDE API.")
    max_pages: int = Field(default=1, description="Maximum number of pages to fetch per query.")
    headers: dict = Field(
        default_factory=lambda: {"Content-Type": "application/json", "Accept": "application/json"},
        description="HTTP headers sent to the SDE API.",
    )
    search_mode: Literal["hybrid", "vector", "keyword"] = Field(default="hybrid", description="SDE search mode.")

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
    def _sde_search(self, page: int, query: str) -> list[dict]:
        """POST a single SDE code-search request and return the ``documents`` list."""
        payload = {
            "page": page,
            "pageSize": self.config.page_size,
            "search_term": query,
            "search_type": self.config.search_mode,
        }
        if self.debug:
            logger.debug(f"SDE payload: {payload}")
        response = requests.post(self.config.base_url, headers=self.config.headers, data=json.dumps(payload))
        return response.json()["documents"]

    async def _arun_single_query(
        self,
        query: str,
        max_results: int,
        **kwargs,
    ) -> SearchToolOutputSchema:
        """Fetch a single query's worth of results from the SDE code search API."""
        query_results: list[dict] = []
        for page in range(1, self.config.max_pages + 1):
            try:
                page_results = self._sde_search(page=page, query=query)
            except Exception as e:
                logger.error(f"Error during SDE search for '{query}' page {page}: {e}")
                continue
            if not page_results:
                break
            for result in page_results:
                result["query"] = query
            query_results.extend(page_results)

        formatted = [
            SearchResultItem(
                title=str(result.get("url", "")).split("/")[-1],
                url=HttpUrlAdapter.validate_python(result.pop("url", "")),
                content=result.pop("full_text", ""),
                query=result.pop("query", ""),
                extra=result,
            )
            for result in query_results[:max_results]
        ]
        return SearchToolOutputSchema(results=formatted)

    async def _arun(self, params: RepositorySearchToolInputSchema) -> RepositorySearchToolOutputSchema:
        search_result: SearchToolOutputSchema = await super()._arun(params)
        tasks: list[asyncio.Task] = [
            self._enrich_code_search_with_metadata(repository_item) for repository_item in search_result.results
        ]
        enriched_results: list[RepositorySearchResultItem] = await asyncio.gather(*tasks)
        repository_search_result: RepositorySearchToolOutputSchema = RepositorySearchToolOutputSchema(
            results=enriched_results, extra=search_result.extra
        )
        return repository_search_result

    async def _enrich_code_search_with_metadata(self, repository_item: SearchResultItem) -> RepositorySearchResultItem:
        url: str = str(repository_item.url)
        if not url:
            return RepositorySearchResultItem(**repository_item.model_dump())
        # Parse URL to extract owner/repo from github url
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")
        owner, repo = path_parts[0], path_parts[1]
        repo_name = f"{owner}/{repo}"
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
