"""Unit tests for ODE (Orbital Data Explorer) tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from akd_ext.tools.pds.ode.search_products import (
    ODESearchProductsInputSchema,
    ODESearchProductsOutputSchema,
    ODESearchProductsTool,
    ODESearchProductsToolConfig,
)
from akd_ext.tools.pds.ode.count_products import (
    ODECountProductsInputSchema,
    ODECountProductsOutputSchema,
    ODECountProductsTool,
    ODECountProductsToolConfig,
)
from akd_ext.tools.pds.ode.list_instruments import (
    ODEInstrumentSummary,
    ODEListInstrumentsInputSchema,
    ODEListInstrumentsOutputSchema,
    ODEListInstrumentsTool,
    ODEListInstrumentsToolConfig,
)
from akd_ext.tools.pds.ode.list_feature_classes import (
    ODEListFeatureClassesInputSchema,
    ODEListFeatureClassesOutputSchema,
    ODEListFeatureClassesTool,
    ODEListFeatureClassesToolConfig,
)
from akd_ext.tools.pds.ode.list_feature_names import (
    ODEListFeatureNamesInputSchema,
    ODEListFeatureNamesOutputSchema,
    ODEListFeatureNamesTool,
    ODEListFeatureNamesToolConfig,
)
from akd_ext.tools.pds.ode.get_feature_bounds import (
    ODEGetFeatureBoundsInputSchema,
    ODEGetFeatureBoundsOutputSchema,
    ODEGetFeatureBoundsTool,
    ODEGetFeatureBoundsToolConfig,
)
from akd_ext.tools.pds.utils.ode_client import ODEClientError

# Patch paths – must match where ODEClient is looked up at runtime
_SEARCH_CLIENT = "akd_ext.tools.pds.ode.search_products.ODEClient"
_COUNT_CLIENT = "akd_ext.tools.pds.ode.count_products.ODEClient"
_LIST_INSTRUMENTS_CLIENT = "akd_ext.tools.pds.ode.list_instruments.ODEClient"
_LIST_FEATURE_CLASSES_CLIENT = "akd_ext.tools.pds.ode.list_feature_classes.ODEClient"
_LIST_FEATURE_NAMES_CLIENT = "akd_ext.tools.pds.ode.list_feature_names.ODEClient"
_GET_FEATURE_BOUNDS_CLIENT = "akd_ext.tools.pds.ode.get_feature_bounds.ODEClient"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_product_file(**overrides):
    """Create a mock ODEProductFile with sensible defaults."""
    f = MagicMock()
    f.file_name = overrides.get("file_name", "product.img")
    f.url = overrides.get("url", "https://ode.example.com/product.img")
    f.file_type = overrides.get("file_type", "Product")
    f.kbytes = overrides.get("kbytes", "1024")
    return f


def _make_mock_product(**overrides):
    """Create a mock ODEProduct with sensible defaults."""
    product = MagicMock()
    product.pdsid = overrides.get("pdsid", "ESP_012600_1655_RED")
    product.ode_id = overrides.get("ode_id", "12345")
    product.data_set_id = overrides.get("data_set_id", "MRO-M-HIRISE-3-RDR-V1.1")
    product.ihid = overrides.get("ihid", "MRO")
    product.iid = overrides.get("iid", "HIRISE")
    product.pt = overrides.get("pt", "RDRV11")
    product.center_latitude = overrides.get("center_latitude", -14.5)
    product.center_longitude = overrides.get("center_longitude", 175.5)
    product.observation_time = overrides.get("observation_time", "2009-04-06T12:00:00")
    product.minimum_latitude = overrides.get("minimum_latitude", -14.8)
    product.maximum_latitude = overrides.get("maximum_latitude", -14.2)
    product.westernmost_longitude = overrides.get("westernmost_longitude", 175.2)
    product.easternmost_longitude = overrides.get("easternmost_longitude", 175.8)
    product.emission_angle = overrides.get("emission_angle", 2.5)
    product.incidence_angle = overrides.get("incidence_angle", 55.0)
    product.phase_angle = overrides.get("phase_angle", 57.5)
    product.map_scale = overrides.get("map_scale", 0.25)
    product.label_url = overrides.get("label_url", "https://ode.example.com/label.lbl")
    product.product_files = overrides.get("product_files", [_make_mock_product_file()])
    return product


def _make_mock_search_response(**overrides):
    """Create a mock ODEProductSearchResponse."""
    response = MagicMock()
    response.status = overrides.get("status", "OK")
    response.count = overrides.get("count", 1)
    response.products = overrides.get("products", [_make_mock_product()])
    response.error = overrides.get("error", None)
    return response


def _make_mock_count_response(**overrides):
    """Create a mock ODEProductCountResponse."""
    response = MagicMock()
    response.status = overrides.get("status", "OK")
    response.count = overrides.get("count", 42)
    response.error = overrides.get("error", None)
    return response


def _make_mock_instrument_info(**overrides):
    """Create a mock ODEInstrumentInfo."""
    inst = MagicMock()
    inst.ihid = overrides.get("ihid", "MRO")
    inst.instrument_host_name = overrides.get("instrument_host_name", "Mars Reconnaissance Orbiter")
    inst.iid = overrides.get("iid", "HIRISE")
    inst.instrument_name = overrides.get("instrument_name", "High Resolution Imaging Science Experiment")
    inst.pt = overrides.get("pt", "RDRV11")
    inst.pt_name = overrides.get("pt_name", "RDR V1.1")
    inst.number_products = overrides.get("number_products", 50000)
    return inst


def _make_mock_instruments_response(**overrides):
    """Create a mock ODEIIPTResponse."""
    response = MagicMock()
    response.status = overrides.get("status", "OK")
    response.instruments = overrides.get("instruments", [_make_mock_instrument_info()])
    response.error = overrides.get("error", None)
    return response


def _make_mock_feature_classes_response(**overrides):
    """Create a mock ODEFeatureClassesResponse."""
    response = MagicMock()
    response.status = overrides.get("status", "OK")
    response.feature_classes = overrides.get("feature_classes", ["crater", "chasma", "mons", "vallis"])
    response.error = overrides.get("error", None)
    return response


def _make_mock_feature_names_response(**overrides):
    """Create a mock ODEFeatureNamesResponse."""
    response = MagicMock()
    response.status = overrides.get("status", "OK")
    response.feature_names = overrides.get("feature_names", ["Gale", "Jezero", "Holden"])
    response.error = overrides.get("error", None)
    return response


def _make_mock_feature(**overrides):
    """Create a mock ODEFeature."""
    feature = MagicMock()
    feature.feature_class = overrides.get("feature_class", "crater")
    feature.feature_name = overrides.get("feature_name", "Gale")
    feature.min_lat = overrides.get("min_lat", -6.0)
    feature.max_lat = overrides.get("max_lat", -3.5)
    feature.west_lon = overrides.get("west_lon", 136.5)
    feature.east_lon = overrides.get("east_lon", 138.5)
    return feature


def _make_mock_feature_data_response(**overrides):
    """Create a mock ODEFeatureDataResponse."""
    response = MagicMock()
    response.status = overrides.get("status", "OK")
    response.features = overrides.get("features", [_make_mock_feature()])
    response.error = overrides.get("error", None)
    return response


def _patch_ode_client(patch_target, mock_client):
    """Set up the patch for an ODE client async context manager.

    Returns:
        The patcher context manager result (MockClient).
    """
    patcher = patch(patch_target)
    MockClient = patcher.start()
    MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
    return MockClient, patcher


# ---------------------------------------------------------------------------
# ODESearchProductsTool
# ---------------------------------------------------------------------------


class TestODESearchProductsTool:
    """Tests for ODESearchProductsTool."""

    async def test_basic_search(self):
        """Basic search with required target returns products."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        assert isinstance(result, ODESearchProductsOutputSchema)
        assert result.status == "success"
        assert result.target == "mars"
        assert result.count == 1
        assert result.total_available == 1
        assert len(result.products) == 1

    async def test_search_product_fields(self):
        """Product summaries contain expected fields."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        product = result.products[0]
        assert product.pdsid == "ESP_012600_1655_RED"
        assert product.ode_id == "12345"
        assert product.data_set_id == "MRO-M-HIRISE-3-RDR-V1.1"
        assert product.instrument_host == "MRO"
        assert product.instrument == "HIRISE"
        assert product.product_type == "RDRV11"
        assert product.center_latitude == -14.5
        assert product.center_longitude == 175.5
        assert product.observation_time == "2009-04-06T12:00:00"
        assert product.min_latitude == -14.8
        assert product.max_latitude == -14.2
        assert product.west_longitude == 175.2
        assert product.east_longitude == 175.8
        assert product.emission_angle == 2.5
        assert product.incidence_angle == 55.0
        assert product.phase_angle == 57.5
        assert product.map_scale == 0.25
        assert product.label_url == "https://ode.example.com/label.lbl"

    async def test_search_product_files(self):
        """Product files are included in summary."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        product = result.products[0]
        assert len(product.files) == 1
        assert product.files[0].name == "product.img"
        assert product.files[0].url == "https://ode.example.com/product.img"
        assert product.files[0].type == "Product"
        assert product.files[0].size_kb == "1024"

    async def test_search_files_truncated(self):
        """Products with more than MAX_FILES_PER_PRODUCT files are truncated."""
        files = [_make_mock_product_file(file_name=f"file_{i}.img") for i in range(5)]
        product = _make_mock_product(product_files=files)
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(
                return_value=_make_mock_search_response(products=[product])
            )

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        p = result.products[0]
        assert len(p.files) == 3  # MAX_FILES_PER_PRODUCT
        assert p.files_truncated is True
        assert p.total_files == 5

    async def test_search_with_pdsid(self):
        """Search by PDS ID forwards pdsid to client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(target="mars", pdsid="ESP_012600_1655_RED")
            )

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["pdsid"] == "ESP_012600_1655_RED"
        assert result.status == "success"

    async def test_search_with_latlon_bounds(self):
        """Lat/lon bounds are forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = ODESearchProductsTool()
            await tool.arun(
                ODESearchProductsInputSchema(
                    target="mars",
                    ihid="MRO",
                    iid="HIRISE",
                    pt="RDRV11",
                    minlat=-15.0,
                    maxlat=-14.0,
                    westlon=175.0,
                    eastlon=176.0,
                )
            )

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["minlat"] == -15.0
        assert call_kwargs["maxlat"] == -14.0
        assert call_kwargs["westlon"] == 175.0
        assert call_kwargs["eastlon"] == 176.0

    async def test_search_with_time_bounds(self):
        """Observation time bounds are forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = ODESearchProductsTool()
            await tool.arun(
                ODESearchProductsInputSchema(
                    target="mars",
                    ihid="MRO",
                    iid="HIRISE",
                    pt="RDRV11",
                    minobtime="2018-05-01",
                    maxobtime="2018-08-31",
                )
            )

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["minobtime"] == "2018-05-01"
        assert call_kwargs["maxobtime"] == "2018-08-31"

    async def test_search_all_filters_combined(self):
        """All filters combined are forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(
                    target="mars",
                    ihid="MRO",
                    iid="HIRISE",
                    pt="RDRV11",
                    minlat=-15.0,
                    maxlat=-14.0,
                    westlon=175.0,
                    eastlon=176.0,
                    minobtime="2018-05-01",
                    maxobtime="2018-08-31",
                    limit=5,
                    offset=10,
                )
            )

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["target"] == "mars"
        assert call_kwargs["ihid"] == "MRO"
        assert call_kwargs["iid"] == "HIRISE"
        assert call_kwargs["pt"] == "RDRV11"
        assert call_kwargs["minlat"] == -15.0
        assert call_kwargs["maxlat"] == -14.0
        assert call_kwargs["westlon"] == 175.0
        assert call_kwargs["eastlon"] == 176.0
        assert call_kwargs["minobtime"] == "2018-05-01"
        assert call_kwargs["maxobtime"] == "2018-08-31"
        assert call_kwargs["limit"] == 5
        assert call_kwargs["offset"] == 10
        assert result.status == "success"

    async def test_search_pagination_has_more(self):
        """has_more is True when more products are available."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            # 1 product returned but 50 total available
            mock_client.search_products = AsyncMock(
                return_value=_make_mock_search_response(count=50, products=[_make_mock_product()])
            )

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", limit=1, offset=0)
            )

        assert result.count == 1
        assert result.total_available == 50
        assert result.offset == 0
        assert result.has_more is True

    async def test_search_pagination_no_more(self):
        """has_more is False when all results are returned."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(
                return_value=_make_mock_search_response(count=1, products=[_make_mock_product()])
            )

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", limit=10, offset=0)
            )

        assert result.has_more is False

    async def test_search_pagination_with_offset(self):
        """Offset is correctly used in has_more computation."""
        products = [_make_mock_product(), _make_mock_product(pdsid="PSP_001234_1234_RED")]
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(
                return_value=_make_mock_search_response(count=5, products=products)
            )

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", limit=2, offset=2)
            )

        assert result.count == 2
        assert result.total_available == 5
        assert result.offset == 2
        assert result.has_more is True  # offset(2) + count(2) = 4 < 5

    async def test_search_limit_capped_at_max(self):
        """Limit is capped at MAX_SEARCH_LIMIT (10)."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = ODESearchProductsTool()
            # Schema allows max 10, so test with exactly 10
            await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", limit=10)
            )

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["limit"] == 10

    async def test_search_empty_results(self):
        """Empty search results return count=0 and empty products list."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(
                return_value=_make_mock_search_response(count=0, products=[])
            )

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        assert result.status == "success"
        assert result.count == 0
        assert result.total_available == 0
        assert result.products == []
        assert result.has_more is False

    async def test_search_api_error_returns_error_schema(self):
        """API error response (status=ERROR) returns error output schema."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(
                return_value=_make_mock_search_response(status="ERROR", error="Invalid query parameters", products=[])
            )

            tool = ODESearchProductsTool()
            result = await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        assert result.status == "error"
        assert result.error == "Invalid query parameters"
        assert result.count == 0
        assert result.total_available == 0
        assert result.has_more is False

    async def test_search_client_error_raises(self):
        """ODEClientError is re-raised."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(side_effect=ODEClientError("connection failed"))

            tool = ODESearchProductsTool()
            with pytest.raises(ODEClientError, match="connection failed"):
                await tool.arun(
                    ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
                )

    async def test_search_value_error_raises(self):
        """ValueError is re-raised."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(side_effect=ValueError("bad param"))

            tool = ODESearchProductsTool()
            with pytest.raises(ValueError, match="bad param"):
                await tool.arun(
                    ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
                )

    async def test_search_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(side_effect=TypeError("bad type"))

            tool = ODESearchProductsTool()
            with pytest.raises(RuntimeError, match="Internal error during product search"):
                await tool.arun(
                    ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
                )

    async def test_search_with_config(self):
        """Custom config values are passed to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            config = ODESearchProductsToolConfig(
                base_url="https://custom.ode.example.com/", timeout=60.0, max_retries=5
            )
            tool = ODESearchProductsTool(config=config)
            await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        MockClient.assert_called_once_with(
            base_url="https://custom.ode.example.com/", timeout=60.0, max_retries=5
        )

    async def test_search_results_fpc_forwarded(self):
        """The results='fpc' parameter is forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_products = AsyncMock(return_value=_make_mock_search_response())

            tool = ODESearchProductsTool()
            await tool.arun(
                ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        call_kwargs = mock_client.search_products.call_args.kwargs
        assert call_kwargs["results"] == "fpc"


# ---------------------------------------------------------------------------
# ODECountProductsTool
# ---------------------------------------------------------------------------


class TestODECountProductsTool:
    """Tests for ODECountProductsTool."""

    async def test_basic_count(self):
        """Basic count returns product count."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(return_value=_make_mock_count_response())

            tool = ODECountProductsTool()
            result = await tool.arun(
                ODECountProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        assert isinstance(result, ODECountProductsOutputSchema)
        assert result.status == "success"
        assert result.count == 42
        assert result.target == "mars"
        assert result.instrument_host == "MRO"
        assert result.instrument == "HIRISE"
        assert result.product_type == "RDRV11"

    async def test_count_with_latlon_filters(self):
        """Lat/lon filters are forwarded to the client."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(return_value=_make_mock_count_response(count=10))

            tool = ODECountProductsTool()
            await tool.arun(
                ODECountProductsInputSchema(
                    target="mars",
                    ihid="MRO",
                    iid="HIRISE",
                    pt="RDRV11",
                    minlat=-15.0,
                    maxlat=-14.0,
                    westlon=175.0,
                    eastlon=176.0,
                )
            )

        call_kwargs = mock_client.count_products.call_args.kwargs
        assert call_kwargs["minlat"] == -15.0
        assert call_kwargs["maxlat"] == -14.0
        assert call_kwargs["westlon"] == 175.0
        assert call_kwargs["eastlon"] == 176.0

    async def test_count_with_time_filters(self):
        """Observation time filters are forwarded to the client."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(return_value=_make_mock_count_response())

            tool = ODECountProductsTool()
            await tool.arun(
                ODECountProductsInputSchema(
                    target="mars",
                    ihid="MRO",
                    iid="HIRISE",
                    pt="RDRV11",
                    minobtime="2020-01-01",
                    maxobtime="2020-12-31",
                )
            )

        call_kwargs = mock_client.count_products.call_args.kwargs
        assert call_kwargs["minobtime"] == "2020-01-01"
        assert call_kwargs["maxobtime"] == "2020-12-31"

    async def test_count_zero_results(self):
        """Zero count returns success with count=0."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(return_value=_make_mock_count_response(count=0))

            tool = ODECountProductsTool()
            result = await tool.arun(
                ODECountProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        assert result.status == "success"
        assert result.count == 0

    async def test_count_api_error_returns_error_schema(self):
        """API error response returns error output schema."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(
                return_value=_make_mock_count_response(status="ERROR", error="Bad instrument ID", count=0)
            )

            tool = ODECountProductsTool()
            result = await tool.arun(
                ODECountProductsInputSchema(target="mars", ihid="MRO", iid="INVALID", pt="RDRV11")
            )

        assert result.status == "error"
        assert result.error == "Bad instrument ID"
        assert result.count == 0

    async def test_count_client_error_raises(self):
        """ODEClientError is re-raised."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(side_effect=ODEClientError("timeout"))

            tool = ODECountProductsTool()
            with pytest.raises(ODEClientError, match="timeout"):
                await tool.arun(
                    ODECountProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
                )

    async def test_count_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(side_effect=KeyError("missing key"))

            tool = ODECountProductsTool()
            with pytest.raises(RuntimeError, match="Internal error during product count"):
                await tool.arun(
                    ODECountProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
                )

    async def test_count_with_config(self):
        """Custom config values are passed to the client."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(return_value=_make_mock_count_response())

            config = ODECountProductsToolConfig(
                base_url="https://custom.ode.example.com/", timeout=45.0, max_retries=2
            )
            tool = ODECountProductsTool(config=config)
            await tool.arun(
                ODECountProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
            )

        MockClient.assert_called_once_with(
            base_url="https://custom.ode.example.com/", timeout=45.0, max_retries=2
        )

    async def test_count_all_filters_combined(self):
        """All filters are forwarded to the client."""
        with patch(_COUNT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.count_products = AsyncMock(return_value=_make_mock_count_response(count=5))

            tool = ODECountProductsTool()
            result = await tool.arun(
                ODECountProductsInputSchema(
                    target="moon",
                    ihid="LRO",
                    iid="LROC",
                    pt="EDR",
                    minlat=-20.0,
                    maxlat=20.0,
                    westlon=0.0,
                    eastlon=180.0,
                    minobtime="2010-01-01",
                    maxobtime="2020-12-31",
                )
            )

        call_kwargs = mock_client.count_products.call_args.kwargs
        assert call_kwargs["target"] == "moon"
        assert call_kwargs["ihid"] == "LRO"
        assert call_kwargs["iid"] == "LROC"
        assert call_kwargs["pt"] == "EDR"
        assert call_kwargs["minlat"] == -20.0
        assert call_kwargs["maxlat"] == 20.0
        assert call_kwargs["westlon"] == 0.0
        assert call_kwargs["eastlon"] == 180.0
        assert call_kwargs["minobtime"] == "2010-01-01"
        assert call_kwargs["maxobtime"] == "2020-12-31"
        assert result.count == 5


# ---------------------------------------------------------------------------
# ODEListInstrumentsTool
# ---------------------------------------------------------------------------


class TestODEListInstrumentsTool:
    """Tests for ODEListInstrumentsTool."""

    async def test_basic_list_instruments(self):
        """Basic list instruments returns instrument summaries."""
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(return_value=_make_mock_instruments_response())

            tool = ODEListInstrumentsTool()
            result = await tool.arun(ODEListInstrumentsInputSchema(target="mars"))

        assert isinstance(result, ODEListInstrumentsOutputSchema)
        assert result.status == "success"
        assert result.target == "mars"
        assert result.count == 1
        assert result.total_available == 1
        assert len(result.instruments) == 1

    async def test_list_instruments_fields(self):
        """Instrument summaries contain expected fields."""
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(return_value=_make_mock_instruments_response())

            tool = ODEListInstrumentsTool()
            result = await tool.arun(ODEListInstrumentsInputSchema(target="mars"))

        inst = result.instruments[0]
        assert isinstance(inst, ODEInstrumentSummary)
        assert inst.ihid == "MRO"
        assert inst.instrument_host_name == "Mars Reconnaissance Orbiter"
        assert inst.iid == "HIRISE"
        assert inst.instrument_name == "High Resolution Imaging Science Experiment"
        assert inst.pt == "RDRV11"
        assert inst.product_type_name == "RDR V1.1"
        assert inst.number_products == 50000

    async def test_list_instruments_with_ihid_filter(self):
        """IHID filter is applied client-side."""
        instruments = [
            _make_mock_instrument_info(ihid="MRO", iid="HIRISE", pt="RDRV11"),
            _make_mock_instrument_info(ihid="MRO", iid="CTX", pt="EDR"),
            _make_mock_instrument_info(ihid="ODY", iid="THEMIS", pt="EDR"),
        ]
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(
                return_value=_make_mock_instruments_response(instruments=instruments)
            )

            tool = ODEListInstrumentsTool()
            result = await tool.arun(ODEListInstrumentsInputSchema(target="mars", ihid="MRO"))

        assert result.count == 2
        assert result.total_available == 2
        for inst in result.instruments:
            assert inst.ihid == "MRO"

    async def test_list_instruments_with_iid_filter(self):
        """IID filter is applied client-side."""
        instruments = [
            _make_mock_instrument_info(ihid="MRO", iid="HIRISE", pt="RDRV11"),
            _make_mock_instrument_info(ihid="MRO", iid="HIRISE", pt="EDR"),
            _make_mock_instrument_info(ihid="MRO", iid="CTX", pt="EDR"),
        ]
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(
                return_value=_make_mock_instruments_response(instruments=instruments)
            )

            tool = ODEListInstrumentsTool()
            result = await tool.arun(ODEListInstrumentsInputSchema(target="mars", iid="HIRISE"))

        assert result.count == 2
        for inst in result.instruments:
            assert inst.iid == "HIRISE"

    async def test_list_instruments_with_ihid_and_iid_filter(self):
        """Combined IHID and IID filter narrows results."""
        instruments = [
            _make_mock_instrument_info(ihid="MRO", iid="HIRISE", pt="RDRV11"),
            _make_mock_instrument_info(ihid="MRO", iid="CTX", pt="EDR"),
            _make_mock_instrument_info(ihid="ODY", iid="HIRISE", pt="EDR"),
        ]
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(
                return_value=_make_mock_instruments_response(instruments=instruments)
            )

            tool = ODEListInstrumentsTool()
            result = await tool.arun(ODEListInstrumentsInputSchema(target="mars", ihid="MRO", iid="HIRISE"))

        assert result.count == 1
        assert result.instruments[0].ihid == "MRO"
        assert result.instruments[0].iid == "HIRISE"

    async def test_list_instruments_with_limit(self):
        """Limit parameter truncates results and sets has_more."""
        instruments = [
            _make_mock_instrument_info(ihid="MRO", iid="HIRISE", pt="RDRV11"),
            _make_mock_instrument_info(ihid="MRO", iid="CTX", pt="EDR"),
            _make_mock_instrument_info(ihid="MRO", iid="CRISM", pt="TRDR"),
        ]
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(
                return_value=_make_mock_instruments_response(instruments=instruments)
            )

            tool = ODEListInstrumentsTool()
            result = await tool.arun(ODEListInstrumentsInputSchema(target="mars", limit=2))

        assert result.count == 2
        assert result.total_available == 3
        assert result.has_more is True

    async def test_list_instruments_has_more_false(self):
        """has_more is False when all instruments fit within limit."""
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(return_value=_make_mock_instruments_response())

            tool = ODEListInstrumentsTool()
            result = await tool.arun(ODEListInstrumentsInputSchema(target="mars"))

        assert result.has_more is False

    async def test_list_instruments_empty(self):
        """Empty instruments list returns count=0."""
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(
                return_value=_make_mock_instruments_response(instruments=[])
            )

            tool = ODEListInstrumentsTool()
            result = await tool.arun(ODEListInstrumentsInputSchema(target="mars"))

        assert result.status == "success"
        assert result.count == 0
        assert result.total_available == 0
        assert result.instruments == []
        assert result.has_more is False

    async def test_list_instruments_api_error_returns_error_schema(self):
        """API error response returns error output schema."""
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(
                return_value=_make_mock_instruments_response(status="ERROR", error="Invalid target", instruments=[])
            )

            tool = ODEListInstrumentsTool()
            result = await tool.arun(ODEListInstrumentsInputSchema(target="mars"))

        assert result.status == "error"
        assert result.error == "Invalid target"
        assert result.count == 0

    async def test_list_instruments_client_error_raises(self):
        """ODEClientError is re-raised."""
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(side_effect=ODEClientError("network error"))

            tool = ODEListInstrumentsTool()
            with pytest.raises(ODEClientError, match="network error"):
                await tool.arun(ODEListInstrumentsInputSchema(target="mars"))

    async def test_list_instruments_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(side_effect=IndexError("out of range"))

            tool = ODEListInstrumentsTool()
            with pytest.raises(RuntimeError, match="Internal error during instruments query"):
                await tool.arun(ODEListInstrumentsInputSchema(target="mars"))

    async def test_list_instruments_with_config(self):
        """Custom config values are passed to the client."""
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(return_value=_make_mock_instruments_response())

            config = ODEListInstrumentsToolConfig(
                base_url="https://custom.ode.example.com/", timeout=20.0, max_retries=1
            )
            tool = ODEListInstrumentsTool(config=config)
            await tool.arun(ODEListInstrumentsInputSchema(target="mars"))

        MockClient.assert_called_once_with(
            base_url="https://custom.ode.example.com/", timeout=20.0, max_retries=1
        )

    async def test_list_instruments_target_forwarded(self):
        """Target is forwarded to the client."""
        with patch(_LIST_INSTRUMENTS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_instruments = AsyncMock(return_value=_make_mock_instruments_response())

            tool = ODEListInstrumentsTool()
            await tool.arun(ODEListInstrumentsInputSchema(target="moon"))

        mock_client.list_instruments.assert_called_once_with("moon")


# ---------------------------------------------------------------------------
# ODEListFeatureClassesTool
# ---------------------------------------------------------------------------


class TestODEListFeatureClassesTool:
    """Tests for ODEListFeatureClassesTool."""

    async def test_basic_list_feature_classes(self):
        """Basic list feature classes returns class names."""
        with patch(_LIST_FEATURE_CLASSES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_classes = AsyncMock(return_value=_make_mock_feature_classes_response())

            tool = ODEListFeatureClassesTool()
            result = await tool.arun(ODEListFeatureClassesInputSchema(target="mars"))

        assert isinstance(result, ODEListFeatureClassesOutputSchema)
        assert result.status == "success"
        assert result.target == "mars"
        assert result.count == 4
        assert result.feature_classes == ["crater", "chasma", "mons", "vallis"]

    async def test_list_feature_classes_different_target(self):
        """Feature classes for a different target are returned correctly."""
        moon_classes = ["crater", "mare", "mons", "lacus", "oceanus"]
        with patch(_LIST_FEATURE_CLASSES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_classes = AsyncMock(
                return_value=_make_mock_feature_classes_response(feature_classes=moon_classes)
            )

            tool = ODEListFeatureClassesTool()
            result = await tool.arun(ODEListFeatureClassesInputSchema(target="moon"))

        assert result.target == "moon"
        assert result.count == 5
        assert "mare" in result.feature_classes
        mock_client.list_feature_classes.assert_called_once_with("moon")

    async def test_list_feature_classes_empty(self):
        """Empty feature classes returns count=0."""
        with patch(_LIST_FEATURE_CLASSES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_classes = AsyncMock(
                return_value=_make_mock_feature_classes_response(feature_classes=[])
            )

            tool = ODEListFeatureClassesTool()
            result = await tool.arun(ODEListFeatureClassesInputSchema(target="venus"))

        assert result.status == "success"
        assert result.count == 0
        assert result.feature_classes == []

    async def test_list_feature_classes_api_error_returns_error_schema(self):
        """API error response returns error output schema."""
        with patch(_LIST_FEATURE_CLASSES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_classes = AsyncMock(
                return_value=_make_mock_feature_classes_response(
                    status="ERROR", error="Service unavailable", feature_classes=[]
                )
            )

            tool = ODEListFeatureClassesTool()
            result = await tool.arun(ODEListFeatureClassesInputSchema(target="mars"))

        assert result.status == "error"
        assert result.error == "Service unavailable"
        assert result.count == 0

    async def test_list_feature_classes_client_error_raises(self):
        """ODEClientError is re-raised."""
        with patch(_LIST_FEATURE_CLASSES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_classes = AsyncMock(side_effect=ODEClientError("rate limited"))

            tool = ODEListFeatureClassesTool()
            with pytest.raises(ODEClientError, match="rate limited"):
                await tool.arun(ODEListFeatureClassesInputSchema(target="mars"))

    async def test_list_feature_classes_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_LIST_FEATURE_CLASSES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_classes = AsyncMock(side_effect=AttributeError("no attribute"))

            tool = ODEListFeatureClassesTool()
            with pytest.raises(RuntimeError, match="Internal error during feature classes query"):
                await tool.arun(ODEListFeatureClassesInputSchema(target="mars"))

    async def test_list_feature_classes_with_config(self):
        """Custom config values are passed to the client."""
        with patch(_LIST_FEATURE_CLASSES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_classes = AsyncMock(return_value=_make_mock_feature_classes_response())

            config = ODEListFeatureClassesToolConfig(
                base_url="https://custom.ode.example.com/", timeout=15.0, max_retries=1
            )
            tool = ODEListFeatureClassesTool(config=config)
            await tool.arun(ODEListFeatureClassesInputSchema(target="mars"))

        MockClient.assert_called_once_with(
            base_url="https://custom.ode.example.com/", timeout=15.0, max_retries=1
        )


# ---------------------------------------------------------------------------
# ODEListFeatureNamesTool
# ---------------------------------------------------------------------------


class TestODEListFeatureNamesTool:
    """Tests for ODEListFeatureNamesTool."""

    async def test_basic_list_feature_names(self):
        """Basic list feature names returns names for a feature class."""
        with patch(_LIST_FEATURE_NAMES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_names = AsyncMock(return_value=_make_mock_feature_names_response())

            tool = ODEListFeatureNamesTool()
            result = await tool.arun(
                ODEListFeatureNamesInputSchema(target="mars", feature_class="crater")
            )

        assert isinstance(result, ODEListFeatureNamesOutputSchema)
        assert result.status == "success"
        assert result.target == "mars"
        assert result.feature_class == "crater"
        assert result.count == 3
        assert result.feature_names == ["Gale", "Jezero", "Holden"]

    async def test_list_feature_names_with_limit(self):
        """Limit parameter is forwarded to the client."""
        with patch(_LIST_FEATURE_NAMES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_names = AsyncMock(
                return_value=_make_mock_feature_names_response(feature_names=["Gale"])
            )

            tool = ODEListFeatureNamesTool()
            await tool.arun(
                ODEListFeatureNamesInputSchema(target="mars", feature_class="crater", limit=1)
            )

        call_kwargs = mock_client.list_feature_names.call_args.kwargs
        assert call_kwargs["limit"] == 1

    async def test_list_feature_names_limit_capped(self):
        """Limit is capped at MAX_FEATURE_NAMES_LIMIT (50)."""
        with patch(_LIST_FEATURE_NAMES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_names = AsyncMock(return_value=_make_mock_feature_names_response())

            tool = ODEListFeatureNamesTool()
            # Schema allows max 50, so test with exactly 50
            await tool.arun(
                ODEListFeatureNamesInputSchema(target="mars", feature_class="crater", limit=50)
            )

        call_kwargs = mock_client.list_feature_names.call_args.kwargs
        assert call_kwargs["limit"] == 50

    async def test_list_feature_names_target_and_class_forwarded(self):
        """Target and feature_class are forwarded to the client."""
        with patch(_LIST_FEATURE_NAMES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_names = AsyncMock(
                return_value=_make_mock_feature_names_response(feature_names=["Tycho", "Copernicus"])
            )

            tool = ODEListFeatureNamesTool()
            await tool.arun(
                ODEListFeatureNamesInputSchema(target="moon", feature_class="crater")
            )

        call_kwargs = mock_client.list_feature_names.call_args.kwargs
        assert call_kwargs["target"] == "moon"
        assert call_kwargs["feature_class"] == "crater"

    async def test_list_feature_names_empty(self):
        """Empty feature names returns count=0."""
        with patch(_LIST_FEATURE_NAMES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_names = AsyncMock(
                return_value=_make_mock_feature_names_response(feature_names=[])
            )

            tool = ODEListFeatureNamesTool()
            result = await tool.arun(
                ODEListFeatureNamesInputSchema(target="mars", feature_class="labyrinthus")
            )

        assert result.status == "success"
        assert result.count == 0
        assert result.feature_names == []

    async def test_list_feature_names_api_error_returns_error_schema(self):
        """API error response returns error output schema."""
        with patch(_LIST_FEATURE_NAMES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_names = AsyncMock(
                return_value=_make_mock_feature_names_response(
                    status="ERROR", error="Unknown feature class", feature_names=[]
                )
            )

            tool = ODEListFeatureNamesTool()
            result = await tool.arun(
                ODEListFeatureNamesInputSchema(target="mars", feature_class="nonexistent")
            )

        assert result.status == "error"
        assert result.error == "Unknown feature class"
        assert result.count == 0

    async def test_list_feature_names_client_error_raises(self):
        """ODEClientError is re-raised."""
        with patch(_LIST_FEATURE_NAMES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_names = AsyncMock(side_effect=ODEClientError("server error"))

            tool = ODEListFeatureNamesTool()
            with pytest.raises(ODEClientError, match="server error"):
                await tool.arun(
                    ODEListFeatureNamesInputSchema(target="mars", feature_class="crater")
                )

    async def test_list_feature_names_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_LIST_FEATURE_NAMES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_names = AsyncMock(side_effect=IOError("disk failure"))

            tool = ODEListFeatureNamesTool()
            with pytest.raises(RuntimeError, match="Internal error during feature names query"):
                await tool.arun(
                    ODEListFeatureNamesInputSchema(target="mars", feature_class="crater")
                )

    async def test_list_feature_names_with_config(self):
        """Custom config values are passed to the client."""
        with patch(_LIST_FEATURE_NAMES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_feature_names = AsyncMock(return_value=_make_mock_feature_names_response())

            config = ODEListFeatureNamesToolConfig(
                base_url="https://custom.ode.example.com/", timeout=10.0, max_retries=2
            )
            tool = ODEListFeatureNamesTool(config=config)
            await tool.arun(
                ODEListFeatureNamesInputSchema(target="mars", feature_class="crater")
            )

        MockClient.assert_called_once_with(
            base_url="https://custom.ode.example.com/", timeout=10.0, max_retries=2
        )


# ---------------------------------------------------------------------------
# ODEGetFeatureBoundsTool
# ---------------------------------------------------------------------------


class TestODEGetFeatureBoundsTool:
    """Tests for ODEGetFeatureBoundsTool."""

    async def test_basic_get_feature_bounds(self):
        """Basic get feature bounds returns bounds dictionary."""
        with patch(_GET_FEATURE_BOUNDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_feature_bounds = AsyncMock(return_value=_make_mock_feature_data_response())

            tool = ODEGetFeatureBoundsTool()
            result = await tool.arun(
                ODEGetFeatureBoundsInputSchema(target="mars", feature_class="crater", feature_name="Gale")
            )

        assert isinstance(result, ODEGetFeatureBoundsOutputSchema)
        assert result.status == "success"
        assert result.target == "mars"
        assert result.feature_class == "crater"
        assert result.feature_name == "Gale"
        assert result.bounds is not None
        assert result.bounds["min_lat"] == -6.0
        assert result.bounds["max_lat"] == -3.5
        assert result.bounds["west_lon"] == 136.5
        assert result.bounds["east_lon"] == 138.5

    async def test_get_feature_bounds_params_forwarded(self):
        """Target, feature_class, and feature_name are forwarded to the client."""
        with patch(_GET_FEATURE_BOUNDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_feature_bounds = AsyncMock(return_value=_make_mock_feature_data_response())

            tool = ODEGetFeatureBoundsTool()
            await tool.arun(
                ODEGetFeatureBoundsInputSchema(target="moon", feature_class="crater", feature_name="Tycho")
            )

        call_kwargs = mock_client.get_feature_bounds.call_args.kwargs
        assert call_kwargs["target"] == "moon"
        assert call_kwargs["feature_class"] == "crater"
        assert call_kwargs["feature_name"] == "Tycho"

    async def test_get_feature_bounds_not_found(self):
        """Feature not found returns not_found status."""
        with patch(_GET_FEATURE_BOUNDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_feature_bounds = AsyncMock(
                return_value=_make_mock_feature_data_response(features=[])
            )

            tool = ODEGetFeatureBoundsTool()
            result = await tool.arun(
                ODEGetFeatureBoundsInputSchema(target="mars", feature_class="crater", feature_name="Nonexistent")
            )

        assert result.status == "not_found"
        assert result.bounds is None
        assert result.message is not None
        assert "Nonexistent" in result.message
        assert "crater" in result.message
        assert "mars" in result.message

    async def test_get_feature_bounds_api_error_returns_error_schema(self):
        """API error response returns error output schema."""
        with patch(_GET_FEATURE_BOUNDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_feature_bounds = AsyncMock(
                return_value=_make_mock_feature_data_response(status="ERROR", error="Malformed request", features=[])
            )

            tool = ODEGetFeatureBoundsTool()
            result = await tool.arun(
                ODEGetFeatureBoundsInputSchema(target="mars", feature_class="crater", feature_name="Gale")
            )

        assert result.status == "error"
        assert result.error == "Malformed request"

    async def test_get_feature_bounds_client_error_raises(self):
        """ODEClientError is re-raised."""
        with patch(_GET_FEATURE_BOUNDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_feature_bounds = AsyncMock(side_effect=ODEClientError("API down"))

            tool = ODEGetFeatureBoundsTool()
            with pytest.raises(ODEClientError, match="API down"):
                await tool.arun(
                    ODEGetFeatureBoundsInputSchema(target="mars", feature_class="crater", feature_name="Gale")
                )

    async def test_get_feature_bounds_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_GET_FEATURE_BOUNDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_feature_bounds = AsyncMock(side_effect=ValueError("parse error"))

            tool = ODEGetFeatureBoundsTool()
            with pytest.raises(RuntimeError, match="Internal error during feature bounds query"):
                await tool.arun(
                    ODEGetFeatureBoundsInputSchema(target="mars", feature_class="crater", feature_name="Gale")
                )

    async def test_get_feature_bounds_with_config(self):
        """Custom config values are passed to the client."""
        with patch(_GET_FEATURE_BOUNDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_feature_bounds = AsyncMock(return_value=_make_mock_feature_data_response())

            config = ODEGetFeatureBoundsToolConfig(
                base_url="https://custom.ode.example.com/", timeout=25.0, max_retries=4
            )
            tool = ODEGetFeatureBoundsTool(config=config)
            await tool.arun(
                ODEGetFeatureBoundsInputSchema(target="mars", feature_class="crater", feature_name="Gale")
            )

        MockClient.assert_called_once_with(
            base_url="https://custom.ode.example.com/", timeout=25.0, max_retries=4
        )

    async def test_get_feature_bounds_uses_first_feature(self):
        """When multiple features returned, uses the first one."""
        features = [
            _make_mock_feature(feature_name="Gale", min_lat=-6.0, max_lat=-3.5),
            _make_mock_feature(feature_name="Gale (duplicate)", min_lat=-7.0, max_lat=-2.0),
        ]
        with patch(_GET_FEATURE_BOUNDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get_feature_bounds = AsyncMock(
                return_value=_make_mock_feature_data_response(features=features)
            )

            tool = ODEGetFeatureBoundsTool()
            result = await tool.arun(
                ODEGetFeatureBoundsInputSchema(target="mars", feature_class="crater", feature_name="Gale")
            )

        assert result.status == "success"
        assert result.bounds["min_lat"] == -6.0
        assert result.bounds["max_lat"] == -3.5


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestODESchemaValidation:
    """Tests for ODE input schema validation."""

    # -- ODESearchProductsInputSchema --

    def test_search_input_requires_target(self):
        """SearchInputSchema requires target."""
        with pytest.raises(Exception):
            ODESearchProductsInputSchema()

    def test_search_input_defaults(self):
        """SearchInputSchema has correct defaults for optional fields."""
        schema = ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
        assert schema.target == "mars"
        assert schema.ihid == "MRO"
        assert schema.iid == "HIRISE"
        assert schema.pt == "RDRV11"
        assert schema.pdsid is None
        assert schema.minlat is None
        assert schema.maxlat is None
        assert schema.westlon is None
        assert schema.eastlon is None
        assert schema.minobtime is None
        assert schema.maxobtime is None
        assert schema.limit == 10
        assert schema.offset == 0

    def test_search_input_invalid_target(self):
        """Invalid target raises validation error."""
        with pytest.raises(Exception):
            ODESearchProductsInputSchema(target="pluto", ihid="MRO", iid="HIRISE", pt="RDRV11")

    def test_search_input_limit_bounds(self):
        """Limit must be between 1 and 10."""
        with pytest.raises(Exception):
            ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", limit=0)
        with pytest.raises(Exception):
            ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", limit=11)

    def test_search_input_offset_non_negative(self):
        """Offset must be >= 0."""
        with pytest.raises(Exception):
            ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", offset=-1)

    def test_search_input_latitude_bounds(self):
        """Latitude must be between -90 and 90."""
        with pytest.raises(Exception):
            ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", minlat=-91)
        with pytest.raises(Exception):
            ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", maxlat=91)

    def test_search_input_longitude_bounds(self):
        """Longitude must be between 0 and 360."""
        with pytest.raises(Exception):
            ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", westlon=-1)
        with pytest.raises(Exception):
            ODESearchProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11", eastlon=361)

    def test_search_input_valid_targets(self):
        """All valid targets are accepted."""
        for t in ("mars", "moon", "mercury", "phobos", "deimos", "venus"):
            schema = ODESearchProductsInputSchema(target=t, ihid="X", iid="Y", pt="Z")
            assert schema.target == t

    # -- ODECountProductsInputSchema --

    def test_count_input_requires_all_fields(self):
        """CountInputSchema requires target, ihid, iid, and pt."""
        with pytest.raises(Exception):
            ODECountProductsInputSchema(target="mars")
        with pytest.raises(Exception):
            ODECountProductsInputSchema(target="mars", ihid="MRO")
        with pytest.raises(Exception):
            ODECountProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE")

    def test_count_input_defaults(self):
        """CountInputSchema has correct defaults."""
        schema = ODECountProductsInputSchema(target="mars", ihid="MRO", iid="HIRISE", pt="RDRV11")
        assert schema.minlat is None
        assert schema.maxlat is None
        assert schema.westlon is None
        assert schema.eastlon is None
        assert schema.minobtime is None
        assert schema.maxobtime is None

    # -- ODEListInstrumentsInputSchema --

    def test_list_instruments_input_requires_target(self):
        """ListInstrumentsInputSchema requires target."""
        with pytest.raises(Exception):
            ODEListInstrumentsInputSchema()

    def test_list_instruments_input_defaults(self):
        """ListInstrumentsInputSchema has correct defaults."""
        schema = ODEListInstrumentsInputSchema(target="mars")
        assert schema.ihid is None
        assert schema.iid is None
        assert schema.limit == 25

    def test_list_instruments_input_limit_bounds(self):
        """Limit must be between 1 and 25."""
        with pytest.raises(Exception):
            ODEListInstrumentsInputSchema(target="mars", limit=0)
        with pytest.raises(Exception):
            ODEListInstrumentsInputSchema(target="mars", limit=26)

    # -- ODEListFeatureClassesInputSchema --

    def test_list_feature_classes_input_requires_target(self):
        """ListFeatureClassesInputSchema requires target."""
        with pytest.raises(Exception):
            ODEListFeatureClassesInputSchema()

    # -- ODEListFeatureNamesInputSchema --

    def test_list_feature_names_input_requires_target_and_class(self):
        """ListFeatureNamesInputSchema requires target and feature_class."""
        with pytest.raises(Exception):
            ODEListFeatureNamesInputSchema()
        with pytest.raises(Exception):
            ODEListFeatureNamesInputSchema(target="mars")

    def test_list_feature_names_input_defaults(self):
        """ListFeatureNamesInputSchema has correct defaults."""
        schema = ODEListFeatureNamesInputSchema(target="mars", feature_class="crater")
        assert schema.limit == 50

    def test_list_feature_names_input_limit_bounds(self):
        """Limit must be between 1 and 50."""
        with pytest.raises(Exception):
            ODEListFeatureNamesInputSchema(target="mars", feature_class="crater", limit=0)
        with pytest.raises(Exception):
            ODEListFeatureNamesInputSchema(target="mars", feature_class="crater", limit=51)

    # -- ODEGetFeatureBoundsInputSchema --

    def test_get_feature_bounds_input_requires_all_fields(self):
        """GetFeatureBoundsInputSchema requires target, feature_class, and feature_name."""
        with pytest.raises(Exception):
            ODEGetFeatureBoundsInputSchema()
        with pytest.raises(Exception):
            ODEGetFeatureBoundsInputSchema(target="mars")
        with pytest.raises(Exception):
            ODEGetFeatureBoundsInputSchema(target="mars", feature_class="crater")
