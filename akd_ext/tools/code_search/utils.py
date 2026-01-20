from github import Github, Auth
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import math

class RepositoryMetadata(BaseModel):
  """
    Github repository metadata. includes number of stars, forks, open issues, open pull requests, and closed pull requests.
  """
  # reliability metrics
  stars: int = Field(default=0, description="Number of stars on the repository.")
  forks: int = Field(default=0, description="Number of forks on the repository.")
  watchers: int = Field(default=0, description="Number of watchers on the repository.")
  last_updated: str = Field(default="", description="Last updated date of the repository.")
  created_at: str = Field(default="", description="Creation date of the repository.")
  first_commit_date: str = Field(default="", description="Date of the first commit in the repository.")
  # few extra metrics
  open_issues: int = Field(default=0, description="Number of open issues on the repository.")
  pulls: int = Field(default=0, description="Number of open pull requests on the repository.")
  closed_pulls: int = Field(default=0, description="Number of closed pull requests on the repository.")

async def fetch_github_metadata(repo_name: str, access_token: str | None = None) -> RepositoryMetadata:
  """
    Repo_name should be in the format of owner/repo
  """
  repository_metadata: RepositoryMetadata = RepositoryMetadata()
  auth = None
  if access_token:
    auth = Auth.Token(access_token)
  with Github(auth=auth) as g:
    repo = g.get_repo(repo_name)
    repository_metadata.stars = repo.stargazers_count
    repository_metadata.forks = repo.forks_count
    repository_metadata.watchers = repo.subscribers_count
    repository_metadata.last_updated = repo.pushed_at.isoformat() if repo.pushed_at else ""
    repository_metadata.created_at = repo.created_at.isoformat() if repo.created_at else ""
    repository_metadata.open_issues = repo.get_issues(state='open').totalCount
    repository_metadata.pulls = repo.get_pulls(state='open', sort='created', base='master').totalCount
    repository_metadata.closed_pulls = repo.get_pulls(state='closed', sort='created', base='master').totalCount
    try:
      # Get first commit date
      commits = repo.get_commits() # TODO: optimize this, this takes a lot of time. even goes through rate limits.
      first_commit = list(commits)[-1] if commits.totalCount > 0 else None
      repository_metadata.first_commit_date = first_commit.commit.author.date.isoformat() if first_commit else ""
    except Exception:
      repository_metadata.first_commit_date = ""
  return repository_metadata

def calculate_reliability_score(repository_metadata: RepositoryMetadata) -> float:
  """
  Calculate a comprehensive reliability score (0-100) for a repository.

  Components:
  - Repository Age (20%): Older repos are more mature (capped at 4 years)
  - Recent Activity (25%): Recently updated repos are actively maintained
  - Stars (25%): High stars indicate community trust (log scale)
  - Forks (15%): High forks indicate code reuse (log scale)
  - Development History (15%): Longer development history indicates stability

  Args:
      repository_metadata: RepositoryMetadata with stars, forks, created_at, last_updated, first_commit_date

  Returns:
      float: reliability score between 0 and 100
  """
  now = datetime.now(timezone.utc)
  
  # Parse dates - return 0 if essential data is missing
  if not repository_metadata.created_at:
    return 0.0
  
  try:
    created_at = datetime.fromisoformat(repository_metadata.created_at.replace('Z', '+00:00'))
  except (ValueError, AttributeError):
    return 0.0

  # 1. Repository Age Score (20%) - capped at 4 years (1460 days)
  days_since_created = (now - created_at).total_seconds() / (24 * 3600)
  score_age = min(days_since_created / 1460 * 100, 100) * 0.20

  # 2. Recent Activity Score (25%) - penalize repos not updated in the last year
  score_activity = 0.0
  if repository_metadata.last_updated:
    try:
      last_updated = datetime.fromisoformat(repository_metadata.last_updated.replace('Z', '+00:00'))
      days_since_updated = (now - last_updated).total_seconds() / (24 * 3600)
      score_activity = max(0, min(100 - (days_since_updated / 365 * 100), 100)) * 0.25
    except (ValueError, AttributeError):
      pass

  # 3. Stars Score (25%) - using log scale since we don't have max reference
  # log10(1000) ≈ 3, so 1000 stars = ~100 score
  score_stars = 0.0
  if repository_metadata.stars > 0:
    score_stars = min(math.log10(repository_metadata.stars + 1) / 3 * 100, 100) * 0.25

  # 4. Forks Score (15%) - using log scale
  # log10(500) ≈ 2.7, so ~500 forks = ~100 score
  score_forks = 0.0
  if repository_metadata.forks > 0:
    score_forks = min(math.log10(repository_metadata.forks + 1) / 2.7 * 100, 100) * 0.15

  # 5. Development History Score (15%) - days since first commit, capped at 4 years
  effective_start_date = created_at
  if repository_metadata.first_commit_date:
    try:
      first_commit = datetime.fromisoformat(repository_metadata.first_commit_date.replace('Z', '+00:00'))
      effective_start_date = first_commit
    except (ValueError, AttributeError):
      pass
  
  days_of_development = (now - effective_start_date).total_seconds() / (24 * 3600)
  score_history = min(days_of_development / 1460 * 100, 100) * 0.15

  # Calculate total score
  total_score = score_age + score_activity + score_stars + score_forks + score_history
  return round(total_score, 2)

if __name__ == "__main__":
  import asyncio
  import os

  async def main():
    access_token = os.getenv("GITHUB_ACCESS_TOKEN", None)
    repository_metadata = await fetch_github_metadata("NASA-IMPACT/veda-config-ghg", access_token)
    print("#" * 50)
    print(repository_metadata.model_dump())
    print(calculate_reliability_score(repository_metadata))
    print("#" * 50)

  asyncio.run(main())
