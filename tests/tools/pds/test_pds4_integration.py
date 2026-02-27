"""Integration tests for PDS4 Registry tools using the real PDS4 API."""

import pytest

from akd_ext.tools.pds.pds4.search_bundles import (
    PDS4SearchBundlesInputSchema,
    PDS4SearchBundlesOutputSchema,
    PDS4SearchBundlesTool,
)
from akd_ext.tools.pds.pds4.search_products import (
    PDS4SearchProductsInputSchema,
    PDS4SearchProductsOutputSchema,
    PDS4SearchProductsTool,
)
from akd_ext.tools.pds.pds4.search_collections import (
    PDS4SearchCollectionsInputSchema,
    PDS4SearchCollectionsOutputSchema,
    PDS4SearchCollectionsTool,
)
from akd_ext.tools.pds.pds4.search_investigations import (
    PDS4SearchInvestigationsInputSchema,
    PDS4SearchInvestigationsOutputSchema,
    PDS4SearchInvestigationsTool,
)
from akd_ext.tools.pds.pds4.search_targets import (
    PDS4SearchTargetsInputSchema,
    PDS4SearchTargetsOutputSchema,
    PDS4SearchTargetsTool,
)
from akd_ext.tools.pds.pds4.search_instrument_hosts import (
    PDS4SearchInstrumentHostsInputSchema,
    PDS4SearchInstrumentHostsOutputSchema,
    PDS4SearchInstrumentHostsTool,
)
from akd_ext.tools.pds.pds4.search_instruments import (
    PDS4SearchInstrumentsInputSchema,
    PDS4SearchInstrumentsOutputSchema,
    PDS4SearchInstrumentsTool,
)
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


# ---------------------------------------------------------------------------
# PDS4SearchBundlesTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDS4SearchBundlesIntegration:
    """Integration tests for PDS4SearchBundlesTool against the real PDS4 API."""

    async def test_search_all_bundles(self):
        """Search with limit=5 returns bundles and a positive total_hits."""
        tool = PDS4SearchBundlesTool()
        result = await tool.arun(PDS4SearchBundlesInputSchema(limit=5))

        assert isinstance(result, PDS4SearchBundlesOutputSchema)
        assert result.total_hits > 0
        assert len(result.bundles) <= 5
        assert len(result.bundles) > 0
        for bundle in result.bundles:
            assert bundle.id

    async def test_search_bundles_by_title(self):
        """Search with title_query='Mars' returns Mars-related bundles."""
        tool = PDS4SearchBundlesTool()
        result = await tool.arun(PDS4SearchBundlesInputSchema(title_query="Mars", limit=5))

        assert result.total_hits > 0
        assert len(result.bundles) > 0
        # At least one bundle should have 'mars' in its title or id
        has_mars = any(
            "mars" in (bundle.title or "").lower() or "mars" in bundle.id.lower() for bundle in result.bundles
        )
        assert has_mars, f"Expected at least one Mars-related bundle, got: {[b.title for b in result.bundles]}"

    async def test_search_bundles_facets_only(self):
        """Search with limit=0 and facet_fields returns facets without bundles."""
        tool = PDS4SearchBundlesTool()
        result = await tool.arun(
            PDS4SearchBundlesInputSchema(
                limit=0,
                facet_fields="pds:Identification_Area.pds:title",
            )
        )

        assert result.total_hits > 0
        assert len(result.bundles) == 0
        assert len(result.facets) > 0
        assert "pds:Identification_Area.pds:title" in result.facets


# ---------------------------------------------------------------------------
# PDS4SearchProductsTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDS4SearchProductsIntegration:
    """Integration tests for PDS4SearchProductsTool against the real PDS4 API."""

    async def test_search_products(self):
        """Search with keywords='Mars' returns products."""
        tool = PDS4SearchProductsTool()
        result = await tool.arun(PDS4SearchProductsInputSchema(keywords="Mars", limit=5))

        assert isinstance(result, PDS4SearchProductsOutputSchema)
        assert result.total_hits > 0
        assert len(result.products) <= 5
        assert len(result.products) > 0
        for product in result.products:
            assert product.id

    async def test_search_products_by_target(self):
        """Search by ref_lid_target for Mars returns Mars-related products."""
        tool = PDS4SearchProductsTool()
        result = await tool.arun(
            PDS4SearchProductsInputSchema(
                ref_lid_target="urn:nasa:pds:context:target:planet.mars",
                limit=5,
            )
        )

        assert isinstance(result, PDS4SearchProductsOutputSchema)
        assert result.total_hits > 0
        assert len(result.products) <= 5
        assert len(result.products) > 0


# ---------------------------------------------------------------------------
# PDS4SearchCollectionsTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDS4SearchCollectionsIntegration:
    """Integration tests for PDS4SearchCollectionsTool against the real PDS4 API."""

    async def test_search_all_collections(self):
        """Search with default params returns collections."""
        tool = PDS4SearchCollectionsTool()
        result = await tool.arun(PDS4SearchCollectionsInputSchema(limit=5))

        assert isinstance(result, PDS4SearchCollectionsOutputSchema)
        assert result.total_hits > 0
        assert len(result.collections) <= 5
        assert len(result.collections) > 0
        for collection in result.collections:
            assert collection.id

    async def test_search_collections_by_target(self):
        """Search by ref_lid_target for Mars returns Mars-related collections."""
        tool = PDS4SearchCollectionsTool()
        result = await tool.arun(
            PDS4SearchCollectionsInputSchema(
                ref_lid_target="urn:nasa:pds:context:target:planet.mars",
                limit=5,
            )
        )

        assert result.total_hits > 0
        assert len(result.collections) > 0


# ---------------------------------------------------------------------------
# PDS4SearchInvestigationsTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDS4SearchInvestigationsIntegration:
    """Integration tests for PDS4SearchInvestigationsTool against the real PDS4 API."""

    async def test_search_all_investigations(self):
        """Search with limit=5 returns investigations."""
        tool = PDS4SearchInvestigationsTool()
        result = await tool.arun(PDS4SearchInvestigationsInputSchema(limit=5))

        assert isinstance(result, PDS4SearchInvestigationsOutputSchema)
        assert result.total_hits > 0
        assert len(result.investigations) <= 5
        assert len(result.investigations) > 0
        for investigation in result.investigations:
            assert investigation.id

    async def test_search_investigations_by_keyword(self):
        """Search with keywords='Juno' returns Juno-related investigations."""
        tool = PDS4SearchInvestigationsTool()
        result = await tool.arun(PDS4SearchInvestigationsInputSchema(keywords="Juno", limit=5))

        assert result.total_hits > 0
        assert len(result.investigations) > 0
        # At least one investigation should be Juno-related
        has_juno = any(
            "juno" in (inv.title or "").lower() or "juno" in inv.id.lower() for inv in result.investigations
        )
        assert has_juno, (
            f"Expected at least one Juno-related investigation, got: {[i.title for i in result.investigations]}"
        )


# ---------------------------------------------------------------------------
# PDS4SearchTargetsTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDS4SearchTargetsIntegration:
    """Integration tests for PDS4SearchTargetsTool against the real PDS4 API."""

    async def test_search_all_targets(self):
        """Search with limit=5 returns targets."""
        tool = PDS4SearchTargetsTool()
        result = await tool.arun(PDS4SearchTargetsInputSchema(limit=5))

        assert isinstance(result, PDS4SearchTargetsOutputSchema)
        assert result.total_hits > 0
        assert len(result.targets) <= 5
        assert len(result.targets) > 0
        for target in result.targets:
            assert target.id

    async def test_search_targets_by_type(self):
        """Search with target_type='Planet' returns planet targets."""
        tool = PDS4SearchTargetsTool()
        result = await tool.arun(PDS4SearchTargetsInputSchema(target_type="Planet", limit=5))

        assert result.total_hits > 0
        assert len(result.targets) <= 5
        assert len(result.targets) > 0


# ---------------------------------------------------------------------------
# PDS4SearchInstrumentHostsTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDS4SearchInstrumentHostsIntegration:
    """Integration tests for PDS4SearchInstrumentHostsTool against the real PDS4 API."""

    async def test_search_all_instrument_hosts(self):
        """Search with limit=5 returns instrument hosts."""
        tool = PDS4SearchInstrumentHostsTool()
        result = await tool.arun(PDS4SearchInstrumentHostsInputSchema(limit=5))

        assert isinstance(result, PDS4SearchInstrumentHostsOutputSchema)
        assert result.total_hits > 0
        assert len(result.instrument_hosts) <= 5
        assert len(result.instrument_hosts) > 0
        for host in result.instrument_hosts:
            assert host.id

    async def test_search_instrument_hosts_by_type(self):
        """Search with instrument_host_type='Spacecraft' returns spacecraft hosts."""
        tool = PDS4SearchInstrumentHostsTool()
        result = await tool.arun(
            PDS4SearchInstrumentHostsInputSchema(instrument_host_type="Spacecraft", limit=5)
        )

        assert result.total_hits > 0
        assert len(result.instrument_hosts) > 0


# ---------------------------------------------------------------------------
# PDS4SearchInstrumentsTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDS4SearchInstrumentsIntegration:
    """Integration tests for PDS4SearchInstrumentsTool against the real PDS4 API."""

    async def test_search_all_instruments(self):
        """Search with limit=5 returns instruments."""
        tool = PDS4SearchInstrumentsTool()
        result = await tool.arun(PDS4SearchInstrumentsInputSchema(limit=5))

        assert isinstance(result, PDS4SearchInstrumentsOutputSchema)
        assert result.total_hits > 0
        assert len(result.instruments) <= 5
        assert len(result.instruments) > 0
        for instrument in result.instruments:
            assert instrument.id

    async def test_search_instruments_by_type(self):
        """Search with instrument_type='Imager' returns imager instruments."""
        tool = PDS4SearchInstrumentsTool()
        result = await tool.arun(PDS4SearchInstrumentsInputSchema(instrument_type="Imager", limit=5))

        assert result.total_hits > 0
        assert len(result.instruments) <= 5
        assert len(result.instruments) > 0


# ---------------------------------------------------------------------------
# PDS4CrawlContextProductTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDS4CrawlContextProductIntegration:
    """Integration tests for PDS4CrawlContextProductTool against the real PDS4 API."""

    async def test_crawl_investigation(self):
        """Crawling the Juno investigation returns associated context products."""
        tool = PDS4CrawlContextProductTool()
        result = await tool.arun(
            PDS4CrawlContextProductInputSchema(urn="urn:nasa:pds:context:investigation:mission.juno")
        )

        assert isinstance(result, PDS4CrawlContextProductOutputSchema)
        # Juno should have associated targets and/or observing system components
        has_related = (
            len(result.targets) > 0 or len(result.observing_system_components) > 0 or len(result.investigations) > 0
        )
        assert has_related, "Expected Juno investigation to have related context products"


# ---------------------------------------------------------------------------
# PDS4GetProductTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDS4GetProductIntegration:
    """Integration tests for PDS4GetProductTool against the real PDS4 API."""

    async def test_get_known_product(self):
        """Get the Juno investigation product by URN returns a populated product dict."""
        tool = PDS4GetProductTool()
        result = await tool.arun(
            PDS4GetProductInputSchema(urn="urn:nasa:pds:context:investigation:mission.juno")
        )

        assert isinstance(result, PDS4GetProductOutputSchema)
        assert isinstance(result.product, dict)
        assert len(result.product) > 0

    async def test_get_target_product(self):
        """Get the Mars target product by URN returns a populated product dict."""
        tool = PDS4GetProductTool()
        result = await tool.arun(
            PDS4GetProductInputSchema(urn="urn:nasa:pds:context:target:planet.mars")
        )

        assert isinstance(result, PDS4GetProductOutputSchema)
        assert isinstance(result.product, dict)
        assert len(result.product) > 0
