"""Integration tests for ODE tools using the real ODE REST API."""

import pytest

from akd_ext.tools.pds.ode.search_products import (
    ODESearchProductsInputSchema,
    ODESearchProductsOutputSchema,
    ODESearchProductsTool,
)
from akd_ext.tools.pds.ode.count_products import (
    ODECountProductsInputSchema,
    ODECountProductsOutputSchema,
    ODECountProductsTool,
)
from akd_ext.tools.pds.ode.list_instruments import (
    ODEListInstrumentsInputSchema,
    ODEListInstrumentsOutputSchema,
    ODEListInstrumentsTool,
)
from akd_ext.tools.pds.ode.list_feature_classes import (
    ODEListFeatureClassesInputSchema,
    ODEListFeatureClassesOutputSchema,
    ODEListFeatureClassesTool,
)
from akd_ext.tools.pds.ode.list_feature_names import (
    ODEListFeatureNamesInputSchema,
    ODEListFeatureNamesOutputSchema,
    ODEListFeatureNamesTool,
)
from akd_ext.tools.pds.ode.get_feature_bounds import (
    ODEGetFeatureBoundsInputSchema,
    ODEGetFeatureBoundsOutputSchema,
    ODEGetFeatureBoundsTool,
)


# ---------------------------------------------------------------------------
# ODESearchProductsTool -- integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestODESearchProductsIntegration:
    """Integration tests for ODESearchProductsTool against the real ODE REST API."""

    async def test_search_mars_hirise(self):
        """Search Mars MRO HIRISE RDRV11 returns products."""
        tool = ODESearchProductsTool()
        result = await tool.arun(
            ODESearchProductsInputSchema(
                target="mars",
                ihid="MRO",
                iid="HIRISE",
                pt="RDRV11",
                limit=3,
            )
        )

        assert isinstance(result, ODESearchProductsOutputSchema)
        assert result.status == "success"
        assert result.count > 0
        assert len(result.products) <= 3
        assert result.total_available > 0
        for product in result.products:
            assert product.pdsid is not None

    async def test_search_by_pdsid(self):
        """Search by a specific PDS product ID returns that product."""
        tool = ODESearchProductsTool()
        result = await tool.arun(
            ODESearchProductsInputSchema(
                target="mars",
                pdsid="ESP_012600_1655_RED",
            )
        )

        assert result.status == "success"
        assert result.count >= 1
        pdsids = [p.pdsid for p in result.products]
        assert "ESP_012600_1655_RED" in pdsids

    async def test_search_with_geographic_bounds(self):
        """Search with lat/lon bounds for Gale crater area returns products."""
        tool = ODESearchProductsTool()
        result = await tool.arun(
            ODESearchProductsInputSchema(
                target="mars",
                ihid="MRO",
                iid="HIRISE",
                pt="RDRV11",
                minlat=-6,
                maxlat=-3,
                westlon=136,
                eastlon=138,
                limit=5,
            )
        )

        assert result.status == "success"
        assert result.count > 0
        for product in result.products:
            assert product.pdsid is not None

    async def test_search_pagination(self):
        """Pagination returns different products on page 1 vs page 2."""
        tool = ODESearchProductsTool()

        page1 = await tool.arun(
            ODESearchProductsInputSchema(
                target="mars",
                ihid="MRO",
                iid="HIRISE",
                pt="RDRV11",
                limit=3,
                offset=0,
            )
        )
        page2 = await tool.arun(
            ODESearchProductsInputSchema(
                target="mars",
                ihid="MRO",
                iid="HIRISE",
                pt="RDRV11",
                limit=3,
                offset=3,
            )
        )

        assert page1.status == "success"
        assert page2.status == "success"

        page1_pdsids = {p.pdsid for p in page1.products}
        page2_pdsids = {p.pdsid for p in page2.products}
        assert page1_pdsids.isdisjoint(page2_pdsids), "Paginated pages should not overlap"


# ---------------------------------------------------------------------------
# ODECountProductsTool -- integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestODECountProductsIntegration:
    """Integration tests for ODECountProductsTool against the real ODE REST API."""

    async def test_count_mars_hirise(self):
        """Count Mars MRO HIRISE RDRV11 returns a positive count."""
        tool = ODECountProductsTool()
        result = await tool.arun(
            ODECountProductsInputSchema(
                target="mars",
                ihid="MRO",
                iid="HIRISE",
                pt="RDRV11",
            )
        )

        assert isinstance(result, ODECountProductsOutputSchema)
        assert result.status == "success"
        assert result.count > 0

    async def test_count_moon_lroc(self):
        """Count Moon LRO LROC EDR returns a positive count."""
        tool = ODECountProductsTool()
        result = await tool.arun(
            ODECountProductsInputSchema(
                target="moon",
                ihid="LRO",
                iid="LROC",
                pt="EDR",
            )
        )

        assert isinstance(result, ODECountProductsOutputSchema)
        assert result.status == "success"
        assert result.count > 0


# ---------------------------------------------------------------------------
# ODEListInstrumentsTool -- integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestODEListInstrumentsIntegration:
    """Integration tests for ODEListInstrumentsTool against the real ODE REST API."""

    async def test_list_mars_instruments(self):
        """Listing Mars instruments returns a substantial set including MRO HIRISE."""
        tool = ODEListInstrumentsTool()
        result = await tool.arun(
            ODEListInstrumentsInputSchema(target="mars")
        )

        assert isinstance(result, ODEListInstrumentsOutputSchema)
        assert result.status == "success"
        assert result.count > 5

        # MRO HIRISE should be among the known instruments
        ihid_iid_pairs = {(inst.ihid, inst.iid) for inst in result.instruments}
        assert ("MRO", "HIRISE") in ihid_iid_pairs

    async def test_list_moon_instruments(self):
        """Listing Moon instruments returns results."""
        tool = ODEListInstrumentsTool()
        result = await tool.arun(
            ODEListInstrumentsInputSchema(target="moon")
        )

        assert result.status == "success"
        assert result.count > 0

    async def test_list_instruments_with_ihid_filter(self):
        """Filtering Mars instruments by ihid='MRO' returns only MRO instruments."""
        tool = ODEListInstrumentsTool()
        result = await tool.arun(
            ODEListInstrumentsInputSchema(target="mars", ihid="MRO")
        )

        assert result.status == "success"
        assert result.count > 0
        for inst in result.instruments:
            assert inst.ihid == "MRO"


# ---------------------------------------------------------------------------
# ODEListFeatureClassesTool -- integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestODEListFeatureClassesIntegration:
    """Integration tests for ODEListFeatureClassesTool against the real ODE REST API."""

    async def test_list_mars_feature_classes(self):
        """Listing Mars feature classes includes 'crater'."""
        tool = ODEListFeatureClassesTool()
        result = await tool.arun(
            ODEListFeatureClassesInputSchema(target="mars")
        )

        assert isinstance(result, ODEListFeatureClassesOutputSchema)
        assert result.status == "success"
        assert result.count > 0

        # Normalize to lowercase for comparison
        lowercase_classes = [fc.lower() for fc in result.feature_classes]
        assert "crater" in lowercase_classes

    async def test_list_moon_feature_classes(self):
        """Listing Moon feature classes returns results."""
        tool = ODEListFeatureClassesTool()
        result = await tool.arun(
            ODEListFeatureClassesInputSchema(target="moon")
        )

        assert result.status == "success"
        assert result.count > 0


# ---------------------------------------------------------------------------
# ODEListFeatureNamesTool -- integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestODEListFeatureNamesIntegration:
    """Integration tests for ODEListFeatureNamesTool against the real ODE REST API."""

    async def test_list_mars_craters(self):
        """Listing Mars craters returns known craters like Gale or Jezero."""
        tool = ODEListFeatureNamesTool()
        result = await tool.arun(
            ODEListFeatureNamesInputSchema(
                target="mars",
                feature_class="crater",
                limit=50,
            )
        )

        assert isinstance(result, ODEListFeatureNamesOutputSchema)
        assert result.status == "success"
        assert result.count > 0

        # At least one of the well-known craters should appear
        feature_names_lower = [name.lower() for name in result.feature_names]
        known_craters = {"gale", "jezero"}
        assert known_craters & set(feature_names_lower), (
            f"Expected at least one of {known_craters} in feature names, got: {result.feature_names[:10]}"
        )


# ---------------------------------------------------------------------------
# ODEGetFeatureBoundsTool -- integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestODEGetFeatureBoundsIntegration:
    """Integration tests for ODEGetFeatureBoundsTool against the real ODE REST API."""

    async def test_get_gale_crater_bounds(self):
        """Getting bounds for Gale crater returns reasonable coordinates."""
        tool = ODEGetFeatureBoundsTool()
        result = await tool.arun(
            ODEGetFeatureBoundsInputSchema(
                target="mars",
                feature_class="crater",
                feature_name="Gale",
            )
        )

        assert isinstance(result, ODEGetFeatureBoundsOutputSchema)
        assert result.status == "success"
        assert result.bounds is not None

        # Gale crater is approximately at -5.4 lat, 137.8 lon
        assert -10 < result.bounds["min_lat"] < 0
        assert -10 < result.bounds["max_lat"] < 5
        assert 130 < result.bounds["west_lon"] < 145
        assert 130 < result.bounds["east_lon"] < 145

    async def test_get_nonexistent_feature(self):
        """Getting bounds for a nonexistent feature returns not_found status."""
        tool = ODEGetFeatureBoundsTool()
        result = await tool.arun(
            ODEGetFeatureBoundsInputSchema(
                target="mars",
                feature_class="crater",
                feature_name="NonexistentXYZ123",
            )
        )

        assert isinstance(result, ODEGetFeatureBoundsOutputSchema)
        assert result.status == "not_found"
