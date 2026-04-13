"""Functional tests for Repository Search Tool."""

import pytest

from akd_ext.tools.code_search.repository_search import (
    RepositorySearchTool,
    RepositorySearchToolConfig,
    RepositorySearchToolInputSchema,
    RepositorySearchToolOutputSchema,
)


class TestRepositorySearchTool:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "query",
        [
            "indus pipeline code",
            "NASA earth science data processing for universal file format",
        ],
    )
    async def test_repository_search_tool(self, query: str):
        """Test Repository Search Tool functionality.

        Args:
            query: Code search query to test
        """
        config = RepositorySearchToolConfig(page_size=2)
        tool = RepositorySearchTool(config=config)
        result = await tool.arun(RepositorySearchToolInputSchema(queries=[query]))

        assert isinstance(result, RepositorySearchToolOutputSchema)
        assert len(result.results) > 0

        # Verify each result has repository metadata and reliability score
        for item in result.results:
            assert hasattr(item, "repository_metadata")
            assert hasattr(item, "reliability_score")
            assert item.repository_metadata.stars >= 0
            assert item.repository_metadata.forks >= 0

    @pytest.mark.parametrize(
        "page_size,result_size",
        [
            (3, 3),
            (8, 8),
            (10, 10),
            (11, 10),  # Capped at max 10
            (55, 10),  # Capped at max 10
            (100, 10),  # Capped at max 10
        ],
    )
    @pytest.mark.asyncio
    async def test_repository_search_tool_results_number(self, page_size: int, result_size: int):
        """Test Repository Search Tool results number."""
        config = RepositorySearchToolConfig(page_size=page_size)
        tool = RepositorySearchTool(config=config)
        result = await tool.arun(RepositorySearchToolInputSchema(queries=["indus pipeline code"]))
        assert len(result.results) == result_size
