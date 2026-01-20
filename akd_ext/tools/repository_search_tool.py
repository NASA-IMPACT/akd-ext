from typing import Optional
from dataclasses import dataclass, field
from pydantic import Field
from akd.tools._base import BaseTool
from akd.tools.search.code_search import SDECodeSearchTool, SDECodeSearchToolConfig, CodeSearchToolInputSchema, CodeSearchToolOutputSchema
from github import Github, Auth

class RepositorySearchToolInputSchema(CodeSearchToolInputSchema):
  """
    Input schema for the repository search tool.
  """

class RepositorySearchToolOutputSchema(CodeSearchToolOutputSchema):
  """
    Output schema for the repository search tool.
  """

class RepositorySearchToolConfig(SDECodeSearchToolConfig):
  """
    Config schema for the repository search tool.
  """
  access_token: Optional[str] = Field(default=None, description="GitHub access token")

@dataclass
class RepositoryExtraMeta():
  stars: int = 0
  forks: int = 0
  open_issues: int = 0
  pulls: int = 0
  closed_pulls: int = 0

RepositoryName = str  # Format: "owner/repo"

@dataclass
class RepositorySearchToolExtra():
  repositories: dict[RepositoryName, RepositoryExtraMeta] = field(default_factory=dict)

class RepositorySearchTool(SDECodeSearchTool):
  """
  Search for code in the repository.
  """
  input_schema = RepositorySearchToolInputSchema
  output_schema = RepositorySearchToolOutputSchema
  config_schema = SDECodeSearchToolConfig
  
  async def _arun(self, params: RepositorySearchToolInputSchema) -> RepositorySearchToolOutputSchema:
    search_result: CodeSearchToolOutputSchema = await super()._arun(params)
    # put everythin inside extra as key value pair
    repositories_extra: RepositorySearchToolExtra = RepositorySearchToolExtra()
    for code_search_result in search_result.results:
      url: str = str(code_search_result.url)
      if not url:
        continue
      # Github library to get repository metadata
      parts = url.rstrip('/').split('github.com/')[-1].split('/')
      owner, repo = parts[0], parts[1]
      repo_name = f"{owner}/{repo}"
      # collect necessary metadata
      extra_meta: RepositoryExtraMeta = RepositoryExtraMeta()
      with Github() as g:
        repo = g.get_repo(repo_name)
        extra_meta.stars = repo.stargazers_count
        extra_meta.forks = repo.forks_count
        extra_meta.open_issues = repo.get_issues(state='open').totalCount
        extra_meta.pulls = repo.get_pulls(state='open', sort='created', base='master').totalCount
        extra_meta.closed_pulls = repo.get_pulls(state='closed', sort='created', base='master').totalCount
      repositories_extra.repositories[repo_name] = extra_meta

    return RepositorySearchToolOutputSchema(results=search_result.results, extra=repositories_extra.repositories)

  def _get_reliability_score(self, stars: int, forks: int, open_issues: int, pulls: int, closed_pulls: int) -> float:
    return 1.0

if __name__ == "__main__":
  import asyncio
  
  async def main():
    config = SDECodeSearchToolConfig(
      page_size = 2     
    )
    tool = RepositorySearchTool(config=config)
    result = await tool._arun(RepositorySearchToolInputSchema(queries=["indus pipeline code"]))
    print(result.model_dump().get("extra"))

  asyncio.run(main())
