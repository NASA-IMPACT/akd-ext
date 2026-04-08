"""Integration tests for IMG Atlas tools using the actual IMG Atlas API."""

import pytest

from akd_ext.tools.pds.img.search import (
    IMGSearchInputSchema,
    IMGSearchOutputSchema,
    IMGSearchTool,
)
from akd_ext.tools.pds.img.count import (
    IMGCountInputSchema,
    IMGCountOutputSchema,
    IMGCountTool,
)
from akd_ext.tools.pds.img.get_facets import (
    IMGGetFacetsInputSchema,
    IMGGetFacetsOutputSchema,
    IMGGetFacetsTool,
)


# ---------------------------------------------------------------------------
# IMGSearchTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestIMGSearchIntegration:
    """Integration tests for IMGSearchTool against the real IMG Atlas API."""

    async def test_search_mars_images(self):
        """Search for Mars images returns results."""
        tool = IMGSearchTool()
        result = await tool.arun(IMGSearchInputSchema(target="Mars", rows=5))

        assert isinstance(result, IMGSearchOutputSchema)
        assert result.status == "success"
        assert result.num_found > 0
        assert len(result.products) <= 5
        for product in result.products:
            assert product.target == "Mars"

    async def test_search_by_mission(self):
        """Search by mission returns matching results."""
        tool = IMGSearchTool()
        result = await tool.arun(
            IMGSearchInputSchema(mission="MARS SCIENCE LABORATORY", rows=5)
        )

        assert result.status == "success"
        assert result.num_found > 0
        for product in result.products:
            assert product.mission == "MARS SCIENCE LABORATORY"

    async def test_search_by_instrument(self):
        """Search by instrument returns matching results."""
        tool = IMGSearchTool()
        result = await tool.arun(
            IMGSearchInputSchema(target="Mars", instrument="MASTCAM", rows=5)
        )

        assert result.status == "success"
        assert result.num_found > 0
        for product in result.products:
            assert product.instrument == "MASTCAM"

    async def test_search_by_product_type(self):
        """Search by product type filters correctly."""
        tool = IMGSearchTool()
        result = await tool.arun(
            IMGSearchInputSchema(target="Mars", product_type="EDR", rows=5)
        )

        assert result.status == "success"
        assert result.num_found > 0
        for product in result.products:
            assert product.product_type == "EDR"

    async def test_search_pagination(self):
        """Pagination returns different pages of results."""
        tool = IMGSearchTool()

        page1 = await tool.arun(IMGSearchInputSchema(target="Mars", rows=5, start=0))
        page2 = await tool.arun(IMGSearchInputSchema(target="Mars", rows=5, start=5))

        assert page1.status == "success"
        assert page2.status == "success"

        page1_uuids = {p.uuid for p in page1.products}
        page2_uuids = {p.uuid for p in page2.products}
        assert page1_uuids.isdisjoint(page2_uuids), "Paginated pages should not overlap"

    async def test_search_saturn_cassini(self):
        """Search for Cassini Saturn images."""
        tool = IMGSearchTool()
        result = await tool.arun(
            IMGSearchInputSchema(target="Saturn", mission="CASSINI-HUYGENS", rows=5)
        )

        assert result.status == "success"
        assert result.num_found > 0


# ---------------------------------------------------------------------------
# IMGCountTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestIMGCountIntegration:
    """Integration tests for IMGCountTool against the real IMG Atlas API."""

    async def test_count_mars_images(self):
        """Count Mars images returns large count."""
        tool = IMGCountTool()
        result = await tool.arun(IMGCountInputSchema(target="Mars"))

        assert isinstance(result, IMGCountOutputSchema)
        assert result.status == "success"
        assert result.count > 1000

    async def test_count_by_mission_and_instrument(self):
        """Count by mission + instrument returns results."""
        tool = IMGCountTool()
        result = await tool.arun(
            IMGCountInputSchema(
                mission="MARS SCIENCE LABORATORY",
                instrument="MASTCAM",
            )
        )

        assert result.status == "success"
        assert result.count > 0

    async def test_count_by_product_type(self):
        """Count EDR products returns results."""
        tool = IMGCountTool()
        result = await tool.arun(
            IMGCountInputSchema(target="Mars", product_type="EDR")
        )

        assert result.status == "success"
        assert result.count > 0


# ---------------------------------------------------------------------------
# IMGGetFacetsTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestIMGGetFacetsIntegration:
    """Integration tests for IMGGetFacetsTool against the real IMG Atlas API."""

    async def test_get_target_facets(self):
        """Get TARGET facets returns known targets."""
        tool = IMGGetFacetsTool()
        result = await tool.arun(IMGGetFacetsInputSchema(facet_field="TARGET"))

        assert isinstance(result, IMGGetFacetsOutputSchema)
        assert result.status == "success"
        assert result.count > 0
        target_names = [v.value for v in result.values]
        assert "Mars" in target_names

    async def test_get_mission_facets(self):
        """Get ATLAS_MISSION_NAME facets returns known missions."""
        tool = IMGGetFacetsTool()
        result = await tool.arun(
            IMGGetFacetsInputSchema(facet_field="ATLAS_MISSION_NAME")
        )

        assert result.status == "success"
        assert result.count > 0
        mission_names = [v.value for v in result.values]
        assert "MARS SCIENCE LABORATORY" in mission_names

    async def test_get_instrument_facets_filtered_by_target(self):
        """Get instrument facets filtered by target."""
        tool = IMGGetFacetsTool()
        result = await tool.arun(
            IMGGetFacetsInputSchema(
                facet_field="ATLAS_INSTRUMENT_NAME",
                target="Mars",
            )
        )

        assert result.status == "success"
        assert result.count > 0
        instrument_names = [v.value for v in result.values]
        assert "MASTCAM" in instrument_names
