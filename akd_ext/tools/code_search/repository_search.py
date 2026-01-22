import os
import asyncio
from pydantic import Field, model_validator
from urllib.parse import urlparse
from loguru import logger

from akd.tools.search.code_search import (
    SDECodeSearchTool,
    SDECodeSearchToolConfig,
    CodeSearchToolInputSchema,
    CodeSearchToolOutputSchema,
)
from akd.structures import SearchResultItem

from akd_ext.mcp import mcp_tool
from .utils import RepositoryMetadata, fetch_github_metadata, calculate_reliability_score


class RepositorySearchResultItem(SearchResultItem):
    """
    Search result item with added github repository metadata and computed reliability score.
    """

    reliability_score: float = Field(
        default=1.0, description="Computed reliability score based on github repository metadata."
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
class RepositorySearchToolConfig(SDECodeSearchToolConfig):
    """
    Config schema for the repository search tool.
    """

    access_token: str | None = Field(default=os.getenv("GITHUB_ACCESS_TOKEN", None), description="GitHub access token")


# Tool implementation
@mcp_tool
class RepositorySearchTool(SDECodeSearchTool):
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

    async def _arun(self, params: RepositorySearchToolInputSchema) -> RepositorySearchToolOutputSchema:
        search_result: CodeSearchToolOutputSchema = await super()._arun(params)
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
        reliability_score: float = calculate_reliability_score(repository_metadata)
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
