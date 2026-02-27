"""Unit tests for PDS4 Registry tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from akd_ext.tools.pds.pds4.crawl_context_product import (
    PDS4CrawlContextProductInputSchema,
    PDS4CrawlContextProductOutputSchema,
    PDS4CrawlContextProductTool,
)
from akd_ext.tools.pds.pds4.get_product import (
    PDS4GetProductInputSchema,
    PDS4GetProductOutputSchema,
    PDS4GetProductTool,
)
from akd_ext.tools.pds.pds4.search_bundles import (
    BundleSummary,
    PDS4SearchBundlesInputSchema,
    PDS4SearchBundlesOutputSchema,
    PDS4SearchBundlesTool,
    PDS4SearchBundlesToolConfig,
)
from akd_ext.tools.pds.pds4.search_investigations import (
    InvestigationSummary,
    PDS4SearchInvestigationsInputSchema,
    PDS4SearchInvestigationsOutputSchema,
    PDS4SearchInvestigationsTool,
)
from akd_ext.tools.pds.pds4.search_products import (
    PDS4SearchProductsInputSchema,
    PDS4SearchProductsOutputSchema,
    PDS4SearchProductsTool,
    ProductSummary,
)
from akd_ext.tools.pds.utils.pds4_client import PDS4ClientError

# Patch paths -- must match where PDS4Client is looked up at runtime
_SEARCH_BUNDLES_CLIENT = "akd_ext.tools.pds.pds4.search_bundles.PDS4Client"
_SEARCH_PRODUCTS_CLIENT = "akd_ext.tools.pds.pds4.search_products.PDS4Client"
_SEARCH_COLLECTIONS_CLIENT = "akd_ext.tools.pds.pds4.search_collections.PDS4Client"
_SEARCH_INVESTIGATIONS_CLIENT = "akd_ext.tools.pds.pds4.search_investigations.PDS4Client"
_SEARCH_TARGETS_CLIENT = "akd_ext.tools.pds.pds4.search_targets.PDS4Client"
_SEARCH_INSTRUMENT_HOSTS_CLIENT = "akd_ext.tools.pds.pds4.search_instrument_hosts.PDS4Client"
_SEARCH_INSTRUMENTS_CLIENT = "akd_ext.tools.pds.pds4.search_instruments.PDS4Client"
_CRAWL_CLIENT = "akd_ext.tools.pds.pds4.crawl_context_product.PDS4Client"
_GET_PRODUCT_CLIENT = "akd_ext.tools.pds.pds4.get_product.PDS4Client"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_product(**overrides):
    """Build a mock PDS4Product with sensible defaults."""
    product = MagicMock()
    product.id = overrides.get("id", "urn:nasa:pds:cassini_iss::1.0")
    product.lid = overrides.get("lid", "urn:nasa:pds:cassini_iss")
    product.lidvid = overrides.get("lidvid", "urn:nasa:pds:cassini_iss::1.0")
    product.title = overrides.get("title", "Cassini ISS Raw Data Bundle")

    # Model objects with model_dump support
    inv_area = MagicMock()
    inv_area.model_dump.return_value = {"name": "Cassini-Huygens", "type": "Mission"}
    product.investigation_area = overrides.get("investigation_area", inv_area)

    ident_area = MagicMock()
    ident_area.model_dump.return_value = {"title": "Cassini ISS Raw Data Bundle"}
    product.identification_area = overrides.get("identification_area", ident_area)

    target_id = MagicMock()
    target_id.model_dump.return_value = {"name": "Saturn", "type": "Planet"}
    product.target_identification = overrides.get("target_identification", target_id)

    time_coords = MagicMock()
    time_coords.model_dump.return_value = {
        "start_date_time": "2004-06-30T00:00:00Z",
        "stop_date_time": "2017-09-15T00:00:00Z",
    }
    product.time_coordinates = overrides.get("time_coordinates", time_coords)

    harvest_info = MagicMock()
    harvest_info.model_dump.return_value = {"node_name": "img"}
    product.harvest_info = overrides.get("harvest_info", harvest_info)

    # For products search
    product.ref_lid_target = overrides.get("ref_lid_target", "urn:nasa:pds:context:target:planet.saturn")
    product.properties = overrides.get("properties", {})

    # For investigations search
    investigation = MagicMock()
    investigation.model_dump.return_value = {
        "start_date": "1997-10-15",
        "stop_date": "2017-09-15",
        "type": "Mission",
    }
    product.investigation = overrides.get("investigation", investigation)

    label_file_info = MagicMock()
    label_file_info.model_dump.return_value = {"file_ref": "/data/pds4/cassini_iss/bundle.xml"}
    product.label_file_info = overrides.get("label_file_info", label_file_info)

    return product


def _make_mock_search_response(products=None, hits=None, took=50, q="test query", facets=None):
    """Build a mock PDS4SearchResponse."""
    if products is None:
        products = [_make_mock_product()]
    response = MagicMock()
    response.summary.hits = hits if hits is not None else len(products)
    response.summary.took = took
    response.summary.q = q
    response.data = products
    response.facets = facets or []
    return response


def _patch_client_context(patch_path, method_name, return_value=None, side_effect=None):
    """Create a patch context for a PDS4Client async context manager.

    Returns:
        A tuple (patcher, setup_func) where setup_func configures the mock.
    """
    patcher = patch(patch_path)

    def setup(mock_cls):
        mock_instance = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        method = getattr(mock_instance, method_name)
        if side_effect is not None:
            method.side_effect = side_effect
        else:
            method.return_value = return_value
        return mock_instance

    return patcher, setup


# ---------------------------------------------------------------------------
# PDS4SearchBundlesTool
# ---------------------------------------------------------------------------


class TestPDS4SearchBundlesTool:
    """Tests for PDS4SearchBundlesTool."""

    async def test_basic_search(self):
        """Search with defaults returns bundles."""
        mock_response = _make_mock_search_response()
        patcher, setup = _patch_client_context(_SEARCH_BUNDLES_CLIENT, "search_bundles", mock_response)
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4SearchBundlesTool()
            result = await tool.arun(PDS4SearchBundlesInputSchema())

        assert isinstance(result, PDS4SearchBundlesOutputSchema)
        assert result.total_hits == 1
        assert result.query_time_ms == 50
        assert result.query == "test query"
        assert len(result.bundles) == 1
        assert isinstance(result.bundles[0], BundleSummary)
        assert result.bundles[0].id == "urn:nasa:pds:cassini_iss::1.0"

    async def test_search_with_title_query(self):
        """title_query is forwarded to the client."""
        mock_response = _make_mock_search_response()
        patcher, setup = _patch_client_context(_SEARCH_BUNDLES_CLIENT, "search_bundles", mock_response)
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4SearchBundlesTool()
            await tool.arun(PDS4SearchBundlesInputSchema(title_query="Lunar"))

        mock_instance.search_bundles.assert_called_once()
        call_kwargs = mock_instance.search_bundles.call_args.kwargs
        assert call_kwargs["title_query"] == "Lunar"

    async def test_search_with_filters(self):
        """All filter parameters are forwarded to the client."""
        mock_response = _make_mock_search_response()
        patcher, setup = _patch_client_context(_SEARCH_BUNDLES_CLIENT, "search_bundles", mock_response)
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4SearchBundlesTool()
            await tool.arun(
                PDS4SearchBundlesInputSchema(
                    title_query="Mars",
                    start_time="2020-01-01T00:00:00Z",
                    end_time="2023-01-01T00:00:00Z",
                    processing_level="Calibrated",
                    limit=50,
                )
            )

        call_kwargs = mock_instance.search_bundles.call_args.kwargs
        assert call_kwargs["title_query"] == "Mars"
        assert call_kwargs["start_time"] == "2020-01-01T00:00:00Z"
        assert call_kwargs["end_time"] == "2023-01-01T00:00:00Z"
        assert call_kwargs["processing_level"] == "Calibrated"
        assert call_kwargs["limit"] == 50

    async def test_search_with_facets(self):
        """Facet fields are parsed and forwarded, facet response is formatted."""
        mock_facet = MagicMock()
        mock_facet.property = "pds:Identification_Area.pds:title"
        mock_facet.counts = {"Cassini ISS": 5, "Juno JunoCam": 3}
        mock_response = _make_mock_search_response(products=[], hits=0, facets=[mock_facet])

        patcher, setup = _patch_client_context(_SEARCH_BUNDLES_CLIENT, "search_bundles", mock_response)
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4SearchBundlesTool()
            result = await tool.arun(
                PDS4SearchBundlesInputSchema(
                    limit=0,
                    facet_fields="pds:Identification_Area.pds:title,lidvid",
                    facet_limit=50,
                )
            )

        call_kwargs = mock_instance.search_bundles.call_args.kwargs
        assert call_kwargs["facet_fields"] == ["pds:Identification_Area.pds:title", "lidvid"]
        assert call_kwargs["facet_limit"] == 50

        assert "pds:Identification_Area.pds:title" in result.facets
        assert result.facets["pds:Identification_Area.pds:title"]["Cassini ISS"] == 5

    async def test_search_empty_results(self):
        """Empty search results return total_hits=0 and empty bundles list."""
        mock_response = _make_mock_search_response(products=[], hits=0)
        patcher, setup = _patch_client_context(_SEARCH_BUNDLES_CLIENT, "search_bundles", mock_response)
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchBundlesTool()
            result = await tool.arun(PDS4SearchBundlesInputSchema(title_query="nonexistent"))

        assert result.total_hits == 0
        assert result.bundles == []
        assert result.facets == {}

    async def test_search_client_error_raised(self):
        """PDS4ClientError is re-raised."""
        patcher, setup = _patch_client_context(
            _SEARCH_BUNDLES_CLIENT, "search_bundles", side_effect=PDS4ClientError("API timeout")
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchBundlesTool()
            with pytest.raises(PDS4ClientError, match="API timeout"):
                await tool.arun(PDS4SearchBundlesInputSchema())

    async def test_search_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        patcher, setup = _patch_client_context(
            _SEARCH_BUNDLES_CLIENT, "search_bundles", side_effect=TypeError("bad type")
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchBundlesTool()
            with pytest.raises(RuntimeError, match="Internal error during bundle search"):
                await tool.arun(PDS4SearchBundlesInputSchema())

    async def test_search_bundle_fields_populated(self):
        """Bundle summary fields are populated from product model_dump."""
        product = _make_mock_product(
            id="urn:nasa:pds:lro_lroc::1.0",
            lid="urn:nasa:pds:lro_lroc",
            lidvid="urn:nasa:pds:lro_lroc::1.0",
            title="LRO LROC Data Bundle",
        )
        mock_response = _make_mock_search_response(products=[product])
        patcher, setup = _patch_client_context(_SEARCH_BUNDLES_CLIENT, "search_bundles", mock_response)
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchBundlesTool()
            result = await tool.arun(PDS4SearchBundlesInputSchema())

        bundle = result.bundles[0]
        assert bundle.id == "urn:nasa:pds:lro_lroc::1.0"
        assert bundle.lid == "urn:nasa:pds:lro_lroc"
        assert bundle.title == "LRO LROC Data Bundle"
        assert bundle.investigation_area is not None
        assert bundle.time_coordinates is not None


# ---------------------------------------------------------------------------
# PDS4SearchProductsTool
# ---------------------------------------------------------------------------


class TestPDS4SearchProductsTool:
    """Tests for PDS4SearchProductsTool."""

    async def test_basic_search(self):
        """Search with defaults returns products."""
        mock_response = _make_mock_search_response()
        patcher, setup = _patch_client_context(_SEARCH_PRODUCTS_CLIENT, "search_products_advanced", mock_response)
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchProductsTool()
            result = await tool.arun(PDS4SearchProductsInputSchema())

        assert isinstance(result, PDS4SearchProductsOutputSchema)
        assert result.total_hits == 1
        assert len(result.products) == 1

    async def test_search_with_keywords(self):
        """Keywords filter is forwarded to the client."""
        mock_response = _make_mock_search_response()
        patcher, setup = _patch_client_context(_SEARCH_PRODUCTS_CLIENT, "search_products_advanced", mock_response)
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4SearchProductsTool()
            await tool.arun(PDS4SearchProductsInputSchema(keywords="HiRISE"))

        call_kwargs = mock_instance.search_products_advanced.call_args.kwargs
        assert call_kwargs["keywords"] == "HiRISE"

    async def test_search_with_bbox_and_target(self):
        """Bounding box and target filters are forwarded."""
        mock_response = _make_mock_search_response()
        patcher, setup = _patch_client_context(_SEARCH_PRODUCTS_CLIENT, "search_products_advanced", mock_response)
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4SearchProductsTool()
            await tool.arun(
                PDS4SearchProductsInputSchema(
                    bbox_north=45.0,
                    bbox_south=-45.0,
                    bbox_east=180.0,
                    bbox_west=-180.0,
                    ref_lid_target="urn:nasa:pds:context:target:planet.mars",
                )
            )

        call_kwargs = mock_instance.search_products_advanced.call_args.kwargs
        assert call_kwargs["bbox_north"] == 45.0
        assert call_kwargs["bbox_south"] == -45.0
        assert call_kwargs["bbox_east"] == 180.0
        assert call_kwargs["bbox_west"] == -180.0
        assert call_kwargs["ref_lid_target"] == "urn:nasa:pds:context:target:planet.mars"

    async def test_search_with_temporal_and_processing(self):
        """Temporal and processing level filters are forwarded."""
        mock_response = _make_mock_search_response()
        patcher, setup = _patch_client_context(_SEARCH_PRODUCTS_CLIENT, "search_products_advanced", mock_response)
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4SearchProductsTool()
            await tool.arun(
                PDS4SearchProductsInputSchema(
                    start_time="2020-01-01T00:00:00Z",
                    end_time="2021-01-01T00:00:00Z",
                    processing_level="Raw",
                    limit=50,
                )
            )

        call_kwargs = mock_instance.search_products_advanced.call_args.kwargs
        assert call_kwargs["start_time"] == "2020-01-01T00:00:00Z"
        assert call_kwargs["end_time"] == "2021-01-01T00:00:00Z"
        assert call_kwargs["processing_level"] == "Raw"
        assert call_kwargs["limit"] == 50

    async def test_search_empty_results(self):
        """Empty search results return total_hits=0 and empty products list."""
        mock_response = _make_mock_search_response(products=[], hits=0)
        patcher, setup = _patch_client_context(_SEARCH_PRODUCTS_CLIENT, "search_products_advanced", mock_response)
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchProductsTool()
            result = await tool.arun(PDS4SearchProductsInputSchema(keywords="nonexistent"))

        assert result.total_hits == 0
        assert result.products == []

    async def test_search_with_processing_level_in_properties(self):
        """Processing level extracted from product properties."""
        product = _make_mock_product(
            properties={
                "pds:Primary_Result_Summary.pds:processing_level": ["Calibrated"],
            }
        )
        mock_response = _make_mock_search_response(products=[product])
        patcher, setup = _patch_client_context(_SEARCH_PRODUCTS_CLIENT, "search_products_advanced", mock_response)
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchProductsTool()
            result = await tool.arun(PDS4SearchProductsInputSchema())

        assert result.products[0].processing_level == "Calibrated"

    async def test_search_client_error_raised(self):
        """PDS4ClientError is re-raised."""
        patcher, setup = _patch_client_context(
            _SEARCH_PRODUCTS_CLIENT, "search_products_advanced", side_effect=PDS4ClientError("connection refused")
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchProductsTool()
            with pytest.raises(PDS4ClientError, match="connection refused"):
                await tool.arun(PDS4SearchProductsInputSchema())

    async def test_search_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        patcher, setup = _patch_client_context(
            _SEARCH_PRODUCTS_CLIENT, "search_products_advanced", side_effect=KeyError("missing")
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchProductsTool()
            with pytest.raises(RuntimeError, match="Internal error during product search"):
                await tool.arun(PDS4SearchProductsInputSchema())


# ---------------------------------------------------------------------------
# PDS4SearchInvestigationsTool
# ---------------------------------------------------------------------------


class TestPDS4SearchInvestigationsTool:
    """Tests for PDS4SearchInvestigationsTool."""

    async def test_basic_search(self):
        """Search with defaults returns investigations."""
        mock_response = _make_mock_search_response()
        patcher, setup = _patch_client_context(
            _SEARCH_INVESTIGATIONS_CLIENT, "search_context_investigations", mock_response
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchInvestigationsTool()
            result = await tool.arun(PDS4SearchInvestigationsInputSchema())

        assert isinstance(result, PDS4SearchInvestigationsOutputSchema)
        assert result.total_hits == 1
        assert len(result.investigations) == 1
        assert isinstance(result.investigations[0], InvestigationSummary)

    async def test_search_with_keywords(self):
        """Keywords filter is forwarded to the client."""
        mock_response = _make_mock_search_response()
        patcher, setup = _patch_client_context(
            _SEARCH_INVESTIGATIONS_CLIENT, "search_context_investigations", mock_response
        )
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4SearchInvestigationsTool()
            await tool.arun(PDS4SearchInvestigationsInputSchema(keywords="mars rover"))

        call_kwargs = mock_instance.search_context_investigations.call_args.kwargs
        assert call_kwargs["keywords"] == "mars rover"

    async def test_search_with_limit(self):
        """Limit parameter is forwarded to the client."""
        mock_response = _make_mock_search_response(products=[], hits=0)
        patcher, setup = _patch_client_context(
            _SEARCH_INVESTIGATIONS_CLIENT, "search_context_investigations", mock_response
        )
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4SearchInvestigationsTool()
            await tool.arun(PDS4SearchInvestigationsInputSchema(limit=50))

        call_kwargs = mock_instance.search_context_investigations.call_args.kwargs
        assert call_kwargs["limit"] == 50

    async def test_search_empty_results(self):
        """Empty search results return total_hits=0 and empty investigations list."""
        mock_response = _make_mock_search_response(products=[], hits=0)
        patcher, setup = _patch_client_context(
            _SEARCH_INVESTIGATIONS_CLIENT, "search_context_investigations", mock_response
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchInvestigationsTool()
            result = await tool.arun(PDS4SearchInvestigationsInputSchema(keywords="nonexistent"))

        assert result.total_hits == 0
        assert result.investigations == []

    async def test_search_investigation_fields_populated(self):
        """Investigation summary fields are populated from the product."""
        product = _make_mock_product(
            id="urn:nasa:pds:context:investigation:mission.juno",
            lid="urn:nasa:pds:context:investigation:mission.juno",
            title="Juno Mission",
        )
        mock_response = _make_mock_search_response(products=[product])
        patcher, setup = _patch_client_context(
            _SEARCH_INVESTIGATIONS_CLIENT, "search_context_investigations", mock_response
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchInvestigationsTool()
            result = await tool.arun(PDS4SearchInvestigationsInputSchema())

        inv = result.investigations[0]
        assert inv.id == "urn:nasa:pds:context:investigation:mission.juno"
        assert inv.title == "Juno Mission"
        assert inv.investigation is not None
        assert inv.label_file_info is not None

    async def test_search_client_error_raised(self):
        """PDS4ClientError is re-raised."""
        patcher, setup = _patch_client_context(
            _SEARCH_INVESTIGATIONS_CLIENT,
            "search_context_investigations",
            side_effect=PDS4ClientError("server error"),
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchInvestigationsTool()
            with pytest.raises(PDS4ClientError, match="server error"):
                await tool.arun(PDS4SearchInvestigationsInputSchema())

    async def test_search_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        patcher, setup = _patch_client_context(
            _SEARCH_INVESTIGATIONS_CLIENT,
            "search_context_investigations",
            side_effect=OSError("network down"),
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4SearchInvestigationsTool()
            with pytest.raises(RuntimeError, match="Internal error during investigation search"):
                await tool.arun(PDS4SearchInvestigationsInputSchema())


# ---------------------------------------------------------------------------
# PDS4GetProductTool
# ---------------------------------------------------------------------------


class TestPDS4GetProductTool:
    """Tests for PDS4GetProductTool."""

    async def test_get_product_basic(self):
        """Get a product by URN returns raw product data."""
        mock_product_data = {
            "id": "urn:nasa:pds:context:investigation:mission.juno",
            "title": "Juno Mission",
            "investigations": [{"id": "urn:nasa:pds:context:investigation:mission.juno"}],
        }
        patcher, setup = _patch_client_context(_GET_PRODUCT_CLIENT, "get_product", mock_product_data)
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4GetProductTool()
            result = await tool.arun(
                PDS4GetProductInputSchema(urn="urn:nasa:pds:context:investigation:mission.juno")
            )

        assert isinstance(result, PDS4GetProductOutputSchema)
        assert result.product["id"] == "urn:nasa:pds:context:investigation:mission.juno"
        assert result.product["title"] == "Juno Mission"

    async def test_get_product_urn_forwarded(self):
        """URN is forwarded to the client."""
        patcher, setup = _patch_client_context(_GET_PRODUCT_CLIENT, "get_product", {"id": "test"})
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4GetProductTool()
            await tool.arun(PDS4GetProductInputSchema(urn="urn:nasa:pds:cassini_iss"))

        mock_instance.get_product.assert_called_once_with("urn:nasa:pds:cassini_iss")

    async def test_get_product_complex_data(self):
        """Complex product data is returned as-is."""
        mock_data = {
            "id": "urn:nasa:pds:cassini_iss::1.0",
            "title": "Cassini ISS Raw Data",
            "properties": {
                "pds:Identification_Area.pds:title": ["Cassini ISS Raw Data"],
                "pds:Time_Coordinates.pds:start_date_time": ["2004-06-30T00:00:00Z"],
            },
            "investigations": [{"id": "urn:nasa:pds:context:investigation:mission.cassini-huygens"}],
            "targets": [{"id": "urn:nasa:pds:context:target:planet.saturn"}],
        }
        patcher, setup = _patch_client_context(_GET_PRODUCT_CLIENT, "get_product", mock_data)
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4GetProductTool()
            result = await tool.arun(PDS4GetProductInputSchema(urn="urn:nasa:pds:cassini_iss"))

        assert result.product["properties"]["pds:Identification_Area.pds:title"] == ["Cassini ISS Raw Data"]
        assert len(result.product["investigations"]) == 1
        assert len(result.product["targets"]) == 1

    async def test_get_product_client_error_raised(self):
        """PDS4ClientError is re-raised."""
        patcher, setup = _patch_client_context(
            _GET_PRODUCT_CLIENT, "get_product", side_effect=PDS4ClientError("product not found")
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4GetProductTool()
            with pytest.raises(PDS4ClientError, match="product not found"):
                await tool.arun(PDS4GetProductInputSchema(urn="urn:nasa:pds:nonexistent:bundle"))

    async def test_get_product_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        patcher, setup = _patch_client_context(
            _GET_PRODUCT_CLIENT, "get_product", side_effect=IOError("disk error")
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4GetProductTool()
            with pytest.raises(RuntimeError, match="Internal error during product retrieval"):
                await tool.arun(PDS4GetProductInputSchema(urn="urn:nasa:pds:cassini_iss"))


# ---------------------------------------------------------------------------
# PDS4CrawlContextProductTool
# ---------------------------------------------------------------------------


class TestPDS4CrawlContextProductTool:
    """Tests for PDS4CrawlContextProductTool."""

    async def test_crawl_basic(self):
        """Crawl returns associated context products."""
        mock_crawl_result = {
            "investigations": {
                "urn:nasa:pds:context:investigation:mission.juno": {
                    "id": "urn:nasa:pds:context:investigation:mission.juno",
                    "title": "Juno Mission",
                }
            },
            "observing_system_components": {
                "urn:nasa:pds:context:instrument:juno.jiram": {
                    "id": "urn:nasa:pds:context:instrument:juno.jiram",
                    "title": "JIRAM",
                }
            },
            "targets": {
                "urn:nasa:pds:context:target:planet.jupiter": {
                    "id": "urn:nasa:pds:context:target:planet.jupiter",
                    "title": "Jupiter",
                }
            },
        }
        patcher, setup = _patch_client_context(_CRAWL_CLIENT, "crawl_context_product", mock_crawl_result)
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4CrawlContextProductTool()
            result = await tool.arun(
                PDS4CrawlContextProductInputSchema(urn="urn:nasa:pds:context:investigation:mission.juno")
            )

        assert isinstance(result, PDS4CrawlContextProductOutputSchema)
        assert "urn:nasa:pds:context:investigation:mission.juno" in result.investigations
        assert result.investigations["urn:nasa:pds:context:investigation:mission.juno"]["title"] == "Juno Mission"
        assert "urn:nasa:pds:context:instrument:juno.jiram" in result.observing_system_components
        assert "urn:nasa:pds:context:target:planet.jupiter" in result.targets
        assert result.errors is None

    async def test_crawl_urn_forwarded(self):
        """URN is forwarded to the client."""
        mock_result = {"investigations": {}, "observing_system_components": {}, "targets": {}}
        patcher, setup = _patch_client_context(_CRAWL_CLIENT, "crawl_context_product", mock_result)
        with patcher as MockClient:
            mock_instance = setup(MockClient)

            tool = PDS4CrawlContextProductTool()
            await tool.arun(
                PDS4CrawlContextProductInputSchema(urn="urn:nasa:pds:context:target:planet.mars")
            )

        mock_instance.crawl_context_product.assert_called_once_with("urn:nasa:pds:context:target:planet.mars")

    async def test_crawl_with_errors(self):
        """Crawl result with errors passes them through."""
        mock_result = {
            "investigations": {},
            "observing_system_components": {},
            "targets": {},
            "errors": ["Failed to fetch urn:nasa:pds:context:instrument:juno.jade: connection timeout"],
        }
        patcher, setup = _patch_client_context(_CRAWL_CLIENT, "crawl_context_product", mock_result)
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4CrawlContextProductTool()
            result = await tool.arun(
                PDS4CrawlContextProductInputSchema(urn="urn:nasa:pds:context:investigation:mission.juno")
            )

        assert result.errors is not None
        assert len(result.errors) == 1
        assert "connection timeout" in result.errors[0]

    async def test_crawl_empty_results(self):
        """Crawl with no related products returns empty dicts."""
        mock_result = {"investigations": {}, "observing_system_components": {}, "targets": {}}
        patcher, setup = _patch_client_context(_CRAWL_CLIENT, "crawl_context_product", mock_result)
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4CrawlContextProductTool()
            result = await tool.arun(
                PDS4CrawlContextProductInputSchema(urn="urn:nasa:pds:context:target:planet.pluto")
            )

        assert result.investigations == {}
        assert result.observing_system_components == {}
        assert result.targets == {}
        assert result.errors is None

    async def test_crawl_client_error_raised(self):
        """PDS4ClientError is re-raised."""
        patcher, setup = _patch_client_context(
            _CRAWL_CLIENT, "crawl_context_product", side_effect=PDS4ClientError("invalid URN")
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4CrawlContextProductTool()
            with pytest.raises(PDS4ClientError, match="invalid URN"):
                await tool.arun(PDS4CrawlContextProductInputSchema(urn="urn:nasa:pds:context:target:planet.mars"))

    async def test_crawl_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        patcher, setup = _patch_client_context(
            _CRAWL_CLIENT, "crawl_context_product", side_effect=ValueError("unexpected")
        )
        with patcher as MockClient:
            setup(MockClient)

            tool = PDS4CrawlContextProductTool()
            with pytest.raises(RuntimeError, match="Internal error during context product crawl"):
                await tool.arun(PDS4CrawlContextProductInputSchema(urn="urn:nasa:pds:context:target:planet.mars"))


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestPDS4SchemaValidation:
    """Tests for PDS4 input schema validation."""

    def test_bundles_input_defaults(self):
        """SearchBundlesInputSchema has correct defaults."""
        schema = PDS4SearchBundlesInputSchema()
        assert schema.title_query is None
        assert schema.start_time is None
        assert schema.end_time is None
        assert schema.processing_level is None
        assert schema.limit == 0
        assert schema.facet_fields is None
        assert schema.facet_limit == 25

    def test_bundles_input_limit_bounds(self):
        """Bundle limit must be between 0 and 100."""
        with pytest.raises(Exception):
            PDS4SearchBundlesInputSchema(limit=-1)
        with pytest.raises(Exception):
            PDS4SearchBundlesInputSchema(limit=101)

    def test_bundles_input_valid_processing_level(self):
        """Valid processing levels are accepted."""
        schema = PDS4SearchBundlesInputSchema(processing_level="Raw")
        assert schema.processing_level == "Raw"
        schema = PDS4SearchBundlesInputSchema(processing_level="Calibrated")
        assert schema.processing_level == "Calibrated"
        schema = PDS4SearchBundlesInputSchema(processing_level="Derived")
        assert schema.processing_level == "Derived"

    def test_bundles_input_invalid_processing_level(self):
        """Invalid processing level raises validation error."""
        with pytest.raises(Exception):
            PDS4SearchBundlesInputSchema(processing_level="invalid")

    def test_products_input_defaults(self):
        """SearchProductsInputSchema has correct defaults."""
        schema = PDS4SearchProductsInputSchema()
        assert schema.keywords is None
        assert schema.start_time is None
        assert schema.end_time is None
        assert schema.processing_level is None
        assert schema.bbox_north is None
        assert schema.bbox_south is None
        assert schema.bbox_east is None
        assert schema.bbox_west is None
        assert schema.ref_lid_target is None
        assert schema.limit == 100

    def test_products_input_bbox_bounds(self):
        """Bounding box coordinates must be within valid range."""
        with pytest.raises(Exception):
            PDS4SearchProductsInputSchema(bbox_north=91)
        with pytest.raises(Exception):
            PDS4SearchProductsInputSchema(bbox_south=-91)
        with pytest.raises(Exception):
            PDS4SearchProductsInputSchema(bbox_east=181)
        with pytest.raises(Exception):
            PDS4SearchProductsInputSchema(bbox_west=-181)

    def test_investigations_input_defaults(self):
        """SearchInvestigationsInputSchema has correct defaults."""
        schema = PDS4SearchInvestigationsInputSchema()
        assert schema.keywords is None
        assert schema.limit == 10

    def test_get_product_input_requires_urn(self):
        """GetProductInputSchema requires urn."""
        with pytest.raises(Exception):
            PDS4GetProductInputSchema()

    def test_crawl_input_requires_urn(self):
        """CrawlContextProductInputSchema requires urn."""
        with pytest.raises(Exception):
            PDS4CrawlContextProductInputSchema()
