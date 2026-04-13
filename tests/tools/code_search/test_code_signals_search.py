"""Tests for Code Signals Search Tool."""

import pytest

from akd_ext.tools.code_search.code_signals import (
    CodeSignalsSearchTool,
    CodeSignalsSearchToolConfig,
    CodeSignalsSearchInputSchema,
    CodeSignalsSearchOutputSchema,
)


class TestCodeSignalsSearchTool:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "query",
        [
            "MODIS",
            "earth science data processing",
        ],
    )
    async def test_code_signals_search_basic(self, query: str):
        """Test Code Signals Search Tool returns results for a query.

        Args:
            query: Code search query to test
        """
        config = CodeSignalsSearchToolConfig()
        tool = CodeSignalsSearchTool(config=config)
        result = await tool.arun(CodeSignalsSearchInputSchema(query=query, limit=5))

        assert isinstance(result, CodeSignalsSearchOutputSchema)
        assert len(result.results) <= 5

        for hit in result.results:
            assert hasattr(hit, "query")
            assert hasattr(hit, "score")
            assert hit.query == query

    @pytest.mark.asyncio
    async def test_code_signals_search_pagination(self):
        """Test Code Signals Search Tool pagination."""
        config = CodeSignalsSearchToolConfig()
        tool = CodeSignalsSearchTool(config=config)

        page1 = await tool.arun(
            CodeSignalsSearchInputSchema(query="MODIS", limit=3, page=1),
        )
        page2 = await tool.arun(
            CodeSignalsSearchInputSchema(query="MODIS", limit=3, page=2),
        )

        assert isinstance(page1, CodeSignalsSearchOutputSchema)
        assert isinstance(page2, CodeSignalsSearchOutputSchema)
        assert len(page1.results) <= 3
        assert len(page2.results) <= 3

        if page1.results and page2.results:
            keys1 = {(h.title, h.repo_id) for h in page1.results}
            keys2 = {(h.title, h.repo_id) for h in page2.results}
            assert keys1.isdisjoint(keys2), "Page 1 and page 2 should not overlap"

    @pytest.mark.parametrize(
        "limit,expected_max",
        [
            (1, 1),
            (5, 5),
            (6, 6),
        ],
    )
    @pytest.mark.asyncio
    async def test_code_signals_search_limit(self, limit: int, expected_max: int):
        """Test Code Signals Search Tool respects limit parameter."""
        config = CodeSignalsSearchToolConfig()
        tool = CodeSignalsSearchTool(config=config)
        result = await tool.arun(
            CodeSignalsSearchInputSchema(query="MODIS", limit=limit, page=1),
        )
        assert len(result.results) <= expected_max
