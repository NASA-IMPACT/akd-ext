"""Integration tests for PDS Catalog tools using the actual scraped dataset."""

import pytest

from akd_ext.tools.pds.pds_catalog.get_dataset import (
    PDSCatalogGetDatasetInputSchema,
    PDSCatalogGetDatasetOutputSchema,
    PDSCatalogGetDatasetTool,
)
from akd_ext.tools.pds.pds_catalog.list_missions import (
    PDSCatalogListMissionsInputSchema,
    PDSCatalogListMissionsOutputSchema,
    PDSCatalogListMissionsTool,
    PDSCatalogMissionItem,
)
from akd_ext.tools.pds.pds_catalog.list_targets import (
    PDSCatalogListTargetsInputSchema,
    PDSCatalogListTargetsOutputSchema,
    PDSCatalogListTargetsTool,
    PDSCatalogTargetItem,
)
from akd_ext.tools.pds.pds_catalog.search import (
    PDSCatalogSearchInputSchema,
    PDSCatalogSearchOutputSchema,
    PDSCatalogSearchTool,
)
from akd_ext.tools.pds.pds_catalog.stats import (
    PDSCatalogStatsInputSchema,
    PDSCatalogStatsOutputSchema,
    PDSCatalogStatsTool,
)


# ---------------------------------------------------------------------------
# PDSCatalogSearchTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDSCatalogSearchIntegration:
    """Integration tests for PDSCatalogSearchTool against real catalog data."""

    async def test_search_no_filters(self):
        """Unfiltered search returns datasets from the catalog."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(PDSCatalogSearchInputSchema(limit=5))

        assert isinstance(result, PDSCatalogSearchOutputSchema)
        assert result.status == "success"
        assert result.count > 0
        assert result.total > 0
        assert len(result.datasets) <= 5

    async def test_search_by_node(self):
        """Filtering by node returns datasets only from that node."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(PDSCatalogSearchInputSchema(node="ppi", limit=10))

        assert result.status == "success"
        assert result.count > 0
        for ds in result.datasets:
            assert ds["node"] == "ppi"

    async def test_search_by_mission_voyager(self):
        """Searching by mission 'Voyager' finds Voyager datasets."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(PDSCatalogSearchInputSchema(mission="Voyager", limit=10, fields="summary"))

        assert result.status == "success"
        assert result.count > 0
        for ds in result.datasets:
            title_lower = ds.get("title", "").lower()
            missions_lower = [m.lower() for m in ds.get("missions", [])]
            ds_id_lower = ds.get("id", "").lower()
            assert (
                any("voyager" in m for m in missions_lower)
                or "voyager" in title_lower
                or "vg1" in ds_id_lower
                or "vg2" in ds_id_lower
            ), f"Dataset {ds.get('id')} does not appear to be a Voyager dataset"

    async def test_search_by_target_mars(self):
        """Searching by target 'Mars' finds Mars datasets."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(PDSCatalogSearchInputSchema(target="Mars", limit=10, fields="summary"))

        assert result.status == "success"
        assert result.count > 0
        for ds in result.datasets:
            targets_lower = [t.lower() for t in ds.get("targets", [])]
            assert any("mars" in t for t in targets_lower), f"Dataset {ds.get('id')} does not target Mars"

    async def test_search_by_pds_version_pds4(self):
        """Filtering by PDS4 returns only PDS4 datasets."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(PDSCatalogSearchInputSchema(pds_version="PDS4", limit=10, fields="summary"))

        assert result.status == "success"
        assert result.count > 0
        for ds in result.datasets:
            assert ds["pds_version"] == "PDS4"

    async def test_search_by_pds_version_pds3(self):
        """Filtering by PDS3 returns only PDS3 datasets."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(PDSCatalogSearchInputSchema(pds_version="PDS3", limit=10, fields="summary"))

        assert result.status == "success"
        assert result.count > 0
        for ds in result.datasets:
            assert ds["pds_version"] == "PDS3"

    async def test_search_by_dataset_type_bundle(self):
        """Filtering by dataset type 'bundle' returns only bundles."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(PDSCatalogSearchInputSchema(dataset_type="bundle", limit=10, fields="summary"))

        assert result.status == "success"
        assert result.count > 0
        for ds in result.datasets:
            assert ds["type"] == "bundle"

    async def test_search_by_dataset_type_volume(self):
        """Filtering by dataset type 'volume' returns only PDS3 volumes."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(
            PDSCatalogSearchInputSchema(dataset_type="volume", limit=10, fields="summary")
        )

        assert result.status == "success"
        assert result.count > 0
        for ds in result.datasets:
            assert ds["type"] == "volume"
            assert ds["pds_version"] == "PDS3"

    async def test_search_with_text_query(self):
        """Text query search returns relevant results."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(PDSCatalogSearchInputSchema(query="plasma wave", limit=10))

        assert result.status == "success"
        assert result.count > 0

    async def test_search_with_date_filter(self):
        """Date-filtered search narrows to datasets overlapping the range."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(
            PDSCatalogSearchInputSchema(
                start_date="2020-01-01",
                stop_date="2025-12-31",
                limit=10,
                fields="full",
            )
        )

        assert result.status == "success"
        assert result.count > 0
        for ds in result.datasets:
            # If the dataset has dates, verify temporal overlap
            if ds.get("stop_date"):
                assert ds["stop_date"] >= "2020-01-01"
            if ds.get("start_date"):
                assert ds["start_date"] <= "2025-12-31"

    async def test_search_combined_node_and_mission(self):
        """Combining node + mission filters narrows results correctly."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(
            PDSCatalogSearchInputSchema(node="ppi", mission="Juno", limit=10, fields="summary")
        )

        assert result.status == "success"
        assert result.count > 0
        for ds in result.datasets:
            assert ds["node"] == "ppi"

    async def test_search_pagination(self):
        """Pagination returns different pages of results."""
        tool = PDSCatalogSearchTool()

        page1 = await tool.arun(PDSCatalogSearchInputSchema(limit=5, offset=0))
        page2 = await tool.arun(PDSCatalogSearchInputSchema(limit=5, offset=5))

        assert page1.status == "success"
        assert page2.status == "success"

        page1_ids = {ds["id"] for ds in page1.datasets}
        page2_ids = {ds["id"] for ds in page2.datasets}
        # Pages should contain different datasets
        assert page1_ids.isdisjoint(page2_ids), "Paginated pages should not overlap"

    async def test_search_essential_fields_profile(self):
        """Essential fields profile returns only minimal fields."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(PDSCatalogSearchInputSchema(limit=3, fields="essential"))

        assert result.fields == "essential"
        for ds in result.datasets:
            assert "id" in ds
            assert "title" in ds
            assert "node" in ds
            assert "browse_url" in ds
            # These should NOT be present in essential
            assert "description" not in ds

    async def test_search_full_fields_profile(self):
        """Full fields profile returns extended metadata."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(
            PDSCatalogSearchInputSchema(target="Mars", limit=3, fields="full")
        )

        assert result.fields == "full"
        for ds in result.datasets:
            assert "id" in ds
            assert "title" in ds
            assert "node" in ds
            # Full profile includes additional fields when populated
            assert "targets" in ds

    async def test_search_no_results(self):
        """Obscure query returns zero results gracefully."""
        tool = PDSCatalogSearchTool()
        result = await tool.arun(
            PDSCatalogSearchInputSchema(query="xyznonexistent123456", limit=5)
        )

        assert result.status == "success"
        assert result.count == 0
        assert result.datasets == []
        assert result.has_more is False


# ---------------------------------------------------------------------------
# PDSCatalogGetDatasetTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDSCatalogGetDatasetIntegration:
    """Integration tests for PDSCatalogGetDatasetTool against real catalog data."""

    async def test_get_pds4_dataset_by_lidvid(self):
        """Retrieve a known PDS4 bundle by its LIDVID."""
        tool = PDSCatalogGetDatasetTool()
        result = await tool.arun(
            PDSCatalogGetDatasetInputSchema(dataset_id="urn:nasa:pds:mars2020_mission::4.0")
        )

        assert isinstance(result, PDSCatalogGetDatasetOutputSchema)
        assert result.status == "success"
        assert result.dataset is not None
        assert result.error is None
        assert result.dataset["id"] == "urn:nasa:pds:mars2020_mission::4.0"
        assert "Mars" in result.dataset["title"] or "mars" in result.dataset["title"].lower()
        assert result.dataset["pds_version"] == "PDS4"
        assert result.dataset["type"] == "bundle"
        assert result.dataset["node"] == "geo"

    async def test_get_pds3_dataset_by_volume_id(self):
        """Retrieve a known PDS3 volume by its VOLUME_ID."""
        tool = PDSCatalogGetDatasetTool()
        result = await tool.arun(
            PDSCatalogGetDatasetInputSchema(dataset_id="CO-S-ISSNA/ISSWA-5-MIDR-V1.0")
        )

        assert result.status == "success"
        assert result.dataset is not None
        assert result.dataset["id"] == "CO-S-ISSNA/ISSWA-5-MIDR-V1.0"
        assert result.dataset["pds_version"] == "PDS3"
        assert result.dataset["type"] == "volume"
        assert result.dataset["node"] == "img"

    async def test_get_dataset_returns_full_fields(self):
        """Retrieved dataset includes all full-profile fields when present."""
        tool = PDSCatalogGetDatasetTool()
        result = await tool.arun(
            PDSCatalogGetDatasetInputSchema(dataset_id="urn:nasa:pds:mars2020_mission::4.0")
        )

        ds = result.dataset
        assert "id" in ds
        assert "title" in ds
        assert "node" in ds
        assert "pds_version" in ds
        assert "type" in ds
        assert "browse_url" in ds
        assert "source_url" in ds
        # Populated optional fields for this dataset
        assert "targets" in ds
        assert "missions" in ds
        assert "instruments" in ds

    async def test_get_nonexistent_dataset(self):
        """Non-existent dataset ID returns not_found."""
        tool = PDSCatalogGetDatasetTool()
        result = await tool.arun(
            PDSCatalogGetDatasetInputSchema(dataset_id="urn:nasa:pds:totally_fake::99.99")
        )

        assert result.status == "not_found"
        assert result.dataset is None
        assert result.error is not None


# ---------------------------------------------------------------------------
# PDSCatalogListMissionsTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDSCatalogListMissionsIntegration:
    """Integration tests for PDSCatalogListMissionsTool against real catalog data."""

    async def test_list_all_missions(self):
        """Listing missions without filters returns many missions."""
        tool = PDSCatalogListMissionsTool()
        result = await tool.arun(PDSCatalogListMissionsInputSchema())

        assert isinstance(result, PDSCatalogListMissionsOutputSchema)
        assert result.status == "success"
        assert result.count > 10  # The catalog has 176 unique missions
        for mission in result.missions:
            assert isinstance(mission, PDSCatalogMissionItem)
            assert mission.name
            assert mission.count > 0
            assert len(mission.nodes) > 0

    async def test_list_missions_filtered_by_node(self):
        """Filtering by node only returns missions with data at that node."""
        tool = PDSCatalogListMissionsTool()
        result = await tool.arun(PDSCatalogListMissionsInputSchema(node="ppi"))

        assert result.status == "success"
        assert result.count > 0
        for mission in result.missions:
            assert "ppi" in mission.nodes, f"Mission '{mission.name}' should have ppi in its nodes"

    async def test_list_missions_with_limit(self):
        """Limit caps the number of missions returned."""
        tool = PDSCatalogListMissionsTool()
        result = await tool.arun(PDSCatalogListMissionsInputSchema(limit=5))

        assert result.status == "success"
        assert result.count <= 5
        assert len(result.missions) <= 5

    async def test_well_known_missions_present(self):
        """Well-known missions exist in the catalog (filtered by ppi node)."""
        tool = PDSCatalogListMissionsTool()
        # Use ppi node where Voyager 1/2 are known to exist
        result = await tool.arun(PDSCatalogListMissionsInputSchema(node="ppi"))

        mission_names_lower = [m.name.lower() for m in result.missions]
        assert any("voyager" in name for name in mission_names_lower), (
            f"Expected a Voyager mission in ppi node, got: {mission_names_lower[:10]}"
        )


# ---------------------------------------------------------------------------
# PDSCatalogListTargetsTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDSCatalogListTargetsIntegration:
    """Integration tests for PDSCatalogListTargetsTool against real catalog data."""

    async def test_list_all_targets(self):
        """Listing targets without filters returns many targets."""
        tool = PDSCatalogListTargetsTool()
        result = await tool.arun(PDSCatalogListTargetsInputSchema())

        assert isinstance(result, PDSCatalogListTargetsOutputSchema)
        assert result.status == "success"
        assert result.count > 10  # The catalog has 4330 unique targets
        for target in result.targets:
            assert isinstance(target, PDSCatalogTargetItem)
            assert target.name
            assert target.count > 0
            assert len(target.nodes) > 0

    async def test_list_targets_filtered_by_node(self):
        """Filtering by node only returns targets at that node."""
        tool = PDSCatalogListTargetsTool()
        result = await tool.arun(PDSCatalogListTargetsInputSchema(node="rms"))

        assert result.status == "success"
        assert result.count > 0
        for target in result.targets:
            assert "rms" in target.nodes, f"Target '{target.name}' should have rms in its nodes"

    async def test_list_targets_with_limit(self):
        """Limit caps the number of targets returned."""
        tool = PDSCatalogListTargetsTool()
        result = await tool.arun(PDSCatalogListTargetsInputSchema(limit=10))

        assert result.status == "success"
        assert result.count <= 10
        assert len(result.targets) <= 10

    async def test_well_known_targets_present(self):
        """Well-known celestial bodies exist in the catalog (via search)."""
        # list_targets is capped at 50 and sorted alphabetically, so well-known
        # targets like "Mars" or "Saturn" may not appear in the first page.
        # Instead, verify via the search tool which uses target as a filter.
        search_tool = PDSCatalogSearchTool()
        result = await search_tool.arun(
            PDSCatalogSearchInputSchema(target="Saturn", limit=1, fields="summary")
        )
        assert result.count > 0, "Expected datasets targeting Saturn in the catalog"
        assert any("saturn" in t.lower() for t in result.datasets[0].get("targets", []))


# ---------------------------------------------------------------------------
# PDSCatalogStatsTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPDSCatalogStatsIntegration:
    """Integration tests for PDSCatalogStatsTool against real catalog data."""

    async def test_stats_returns_totals(self):
        """Stats tool returns non-zero totals from the real catalog."""
        tool = PDSCatalogStatsTool()
        result = await tool.arun(PDSCatalogStatsInputSchema())

        assert isinstance(result, PDSCatalogStatsOutputSchema)
        assert result.status == "success"
        assert result.total_datasets > 1000  # Catalog has 12631 datasets
        assert result.missions_count > 10
        assert result.targets_count > 100

    async def test_stats_by_node(self):
        """Stats include breakdowns by node covering all 7 PDS nodes."""
        tool = PDSCatalogStatsTool()
        result = await tool.arun(PDSCatalogStatsInputSchema())

        expected_nodes = {"atm", "geo", "img", "naif", "ppi", "rms", "sbn"}
        assert expected_nodes == set(result.by_node.keys())
        for node, count in result.by_node.items():
            assert count > 0, f"Node '{node}' should have at least one dataset"

    async def test_stats_by_pds_version(self):
        """Stats include breakdowns by PDS version (PDS3 and PDS4)."""
        tool = PDSCatalogStatsTool()
        result = await tool.arun(PDSCatalogStatsInputSchema())

        assert "PDS3" in result.by_pds_version
        assert "PDS4" in result.by_pds_version
        assert result.by_pds_version["PDS3"] > 0
        assert result.by_pds_version["PDS4"] > 0
        assert result.by_pds_version["PDS3"] + result.by_pds_version["PDS4"] == result.total_datasets

    async def test_stats_by_type(self):
        """Stats include breakdowns by dataset type."""
        tool = PDSCatalogStatsTool()
        result = await tool.arun(PDSCatalogStatsInputSchema())

        expected_types = {"volume", "bundle", "collection"}
        assert expected_types == set(result.by_type.keys())
        total_by_type = sum(result.by_type.values())
        assert total_by_type == result.total_datasets

    async def test_stats_consistency(self):
        """Node counts sum to total_datasets."""
        tool = PDSCatalogStatsTool()
        result = await tool.arun(PDSCatalogStatsInputSchema())

        total_by_node = sum(result.by_node.values())
        assert total_by_node == result.total_datasets
