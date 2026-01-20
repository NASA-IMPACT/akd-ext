from typing import Optional
from dataclasses import dataclass, field
from pydantic import Field
from github import Github, Auth
from akd.tools._base import BaseTool
from akd.tools.search.code_search import SDECodeSearchTool, SDECodeSearchToolConfig, CodeSearchToolInputSchema, CodeSearchToolOutputSchema
from akd.tools.search._base import SearchToolOutputSchema
from akd.structures import SearchResultItem

# Tool specific data
@dataclass
class RepositoryMetadata:
  stars: int = 0
  forks: int = 0
  open_issues: int = 0
  pulls: int = 0
  closed_pulls: int = 0

class RepositorySearchToolSearchResultItem(SearchResultItem):
  """
    Search result item with added github repository metadata and computed reliability score.
  """
  reliability_score: float = Field(default=1.0, description="Computed reliability score based on github repository metadata.")
  repository_metadata: RepositoryMetadata = Field(default_factory=RepositoryMetadata, description="Github repository metadata. includes number of stars, forks, open issues, open pull requests, and closed pull requests.")

# Tool input and output schemas
class RepositorySearchToolInputSchema(CodeSearchToolInputSchema):
  """
    Input query for the repository search tool. Its a text based query that initializes the relevant code search tool.
  """

class RepositorySearchToolOutputSchema(SearchToolOutputSchema):
  """
    Output schema for the repository search tool.
  """
  results: list[RepositorySearchToolSearchResultItem] = Field(
    ...,
    description="List of search result items with added github repository metadata and computed reliability score.",
  )

# Tool config schema
class RepositorySearchToolConfig(SDECodeSearchToolConfig):
  """
    Config schema for the repository search tool.
  """
  access_token: Optional[str] = Field(default=None, description="GitHub access token")

# Tool implementation
class RepositorySearchTool(SDECodeSearchTool):
  """
  Search for code in the repository.
  """
  input_schema = RepositorySearchToolInputSchema
  output_schema = RepositorySearchToolOutputSchema
  config_schema = RepositorySearchToolConfig
  
  async def _arun(self, params: RepositorySearchToolInputSchema) -> RepositorySearchToolOutputSchema:
    # Temporarily use parent's output schema to avoid validation error caused by super()._arun(params) + parents output schema
    # TODO: better fix for this issue
    original_output_schema = self.output_schema
    self.output_schema = CodeSearchToolOutputSchema
    try:
      search_result: CodeSearchToolOutputSchema = await super()._arun(params)
    finally:
      self.output_schema = original_output_schema

    repository_search_result: RepositorySearchToolOutputSchema = RepositorySearchToolOutputSchema(results=[], extra=search_result.extra)
    # add repository metadata to each result
    for repository in search_result.results:
      url: str = str(repository.url)
      if not url:
        continue
      # Github library to get repository metadata
      parts = url.rstrip('/').split('github.com/')[-1].split('/')
      owner, repo = parts[0], parts[1]
      repo_name = f"{owner}/{repo}"
      # collect necessary metadata
      repository_metadata: RepositoryMetadata = RepositoryMetadata()
      with Github() as g:
        repo = g.get_repo(repo_name)
        repository_metadata.stars = repo.stargazers_count
        repository_metadata.forks = repo.forks_count
        repository_metadata.open_issues = repo.get_issues(state='open').totalCount
        repository_metadata.pulls = repo.get_pulls(state='open', sort='created', base='master').totalCount
        repository_metadata.closed_pulls = repo.get_pulls(state='closed', sort='created', base='master').totalCount
      reliability_score = self._get_reliability_score(repository_metadata)
      repository_search_result.results.append(RepositorySearchToolSearchResultItem(**repository.model_dump(), repository_metadata=repository_metadata, reliability_score=reliability_score))
    return repository_search_result

  def _get_reliability_score(self, repository_metadata: RepositoryMetadata) -> float:
    return 1.0

if __name__ == "__main__":
  import asyncio
  
  async def main():
    config = RepositorySearchToolConfig(
      page_size = 2     
    )
    tool = RepositorySearchTool(config=config)
    result = await tool._arun(RepositorySearchToolInputSchema(queries=["indus pipeline code"]))
    print(result.model_dump())

  asyncio.run(main())
