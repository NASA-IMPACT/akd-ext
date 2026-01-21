"""Tests for the SDE Search Tool."""

import pytest

from akd_ext.structures import SDEIndexedDocumentType, NASASMDDivision
from akd_ext.tools import SDESearchTool, SDESearchToolInputSchema, SDESearchToolConfig


@pytest.mark.integration
async def test_sde_search_basic():
    """Test basic SDE search functionality."""
    tool = SDESearchTool()

    # Perform a simple search
    result = await tool.arun(
        SDESearchToolInputSchema(
            query="climate change",
            limit=5,
        )
    )

    # Verify response structure
    assert result.results is not None
    assert isinstance(result.results, list)
    assert len(result.results) > 0 and len(result.results) <= 5

    # If results are returned, verify document structure

    for doc in result.results:
        assert doc.title is not None
        assert doc.url is not None
        assert doc.content is not None
        assert isinstance(doc.score, float)
        assert doc.query == "climate change"

        print(f"title: {doc.title}")
        print(f"url: {doc.url}")
        print(f"content: {doc.content[:100]}...")  # Print first 100 chars of content
        print(f"score: {doc.score}")


@pytest.mark.integration
async def test_sde_search_with_division_filter():
    """Test SDE search with division filter."""
    config = SDESearchToolConfig(
        division=NASASMDDivision.EARTH_SCIENCE,
    )
    tool = SDESearchTool(config=config)

    result = await tool.arun(
        SDESearchToolInputSchema(
            query="climate change",
            limit=5,
        )
    )

    assert result.results is not None
    for doc in result.results:
        print(f"Document division: {doc.division}")
        assert doc.division == NASASMDDivision.EARTH_SCIENCE.value

    assert len(result.results) <= 5

    # If results exist, optionally verify division
    if result.results:
        print(f"Found {len(result.results)} results for Earth Science division")


@pytest.mark.integration
async def test_sde_search_with_doc_type_filter():
    """Test SDE search with document type filter."""
    tool = SDESearchTool()

    result = await tool.arun(
        SDESearchToolInputSchema(
            query="satellite data",
            limit=5,
            doc_type=SDEIndexedDocumentType.DATA,
        )
    )

    assert result.results is not None
    for doc in result.results:
        print(f"Document type: {doc.doc_type}")
        assert doc.doc_type == SDEIndexedDocumentType.DATA.value
    assert len(result.results) > 0


@pytest.mark.integration
async def test_sde_search_types():
    """Test different search types."""
    config = SDESearchToolConfig(
        search_type="hybrid",
    )
    tool = SDESearchTool(config=config)

    # Test hybrid search
    result_hybrid = await tool.arun(
        SDESearchToolInputSchema(
            query="Mars rover",
            limit=3,
        )
    )
    assert result_hybrid.results is not None
    assert len(result_hybrid.results) > 0


@pytest.mark.integration
async def test_sde_search_obscure_text():
    """Test SDE search that may return no results."""
    tool = SDESearchTool()

    # Use a very specific/obscure query
    result = await tool.arun(
        SDESearchToolInputSchema(
            query="xyzabc123nonexistentquery456",
            limit=5,
        )
    )

    assert result.results is not None
    assert isinstance(result.results, list)
    print(f"Number of results returned: {len(result.results)}")
    print(result.results)


@pytest.mark.integration
async def test_sde_search_limit_parameter():
    """Test that limit parameter is respected."""
    tool = SDESearchTool()

    result = await tool.arun(
        SDESearchToolInputSchema(
            query="NASA",
            limit=3,
        )
    )

    assert result.results is not None
    print(f"Number of results returned: {len(result.results)}")
    assert len(result.results) <= 3
