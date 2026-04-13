"""Tests for the SDE Search Tool."""

import pytest
import httpx
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


@pytest.mark.integration
async def test_sde_search_url_validation():
    """Test that URL validation filters out 404s and other inaccessible URLs."""
    # Enable URL validation
    config = SDESearchToolConfig(
        validate_urls=True,
        url_check_timeout=10.0,  # Longer timeout for this test
    )
    tool = SDESearchTool(config=config)

    result = await tool.arun(
        SDESearchToolInputSchema(
            query="Mars rover",
            limit=20,  # Request more results to increase chance of finding valid URLs
        )
    )

    assert result.results is not None
    print(f"Number of results after URL validation: {len(result.results)}")

    # Verify all returned URLs are accessible (no 404s)

    for doc in result.results:
        assert doc.url, f"Document '{doc.title}' has empty URL"
        print(f"Checking URL: {doc.url}")

        # Verify the URL is accessible
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                response = await client.head(doc.url)
                print(f"  Status: {response.status_code}")
                # All returned documents should have status < 400
                assert response.status_code < 400, f"URL {doc.url} returned status {response.status_code}"
            except httpx.HTTPError as e:
                pytest.fail(f"URL {doc.url} failed validation but was not filtered: {e}")

    # Verify extra metadata includes filtered_count
    # filtered_count is the number of results after URL validation AND truncation to limit
    assert result.extra is not None
    assert "filtered_count" in result.extra
    assert result.extra["filtered_count"] == len(result.results)
    print(f"Total count from API: {result.extra.get('total_count')}")
    print(f"Filtered count (after validation & truncation): {result.extra.get('filtered_count')}")


@pytest.mark.integration
async def test_sde_search_url_validation_disabled():
    """Test that URL validation can be disabled."""
    # Disable URL validation
    config = SDESearchToolConfig(
        validate_urls=False,
    )
    tool = SDESearchTool(config=config)

    result = await tool.arun(
        SDESearchToolInputSchema(
            query="climate change",
            limit=5,
        )
    )

    assert result.results is not None
    # When validation is disabled, filtered_count should be None (no filtering/truncation tracking)
    assert result.extra is not None
    assert result.extra.get("filtered_count") is None


@pytest.mark.integration
async def test_sde_search_result_multiplier():
    """Test that result_multiplier fetches more results for filtering."""
    # Use a higher multiplier to fetch more results
    config = SDESearchToolConfig(
        validate_urls=True,
        result_multiplier=3.0,
        url_check_timeout=10.0,
    )
    tool = SDESearchTool(config=config)

    limit = 5
    result = await tool.arun(
        SDESearchToolInputSchema(
            query="Mars",
            limit=limit,
        )
    )

    assert result.results is not None
    assert result.extra is not None

    # Verify metadata
    assert result.extra.get("requested_limit") == limit
    assert result.extra.get("filtered_count") is not None

    # filtered_count should equal len(results) since it's the count after truncation to limit
    assert result.extra.get("filtered_count") == len(result.results)

    # Results should not exceed requested limit
    assert len(result.results) <= limit

    print(f"Requested limit: {limit}")
    print(f"Final result count: {len(result.results)}")
    print(f"Filtered count (after validation & truncation): {result.extra.get('filtered_count')}")
    print(f"Total from API: {result.extra.get('total_count')}")


@pytest.mark.integration
async def test_sde_search_result_multiplier_respects_api_max():
    """Test that result_multiplier respects the API maximum of 100."""
    # Set a high multiplier that would exceed 100
    config = SDESearchToolConfig(
        validate_urls=True,
        result_multiplier=10.0,  # Max allowed
        url_check_timeout=10.0,
    )
    tool = SDESearchTool(config=config)

    # Request 20 results, which with 10x multiplier would be 200, but should cap at 100
    limit = 20
    result = await tool.arun(
        SDESearchToolInputSchema(
            query="NASA",
            limit=limit,
        )
    )

    assert result.results is not None
    assert len(result.results) <= limit

    # The tool should have fetched at most 100 from the API (not 200)
    # filtered_count is the number of results after validation AND truncation to the requested limit
    if result.extra and result.extra.get("filtered_count"):
        # Since we requested 20 results, filtered_count should equal min(validated_results, 20)
        assert result.extra.get("filtered_count") == len(result.results)
        assert result.extra.get("filtered_count") <= limit
        print(f"Filtered count (after validation & truncation): {result.extra.get('filtered_count')}")
        print(f"Requested limit: {limit}")
        print(f"Result count: {len(result.results)}")


@pytest.mark.integration
async def test_sde_search_result_multiplier_disabled():
    """Test that result_multiplier is not used when validation is disabled."""
    # Disable URL validation - multiplier should not apply
    config = SDESearchToolConfig(
        validate_urls=False,
        result_multiplier=5.0,
    )
    tool = SDESearchTool(config=config)

    limit = 10
    result = await tool.arun(
        SDESearchToolInputSchema(
            query="climate change",
            limit=limit,
        )
    )

    assert result.results is not None
    # When validation is disabled, should fetch exactly the limit (not limit * multiplier)
    # filtered_count should be None since validation is disabled
    assert result.extra is not None
    assert result.extra.get("filtered_count") is None
    assert result.extra.get("requested_limit") == limit
    # Results should equal the requested limit (no over-fetching when validation is off)
    assert len(result.results) <= limit
