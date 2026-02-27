"""Unit tests for IMG Atlas tools."""

from unittest.mock import AsyncMock, patch

import pytest

from akd_ext.tools.pds.img.search import (
    IMGImageSize,
    IMGProductSummary,
    IMGSearchInputSchema,
    IMGSearchOutputSchema,
    IMGSearchTool,
    IMGSearchToolConfig,
)
from akd_ext.tools.pds.img.count import (
    IMGCountInputSchema,
    IMGCountOutputSchema,
    IMGCountTool,
    IMGCountToolConfig,
)
from akd_ext.tools.pds.img.get_product import (
    IMGGetProductInputSchema,
    IMGGetProductOutputSchema,
    IMGGetProductTool,
    IMGGetProductToolConfig,
    IMGProductDetailURLs,
)
from akd_ext.tools.pds.img.get_facets import (
    IMGFacetValueItem,
    IMGGetFacetsInputSchema,
    IMGGetFacetsOutputSchema,
    IMGGetFacetsTool,
    IMGGetFacetsToolConfig,
)
from akd_ext.tools.pds.utils.img_client import IMGAtlasClientError

# Patch paths – must match where IMGAtlasClient is looked up at runtime
_SEARCH_CLIENT = "akd_ext.tools.pds.img.search.IMGAtlasClient"
_COUNT_CLIENT = "akd_ext.tools.pds.img.count.IMGAtlasClient"
_GET_PRODUCT_CLIENT = "akd_ext.tools.pds.img.get_product.IMGAtlasClient"
_GET_FACETS_CLIENT = "akd_ext.tools.pds.img.get_facets.IMGAtlasClient"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_product(**overrides):
    """Create a mock IMGProduct with sensible defaults."""
    from unittest.mock import MagicMock

    product = MagicMock()
    product.uuid = overrides.get("uuid", "abc-123-def")
    product.target = overrides.get("target", "Mars")
    product.mission_name = overrides.get("mission_name", "MARS SCIENCE LABORATORY")
    product.spacecraft_name = overrides.get("spacecraft_name", "CURIOSITY")
    product.instrument_name = overrides.get("instrument_name", "MASTCAM")
    product.product_type = overrides.get("product_type", "RDR")
    product.start_time = overrides.get("start_time", "2020-01-01T00:00:00Z")
    product.stop_time = overrides.get("stop_time", "2020-01-01T00:01:00Z")
    product.planet_day_number = overrides.get("planet_day_number", 2650)
    product.lines = overrides.get("lines", 1200)
    product.line_samples = overrides.get("line_samples", 1600)
    product.data_url = overrides.get("data_url", "https://example.com/data.img")
    product.label_url = overrides.get("label_url", "https://example.com/data.lbl")
    product.browse_url = overrides.get("browse_url", "https://example.com/browse.jpg")
    product.thumbnail_url = overrides.get("thumbnail_url", "https://example.com/thumb.jpg")
    product.product_id = overrides.get("product_id", "MSL_MASTCAM_001")
    product.pds_standard = overrides.get("pds_standard", "PDS3")
    product.product_creation_time = overrides.get("product_creation_time", "2020-06-01T00:00:00Z")
    product.local_true_solar_time = overrides.get("local_true_solar_time", "12:00:00")
    product.solar_azimuth = overrides.get("solar_azimuth", 180.0)
    product.solar_elevation = overrides.get("solar_elevation", 45.0)
    product.exposure_duration = overrides.get("exposure_duration", 50.0)
    product.compression_ratio = overrides.get("compression_ratio", 8.0)
    product.frame_type = overrides.get("frame_type", "FULL")
    product.center_latitude = overrides.get("center_latitude", -4.5)
    product.center_longitude = overrides.get("center_longitude", 137.4)
    return product


def _make_mock_search_response(**overrides):
    """Create a mock search response."""
    from unittest.mock import MagicMock

    response = MagicMock()
    response.status = overrides.get("status", "success")
    response.num_found = overrides.get("num_found", 1)
    response.start = overrides.get("start", 0)
    response.query_time_ms = overrides.get("query_time_ms", 15)
    response.products = overrides.get("products", [_make_mock_product()])
    response.error = overrides.get("error", None)
    return response


def _make_mock_count_response(**overrides):
    """Create a mock count response."""
    from unittest.mock import MagicMock

    response = MagicMock()
    response.status = overrides.get("status", "success")
    response.count = overrides.get("count", 500)
    response.query_time_ms = overrides.get("query_time_ms", 5)
    response.error = overrides.get("error", None)
    return response


def _make_mock_facet_response(**overrides):
    """Create a mock facet response."""
    from unittest.mock import MagicMock

    facet_value = MagicMock()
    facet_value.value = "Mars"
    facet_value.count = 10000

    response = MagicMock()
    response.status = overrides.get("status", "success")
    response.facet_field = overrides.get("facet_field", "TARGET")
    response.query_time_ms = overrides.get("query_time_ms", 3)
    response.values = overrides.get("values", [facet_value])
    response.error = overrides.get("error", None)
    return response


# ---------------------------------------------------------------------------
# IMGSearchTool
# ---------------------------------------------------------------------------


class TestIMGSearchTool:
    """Tests for IMGSearchTool."""

    async def test_basic_search(self):
        """Basic search returns products."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema())

        assert isinstance(result, IMGSearchOutputSchema)
        assert result.status == "success"
        assert result.num_found == 1
        assert len(result.products) == 1

    async def test_search_with_target_filter(self):
        """Target filter is forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema(target="Mars"))

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["target"] == "Mars"
        assert result.status == "success"

    async def test_search_with_mission_filter(self):
        """Mission filter is forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema(mission="MARS SCIENCE LABORATORY"))

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["mission"] == "MARS SCIENCE LABORATORY"

    async def test_search_with_instrument_filter(self):
        """Instrument filter is forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema(instrument="MASTCAM"))

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["instrument"] == "MASTCAM"

    async def test_search_with_time_range(self):
        """Time range filters are forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = IMGSearchTool()
            await tool.arun(
                IMGSearchInputSchema(
                    start_time="2020-01-01T00:00:00Z",
                    stop_time="2020-12-31T23:59:59Z",
                )
            )

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["start_time"] == "2020-01-01T00:00:00Z"
        assert call_kwargs["stop_time"] == "2020-12-31T23:59:59Z"

    async def test_search_with_sol_range(self):
        """Sol range filters are forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = IMGSearchTool()
            await tool.arun(IMGSearchInputSchema(sol_min=100, sol_max=200))

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["sol_min"] == 100
        assert call_kwargs["sol_max"] == 200

    async def test_search_with_product_type(self):
        """Product type filter is forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = IMGSearchTool()
            await tool.arun(IMGSearchInputSchema(product_type="EDR"))

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["product_type"] == "EDR"

    async def test_search_with_sort(self):
        """Sort parameters are built and forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = IMGSearchTool()
            await tool.arun(IMGSearchInputSchema(sort_by="START_TIME", sort_order="asc"))

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["sort"] == "START_TIME asc"

    async def test_search_pagination(self):
        """Pagination parameters are forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(
                return_value=_make_mock_search_response(num_found=100)
            )

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema(rows=10, start=20))

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["rows"] == 10
        assert call_kwargs["start"] == 20
        assert result.start == 0  # from the response start

    async def test_search_product_fields(self):
        """Product summaries contain expected fields."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema())

        product = result.products[0]
        assert isinstance(product, IMGProductSummary)
        assert product.uuid == "abc-123-def"
        assert product.target == "Mars"
        assert product.mission == "MARS SCIENCE LABORATORY"
        assert product.instrument == "MASTCAM"
        assert product.sol == 2650
        assert product.image_size is not None
        assert isinstance(product.image_size, IMGImageSize)
        assert product.image_size.lines == 1200
        assert product.image_size.samples == 1600

    async def test_search_empty_results(self):
        """Empty search results return num_found=0 and empty products list."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(
                return_value=_make_mock_search_response(num_found=0, products=[])
            )

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema())

        assert result.status == "success"
        assert result.num_found == 0
        assert result.products == []

    async def test_search_error_response(self):
        """Error response from API returns error status."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(
                return_value=_make_mock_search_response(status="error", error="Bad request", products=[])
            )

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema())

        assert result.status == "error"
        assert result.error == "Bad request"

    async def test_search_client_error_returns_error_status(self):
        """IMGAtlasClientError returns error status (not raised)."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(side_effect=IMGAtlasClientError("connection failed"))

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema())

        assert result.status == "error"
        assert "connection failed" in result.error

    async def test_search_unexpected_error_returns_error_status(self):
        """Unexpected exceptions return error status (not raised)."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(side_effect=TypeError("bad type"))

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema())

        assert result.status == "error"
        assert "Internal error" in result.error

    async def test_search_product_without_image_size(self):
        """Product with None lines/samples has None image_size."""
        product = _make_mock_product(lines=None, line_samples=None)
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(
                return_value=_make_mock_search_response(products=[product])
            )

            tool = IMGSearchTool()
            result = await tool.arun(IMGSearchInputSchema())

        assert result.products[0].image_size is None

    async def test_search_all_filters_combined(self):
        """All filters combined are forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = IMGSearchTool()
            await tool.arun(
                IMGSearchInputSchema(
                    target="Mars",
                    mission="MARS SCIENCE LABORATORY",
                    instrument="MASTCAM",
                    spacecraft="CURIOSITY",
                    start_time="2020-01-01T00:00:00Z",
                    stop_time="2020-12-31T23:59:59Z",
                    sol_min=100,
                    sol_max=200,
                    product_type="RDR",
                    filter_name="L0",
                    frame_type="FULL",
                    exposure_min=10.0,
                    exposure_max=100.0,
                    local_solar_time="12:00",
                    sort_by="START_TIME",
                    sort_order="asc",
                    rows=50,
                    start=10,
                )
            )

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["target"] == "Mars"
        assert call_kwargs["mission"] == "MARS SCIENCE LABORATORY"
        assert call_kwargs["instrument"] == "MASTCAM"
        assert call_kwargs["spacecraft"] == "CURIOSITY"
        assert call_kwargs["product_type"] == "RDR"
        assert call_kwargs["filter_name"] == "L0"
        assert call_kwargs["frame_type"] == "FULL"
        assert call_kwargs["sol_min"] == 100
        assert call_kwargs["sol_max"] == 200
        assert call_kwargs["rows"] == 50

    async def test_search_with_config(self):
        """Custom config is used for the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            config = IMGSearchToolConfig(base_url="https://custom.url/", timeout=60.0)
            tool = IMGSearchTool(config=config)
            await tool.arun(IMGSearchInputSchema())

        MockClient.assert_called_once_with(
            base_url="https://custom.url/",
            timeout=60.0,
            max_retries=3,
            retry_delay=1.0,
        )


# ---------------------------------------------------------------------------
# IMGCountTool
# ---------------------------------------------------------------------------


class TestIMGCountTool:
    """Tests for IMGCountTool."""

    async def test_basic_count(self):
        """Count returns total matching products."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(return_value=_make_mock_count_response())

            tool = IMGCountTool()
            result = await tool.arun(IMGCountInputSchema())

        assert isinstance(result, IMGCountOutputSchema)
        assert result.status == "success"
        assert result.count == 500

    async def test_count_with_target_filter(self):
        """Target filter is forwarded and reflected in filters."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(return_value=_make_mock_count_response())

            tool = IMGCountTool()
            result = await tool.arun(IMGCountInputSchema(target="Mars"))

        assert result.filters["target"] == "Mars"

    async def test_count_with_mission_and_instrument(self):
        """Multiple filters are forwarded."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(return_value=_make_mock_count_response(count=1500))

            tool = IMGCountTool()
            result = await tool.arun(
                IMGCountInputSchema(mission="MARS SCIENCE LABORATORY", instrument="MASTCAM")
            )

        call_kwargs = mock_client.count_products.call_args.kwargs
        assert call_kwargs["mission"] == "MARS SCIENCE LABORATORY"
        assert call_kwargs["instrument"] == "MASTCAM"
        assert result.count == 1500

    async def test_count_error_response(self):
        """Error response from API returns error status."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(
                return_value=_make_mock_count_response(status="error", error="Invalid query", count=0)
            )

            tool = IMGCountTool()
            result = await tool.arun(IMGCountInputSchema())

        assert result.status == "error"
        assert result.count == 0

    async def test_count_client_error_returns_error_status(self):
        """IMGAtlasClientError returns error status."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(side_effect=IMGAtlasClientError("timeout"))

            tool = IMGCountTool()
            result = await tool.arun(IMGCountInputSchema())

        assert result.status == "error"
        assert "timeout" in result.error

    async def test_count_unexpected_error(self):
        """Unexpected exceptions return error status."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(side_effect=ValueError("bad"))

            tool = IMGCountTool()
            result = await tool.arun(IMGCountInputSchema())

        assert result.status == "error"
        assert "Internal error" in result.error


# ---------------------------------------------------------------------------
# IMGGetProductTool
# ---------------------------------------------------------------------------


class TestIMGGetProductTool:
    """Tests for IMGGetProductTool."""

    async def test_get_product_found(self):
        """Existing product returns success with full metadata."""
        product = _make_mock_product()
        with patch(_GET_PRODUCT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_product = AsyncMock(
                return_value=_make_mock_search_response(products=[product])
            )

            tool = IMGGetProductTool()
            result = await tool.arun(IMGGetProductInputSchema(product_id="abc-123-def"))

        assert isinstance(result, IMGGetProductOutputSchema)
        assert result.status == "success"
        assert result.uuid == "abc-123-def"
        assert result.target == "Mars"
        assert result.mission == "MARS SCIENCE LABORATORY"
        assert result.instrument == "MASTCAM"
        assert result.sol == 2650
        assert result.urls is not None
        assert isinstance(result.urls, IMGProductDetailURLs)
        assert result.urls.data == "https://example.com/data.img"

    async def test_get_product_not_found(self):
        """Non-existent product returns not_found status."""
        with patch(_GET_PRODUCT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_product = AsyncMock(
                return_value=_make_mock_search_response(products=[])
            )

            tool = IMGGetProductTool()
            result = await tool.arun(IMGGetProductInputSchema(product_id="nonexistent"))

        assert result.status == "not_found"
        assert "nonexistent" in result.message

    async def test_get_product_error_response(self):
        """Error response from API returns error status."""
        with patch(_GET_PRODUCT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_product = AsyncMock(
                return_value=_make_mock_search_response(status="error", error="server error", products=[])
            )

            tool = IMGGetProductTool()
            result = await tool.arun(IMGGetProductInputSchema(product_id="any"))

        assert result.status == "error"
        assert result.error == "server error"

    async def test_get_product_client_error(self):
        """IMGAtlasClientError returns error status."""
        with patch(_GET_PRODUCT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_product = AsyncMock(side_effect=IMGAtlasClientError("connection error"))

            tool = IMGGetProductTool()
            result = await tool.arun(IMGGetProductInputSchema(product_id="any"))

        assert result.status == "error"
        assert "connection error" in result.error

    async def test_get_product_full_metadata(self):
        """Product response includes all metadata fields."""
        product = _make_mock_product()
        with patch(_GET_PRODUCT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_product = AsyncMock(
                return_value=_make_mock_search_response(products=[product])
            )

            tool = IMGGetProductTool()
            result = await tool.arun(IMGGetProductInputSchema(product_id="abc-123-def"))

        assert result.product_id == "MSL_MASTCAM_001"
        assert result.pds_standard == "PDS3"
        assert result.spacecraft == "CURIOSITY"
        assert result.local_solar_time == "12:00:00"
        assert result.solar_azimuth == 180.0
        assert result.solar_elevation == 45.0
        assert result.exposure_duration_ms == 50.0
        assert result.compression_ratio == 8.0
        assert result.frame_type == "FULL"
        assert result.center_latitude == -4.5
        assert result.center_longitude == 137.4


# ---------------------------------------------------------------------------
# IMGGetFacetsTool
# ---------------------------------------------------------------------------


class TestIMGGetFacetsTool:
    """Tests for IMGGetFacetsTool."""

    async def test_get_facets_target(self):
        """Get TARGET facet values returns targets with counts."""
        with patch(_GET_FACETS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_facets = AsyncMock(return_value=_make_mock_facet_response())

            tool = IMGGetFacetsTool()
            result = await tool.arun(IMGGetFacetsInputSchema(facet_field="TARGET"))

        assert isinstance(result, IMGGetFacetsOutputSchema)
        assert result.status == "success"
        assert result.facet_field == "TARGET"
        assert result.count == 1
        assert len(result.values) == 1
        assert isinstance(result.values[0], IMGFacetValueItem)
        assert result.values[0].value == "Mars"
        assert result.values[0].count == 10000

    async def test_get_facets_with_target_filter(self):
        """Target filter narrows facet results."""
        with patch(_GET_FACETS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_facets = AsyncMock(return_value=_make_mock_facet_response())

            tool = IMGGetFacetsTool()
            await tool.arun(
                IMGGetFacetsInputSchema(facet_field="ATLAS_INSTRUMENT_NAME", target="Mars")
            )

        call_kwargs = mock_client.get_facets.call_args.kwargs
        assert call_kwargs["target"] == "Mars"
        assert call_kwargs["facet_field"] == "ATLAS_INSTRUMENT_NAME"

    async def test_get_facets_with_limit(self):
        """Limit parameter is forwarded."""
        with patch(_GET_FACETS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_facets = AsyncMock(return_value=_make_mock_facet_response())

            tool = IMGGetFacetsTool()
            await tool.arun(IMGGetFacetsInputSchema(facet_field="TARGET", limit=5))

        call_kwargs = mock_client.get_facets.call_args.kwargs
        assert call_kwargs["limit"] == 5

    async def test_get_facets_error_response(self):
        """Error response from API returns error status."""
        with patch(_GET_FACETS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_facets = AsyncMock(
                return_value=_make_mock_facet_response(status="error", error="bad field", values=[])
            )

            tool = IMGGetFacetsTool()
            result = await tool.arun(IMGGetFacetsInputSchema(facet_field="TARGET"))

        assert result.status == "error"
        assert result.count == 0

    async def test_get_facets_client_error(self):
        """IMGAtlasClientError returns error status."""
        with patch(_GET_FACETS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_facets = AsyncMock(side_effect=IMGAtlasClientError("timeout"))

            tool = IMGGetFacetsTool()
            result = await tool.arun(IMGGetFacetsInputSchema(facet_field="TARGET"))

        assert result.status == "error"
        assert "timeout" in result.error


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestIMGSchemaValidation:
    """Tests for IMG input schema validation."""

    def test_search_input_defaults(self):
        """SearchInputSchema has correct defaults."""
        schema = IMGSearchInputSchema()
        assert schema.target is None
        assert schema.mission is None
        assert schema.instrument is None
        assert schema.rows == 100
        assert schema.start == 0
        assert schema.sort_order == "desc"

    def test_search_input_invalid_target(self):
        """Invalid target raises validation error."""
        with pytest.raises(Exception):
            IMGSearchInputSchema(target="InvalidPlanet")

    def test_search_input_invalid_mission(self):
        """Invalid mission raises validation error."""
        with pytest.raises(Exception):
            IMGSearchInputSchema(mission="INVALID MISSION")

    def test_search_input_invalid_instrument(self):
        """Invalid instrument raises validation error."""
        with pytest.raises(Exception):
            IMGSearchInputSchema(instrument="INVALID_INSTRUMENT")

    def test_search_input_rows_bounds(self):
        """Rows must be between 1 and 1000."""
        with pytest.raises(Exception):
            IMGSearchInputSchema(rows=0)
        with pytest.raises(Exception):
            IMGSearchInputSchema(rows=1001)

    def test_count_input_defaults(self):
        """CountInputSchema has correct defaults."""
        schema = IMGCountInputSchema()
        assert schema.target is None
        assert schema.mission is None

    def test_get_product_input_requires_id(self):
        """GetProductInputSchema requires product_id."""
        with pytest.raises(Exception):
            IMGGetProductInputSchema()

    def test_get_facets_input_requires_field(self):
        """GetFacetsInputSchema requires facet_field."""
        with pytest.raises(Exception):
            IMGGetFacetsInputSchema()

    def test_get_facets_input_defaults(self):
        """GetFacetsInputSchema has correct defaults."""
        schema = IMGGetFacetsInputSchema(facet_field="TARGET")
        assert schema.limit == 100
        assert schema.target is None
        assert schema.mission is None
