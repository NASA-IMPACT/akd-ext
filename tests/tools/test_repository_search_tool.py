"""Functional tests for Repository Search Tool."""

import pytest

from akd_ext.tools.repository_search_tool import (
    RepositorySearchTool,
    RepositorySearchToolConfig,
    RepositorySearchToolInputSchema,
    RepositorySearchToolOutputSchema,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "indus pipeline code",
        "NASA earth science data processing for universal file format",
    ],
)
async def test_repository_search_tool(query: str):
    """Test Repository Search Tool functionality.

    Args:
        query: Code search query to test
    """
    config = RepositorySearchToolConfig(page_size=2)
    tool = RepositorySearchTool(config=config)
    result = await tool._arun(RepositorySearchToolInputSchema(queries=[query]))

    assert isinstance(result, RepositorySearchToolOutputSchema)
    assert len(result.results) > 0
    
    # Verify each result has repository metadata and reliability score
    for item in result.results:
        assert hasattr(item, 'repository_metadata')
        assert hasattr(item, 'reliability_score')
        assert item.reliability_score >= 0.0
        assert item.repository_metadata.stars >= 0
        assert item.repository_metadata.forks >= 0
