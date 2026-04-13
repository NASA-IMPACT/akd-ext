"""
Code Signals Search Tool.

Searches LLM-extracted code signals from GitHub repositories.
Use as fallback when README-based search (RepositorySearchTool) is insufficient.
"""

import os
from typing import Any, Literal
from urllib.parse import urljoin

import httpx
from loguru import logger
from pydantic import Field

from akd._base import InputSchema, OutputSchema
from akd.structures import SearchResult
from akd.tools import BaseTool, BaseToolConfig

from akd_ext.mcp import mcp_tool


class CodeSignalsSearchToolConfig(BaseToolConfig):
    """Configuration for the Code Signals Search Tool."""

    sde_base_url: str = Field(
        default=os.getenv("SDE_BASE_URL", "https://dyejsbdumgpqz.cloudfront.net/"),
        description="Base URL for SDE API",
    )
    endpoint: str = Field(
        default="/api/code_signals/search",
        description="Code signals search endpoint",
    )
    timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
    )
    search_type: Literal["hybrid", "vector", "keyword"] = Field(
        default="hybrid",
        description="Search type: 'hybrid' (vector + keyword, recommended), 'vector' (semantic only), 'keyword' (exact matching)",
    )
    debug: bool = Field(default=False, description="Enable debug logging")


class CodeSignalsHit(SearchResult):
    """A single code signals hit from SDE search."""

    repo_id: str | None = Field(None, description="Repository identifier")
    repo_url: str | None = Field(None, description="GitHub repository URL")


class CodeSignalsSearchInputSchema(InputSchema):
    """Input schema for Code Signals search."""

    query: str = Field(..., description="Search query for code functionality")
    limit: int = Field(default=5, ge=1, le=6, description="Maximum results to return")
    page: int = Field(default=1, ge=1, description="Page number for pagination")


class CodeSignalsSearchOutputSchema(OutputSchema):
    """Output schema for Code Signals search."""

    results: list[CodeSignalsHit] = Field(..., description="List of matching code signals")


@mcp_tool
class CodeSignalsSearchTool(BaseTool[CodeSignalsSearchInputSchema, CodeSignalsSearchOutputSchema]):
    """
    Search code repositories using LLM-extracted code signals.

    Use this tool when README-based search is insufficient. Searches through
    extracted function names, class names, imports, data formats, and code summaries.
    """

    input_schema = CodeSignalsSearchInputSchema
    output_schema = CodeSignalsSearchOutputSchema
    config_schema = CodeSignalsSearchToolConfig

    def _extract_summary(self, content: str) -> str:
        """Extract all Code Summary sections."""
        if not content:
            return ""

        summaries = []

        for part in content.split("Code Summary:")[1:]:
            summary = part.split("\n\n")[0].split("===")[0].strip()
            summary = " ".join(summary.split())
            if summary:
                summaries.append(summary)

        return "\n\n".join(summaries) if summaries else content[:1500]

    def _parse_hit(self, doc: dict[str, Any], query: str) -> CodeSignalsHit:
        """Parse a single document from API response."""
        code_signals = doc.get("code_signals") or ""

        return CodeSignalsHit(
            query=query,
            title=doc.get("repo_id") or doc.get("name") or "Unknown",
            content=self._extract_summary(code_signals),
            score=doc.get("score") or doc.get("_score") or 0.0,
            repo_id=doc.get("repo_id"),
            repo_url=doc.get("repo_url"),
        )

    async def _arun(self, params: CodeSignalsSearchInputSchema) -> CodeSignalsSearchOutputSchema:
        """Execute Code Signals search."""
        request_body = {
            "search_term": params.query,
            "search_type": self.config.search_type,
            "page_size": params.limit,
            "page": params.page,
        }

        if self.config.debug:
            logger.debug(f"Code Signals API request: {request_body}")

        url = urljoin(self.config.sde_base_url, self.config.endpoint)

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.post(url, json=request_body)
                response.raise_for_status()
                data = response.json()
            except httpx.TimeoutException as e:
                msg = f"Code Signals API request timed out after {self.config.timeout}s"
                raise TimeoutError(msg) from e
            except httpx.HTTPStatusError as e:
                msg = f"Code Signals API returned error status {e.response.status_code}: {e.response.text}"
                raise RuntimeError(msg) from e
            except Exception as e:
                msg = f"Failed to query Code Signals API: {e}"
                raise RuntimeError(msg) from e

        documents = [self._parse_hit(doc, params.query) for doc in data.get("documents", [])]

        return CodeSignalsSearchOutputSchema(results=documents)
