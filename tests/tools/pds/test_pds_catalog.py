"""Unit tests for PDS Catalog tools."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from akd_ext.tools.pds.pds_catalog.get_dataset import (
    PDSCatalogGetDatasetInputSchema,
    PDSCatalogGetDatasetOutputSchema,
    PDSCatalogGetDatasetTool,
    PDSCatalogGetDatasetToolConfig,
)
from akd_ext.tools.pds.pds_catalog.list_missions import (
    PDSCatalogListMissionsInputSchema,
    PDSCatalogListMissionsOutputSchema,
    PDSCatalogListMissionsTool,
    PDSCatalogListMissionsToolConfig,
    PDSCatalogMissionItem,
)
from akd_ext.tools.pds.pds_catalog.list_targets import (
    PDSCatalogListTargetsInputSchema,
    PDSCatalogListTargetsOutputSchema,
    PDSCatalogListTargetsTool,
    PDSCatalogListTargetsToolConfig,
    PDSCatalogTargetItem,
)
from akd_ext.tools.pds.pds_catalog.search import (
    PDSCatalogSearchInputSchema,
    PDSCatalogSearchOutputSchema,
    PDSCatalogSearchTool,
    PDSCatalogSearchToolConfig,
)
from akd_ext.tools.pds.pds_catalog.stats import (
    PDSCatalogStatsInputSchema,
    PDSCatalogStatsOutputSchema,
    PDSCatalogStatsTool,
    PDSCatalogStatsToolConfig,
)
from akd_ext.tools.pds.utils.pds_catalog_api_models import DatasetType, PDSDataset, PDSNode, PDSVersion
from akd_ext.tools.pds.utils.pds_catalog_client import PDSCatalogClientError

# Patch paths – must match where PDSCatalogClient is looked up at runtime
_SEARCH_CLIENT = "akd_ext.tools.pds.pds_catalog.search.PDSCatalogClient"
_GET_DATASET_CLIENT = "akd_ext.tools.pds.pds_catalog.get_dataset.PDSCatalogClient"
_LIST_MISSIONS_CLIENT = "akd_ext.tools.pds.pds_catalog.list_missions.PDSCatalogClient"
_LIST_TARGETS_CLIENT = "akd_ext.tools.pds.pds_catalog.list_targets.PDSCatalogClient"
_STATS_CLIENT = "akd_ext.tools.pds.pds_catalog.stats.PDSCatalogClient"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_dataset(**overrides) -> PDSDataset:
    """Helper to build a PDSDataset with sensible defaults."""
    defaults = {
        "id": "urn:nasa:pds:cassini_iss::1.0",
        "title": "Cassini ISS Images of Saturn",
        "description": "Images from the Cassini ISS camera",
        "node": PDSNode.IMG,
        "pds_version": PDSVersion.PDS4,
        "type": DatasetType.BUNDLE,
        "missions": ["Cassini"],
        "targets": ["Saturn"],
        "instruments": ["ISS"],
        "instrument_hosts": ["Cassini Orbiter"],
        "data_types": ["images"],
        "start_date": date(2004, 6, 30),
        "stop_date": date(2017, 9, 15),
        "browse_url": "https://pds.nasa.gov/browse/cassini_iss",
        "source_url": "https://pds.nasa.gov/source/cassini_iss",
        "keywords": ["saturn", "rings", "imaging"],
        "processing_level": "Raw",
    }
    defaults.update(overrides)
    return PDSDataset(**defaults)


@pytest.fixture
def sample_dataset():
    return _make_dataset()


@pytest.fixture
def sample_dataset_pds3():
    return _make_dataset(
        id="GO_0017",
        title="Galileo SSI Jupiter Images",
        description="Galileo SSI images of Jupiter",
        node=PDSNode.IMG,
        pds_version=PDSVersion.PDS3,
        type=DatasetType.VOLUME,
        missions=["Galileo"],
        targets=["Jupiter"],
        instruments=["SSI"],
        instrument_hosts=["Galileo Orbiter"],
        start_date=date(1996, 6, 1),
        stop_date=date(2003, 9, 21),
        browse_url="https://pds.nasa.gov/browse/GO_0017",
        source_url="https://pds.nasa.gov/source/GO_0017",
        keywords=["jupiter", "galileo"],
        processing_level="Calibrated",
    )


@pytest.fixture
def sample_datasets(sample_dataset, sample_dataset_pds3):
    return [sample_dataset, sample_dataset_pds3]


# ---------------------------------------------------------------------------
# PDSCatalogSearchTool
# ---------------------------------------------------------------------------


class TestPDSCatalogSearchTool:
    """Tests for PDSCatalogSearchTool."""

    async def test_basic_search(self, sample_datasets):
        """Search with no filters returns all datasets."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=(sample_datasets, 2))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema())

        assert isinstance(result, PDSCatalogSearchOutputSchema)
        assert result.status == "success"
        assert result.count == 2
        assert result.total == 2
        assert result.has_more is False
        assert len(result.datasets) == 2

    async def test_search_with_query(self, sample_dataset):
        """Search with a text query is forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(query="cassini saturn"))

        mock_client.search.assert_called_once()
        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["query"] == "cassini saturn"
        assert result.count == 1

    async def test_search_with_node_filter(self, sample_dataset):
        """Search with node filter passes node to client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(node="img"))

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["node"] == "img"
        assert result.status == "success"

    async def test_search_with_mission_filter(self, sample_dataset):
        """Search with mission filter passes mission to client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(mission="Cassini"))

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["mission"] == "Cassini"
        assert result.count == 1

    async def test_search_with_target_filter(self, sample_dataset):
        """Search with target filter passes target to client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(target="Saturn"))

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["target"] == "Saturn"

    async def test_search_with_instrument_filter(self, sample_dataset):
        """Search with instrument filter passes instrument to client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(instrument="ISS"))

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["instrument"] == "ISS"

    async def test_search_with_pds_version_filter(self, sample_dataset):
        """Search with PDS version filter passes pds_version to client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(pds_version="PDS4"))

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["pds_version"] == "PDS4"

    async def test_search_with_dataset_type_filter(self, sample_dataset):
        """Search with dataset type filter passes dataset_type to client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(dataset_type="bundle"))

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["dataset_type"] == "bundle"

    async def test_search_with_date_filters(self, sample_dataset):
        """Search with date filters parses ISO strings and passes date objects."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(
                PDSCatalogSearchInputSchema(
                    start_date="2005-01-01",
                    stop_date="2010-12-31",
                )
            )

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["start_date"] == date(2005, 1, 1)
        assert call_kwargs["stop_date"] == date(2010, 12, 31)

    async def test_search_invalid_date_raises_value_error(self):
        """Invalid date format raises ValueError."""
        with patch(_SEARCH_CLIENT):
            tool = PDSCatalogSearchTool()
            with pytest.raises(ValueError, match="Invalid date format"):
                await tool.arun(PDSCatalogSearchInputSchema(start_date="not-a-date"))

    async def test_search_pagination(self, sample_dataset):
        """Pagination parameters (offset, limit) are forwarded and has_more computed."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            # Return 1 dataset but report 5 total to trigger has_more=True
            mock_client.search = AsyncMock(return_value=([sample_dataset], 5))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(limit=1, offset=0))

        assert result.count == 1
        assert result.total == 5
        assert result.limit == 1
        assert result.offset == 0
        assert result.has_more is True

    async def test_search_pagination_no_more(self, sample_datasets):
        """has_more is False when all results are returned."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=(sample_datasets, 2))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(limit=10, offset=0))

        assert result.has_more is False

    async def test_search_limit_capped_at_max(self, sample_datasets):
        """Limit exceeding MAX_RESULTS_LIMIT (50) is capped."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=(sample_datasets, 2))

            tool = PDSCatalogSearchTool()
            # Pydantic le=50 validation prevents >50, so test with exactly 50
            result = await tool.arun(PDSCatalogSearchInputSchema(limit=50))

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["limit"] == 50

    async def test_search_essential_fields(self, sample_dataset):
        """Essential field profile returns only id, title, node, browse_url."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(fields="essential"))

        assert result.fields == "essential"
        ds = result.datasets[0]
        assert "id" in ds
        assert "title" in ds
        assert "node" in ds
        assert "browse_url" in ds
        # Summary/full fields should not be present
        assert "missions" not in ds
        assert "description" not in ds

    async def test_search_summary_fields(self, sample_dataset):
        """Summary field profile includes essential + missions, targets, etc."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(fields="summary"))

        ds = result.datasets[0]
        assert "id" in ds
        assert "missions" in ds
        assert "targets" in ds
        assert "instruments" in ds
        assert "pds_version" in ds
        assert "type" in ds
        # Description only appears in full profile
        assert "description" not in ds

    async def test_search_full_fields(self, sample_dataset):
        """Full field profile includes description, dates, keywords, etc."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(fields="full"))

        ds = result.datasets[0]
        assert "id" in ds
        assert "description" in ds
        assert "start_date" in ds
        assert "stop_date" in ds
        assert "keywords" in ds
        assert "processing_level" in ds

    async def test_search_empty_results(self):
        """Empty search results return count=0 and empty datasets list."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([], 0))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(PDSCatalogSearchInputSchema(query="nonexistent"))

        assert result.status == "success"
        assert result.count == 0
        assert result.total == 0
        assert result.datasets == []
        assert result.has_more is False

    async def test_search_catalog_client_error(self):
        """PDSCatalogClientError is re-raised."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(side_effect=PDSCatalogClientError("catalog broken"))

            tool = PDSCatalogSearchTool()
            with pytest.raises(PDSCatalogClientError, match="catalog broken"):
                await tool.arun(PDSCatalogSearchInputSchema())

    async def test_search_unexpected_error_wrapped(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(side_effect=TypeError("bad type"))

            tool = PDSCatalogSearchTool()
            with pytest.raises(RuntimeError, match="Internal error during catalog search"):
                await tool.arun(PDSCatalogSearchInputSchema())

    async def test_search_with_config(self, sample_dataset):
        """Custom catalog_dir config is passed to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            config = PDSCatalogSearchToolConfig(catalog_dir="/custom/path")
            tool = PDSCatalogSearchTool(config=config)
            await tool.arun(PDSCatalogSearchInputSchema())

        MockClient.assert_called_once_with(catalog_dir="/custom/path")

    async def test_search_all_filters_combined(self, sample_dataset):
        """All filters combined are forwarded to the client."""
        with patch(_SEARCH_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.search = AsyncMock(return_value=([sample_dataset], 1))

            tool = PDSCatalogSearchTool()
            result = await tool.arun(
                PDSCatalogSearchInputSchema(
                    query="saturn images",
                    node="img",
                    mission="Cassini",
                    instrument="ISS",
                    target="Saturn",
                    pds_version="PDS4",
                    dataset_type="bundle",
                    start_date="2005-01-01",
                    stop_date="2015-12-31",
                    limit=10,
                    offset=5,
                    fields="full",
                )
            )

        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["query"] == "saturn images"
        assert call_kwargs["node"] == "img"
        assert call_kwargs["mission"] == "Cassini"
        assert call_kwargs["instrument"] == "ISS"
        assert call_kwargs["target"] == "Saturn"
        assert call_kwargs["pds_version"] == "PDS4"
        assert call_kwargs["dataset_type"] == "bundle"
        assert call_kwargs["start_date"] == date(2005, 1, 1)
        assert call_kwargs["stop_date"] == date(2015, 12, 31)
        assert call_kwargs["limit"] == 10
        assert call_kwargs["offset"] == 5
        assert result.fields == "full"


# ---------------------------------------------------------------------------
# PDSCatalogGetDatasetTool
# ---------------------------------------------------------------------------


class TestPDSCatalogGetDatasetTool:
    """Tests for PDSCatalogGetDatasetTool."""

    async def test_get_dataset_found(self, sample_dataset):
        """Existing dataset returns success with full metadata."""
        with patch(_GET_DATASET_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_dataset = AsyncMock(return_value=sample_dataset)

            tool = PDSCatalogGetDatasetTool()
            result = await tool.arun(
                PDSCatalogGetDatasetInputSchema(dataset_id="urn:nasa:pds:cassini_iss::1.0")
            )

        assert isinstance(result, PDSCatalogGetDatasetOutputSchema)
        assert result.status == "success"
        assert result.dataset is not None
        assert result.error is None
        assert result.dataset["id"] == "urn:nasa:pds:cassini_iss::1.0"
        assert result.dataset["title"] == "Cassini ISS Images of Saturn"

    async def test_get_dataset_full_fields_returned(self, sample_dataset):
        """Dataset response uses the full field profile."""
        with patch(_GET_DATASET_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_dataset = AsyncMock(return_value=sample_dataset)

            tool = PDSCatalogGetDatasetTool()
            result = await tool.arun(
                PDSCatalogGetDatasetInputSchema(dataset_id="urn:nasa:pds:cassini_iss::1.0")
            )

        ds = result.dataset
        assert "id" in ds
        assert "title" in ds
        assert "description" in ds
        assert "missions" in ds
        assert "targets" in ds
        assert "instruments" in ds
        assert "start_date" in ds
        assert "stop_date" in ds
        assert "keywords" in ds
        assert "processing_level" in ds

    async def test_get_dataset_not_found(self):
        """Non-existent dataset returns not_found status."""
        with patch(_GET_DATASET_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_dataset = AsyncMock(return_value=None)

            tool = PDSCatalogGetDatasetTool()
            result = await tool.arun(
                PDSCatalogGetDatasetInputSchema(dataset_id="nonexistent_id")
            )

        assert result.status == "not_found"
        assert result.dataset is None
        assert result.error is not None
        assert "nonexistent_id" in result.error

    async def test_get_dataset_pds3_volume(self, sample_dataset_pds3):
        """PDS3 volume dataset is retrieved successfully."""
        with patch(_GET_DATASET_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_dataset = AsyncMock(return_value=sample_dataset_pds3)

            tool = PDSCatalogGetDatasetTool()
            result = await tool.arun(
                PDSCatalogGetDatasetInputSchema(dataset_id="GO_0017")
            )

        assert result.status == "success"
        assert result.dataset["id"] == "GO_0017"
        assert result.dataset["pds_version"] == "PDS3"
        assert result.dataset["type"] == "volume"

    async def test_get_dataset_catalog_client_error(self):
        """PDSCatalogClientError is re-raised."""
        with patch(_GET_DATASET_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_dataset = AsyncMock(side_effect=PDSCatalogClientError("load failed"))

            tool = PDSCatalogGetDatasetTool()
            with pytest.raises(PDSCatalogClientError, match="load failed"):
                await tool.arun(PDSCatalogGetDatasetInputSchema(dataset_id="any"))

    async def test_get_dataset_unexpected_error(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_GET_DATASET_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_dataset = AsyncMock(side_effect=IOError("disk error"))

            tool = PDSCatalogGetDatasetTool()
            with pytest.raises(RuntimeError, match="Internal error retrieving dataset"):
                await tool.arun(PDSCatalogGetDatasetInputSchema(dataset_id="any"))

    async def test_get_dataset_with_config(self, sample_dataset):
        """Custom catalog_dir config is passed to the client."""
        with patch(_GET_DATASET_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_dataset = AsyncMock(return_value=sample_dataset)

            config = PDSCatalogGetDatasetToolConfig(catalog_dir="/my/catalog")
            tool = PDSCatalogGetDatasetTool(config=config)
            await tool.arun(PDSCatalogGetDatasetInputSchema(dataset_id="any"))

        MockClient.assert_called_once_with(catalog_dir="/my/catalog")


# ---------------------------------------------------------------------------
# PDSCatalogListMissionsTool
# ---------------------------------------------------------------------------


class TestPDSCatalogListMissionsTool:
    """Tests for PDSCatalogListMissionsTool."""

    async def test_list_missions_basic(self):
        """List missions returns formatted mission items."""
        mock_missions = [
            {"name": "Cassini", "count": 42, "nodes": ["img", "ppi"]},
            {"name": "Juno", "count": 15, "nodes": ["ppi"]},
        ]
        with patch(_LIST_MISSIONS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_missions = AsyncMock(return_value=mock_missions)

            tool = PDSCatalogListMissionsTool()
            result = await tool.arun(PDSCatalogListMissionsInputSchema())

        assert isinstance(result, PDSCatalogListMissionsOutputSchema)
        assert result.status == "success"
        assert result.count == 2
        assert len(result.missions) == 2

        cassini = result.missions[0]
        assert isinstance(cassini, PDSCatalogMissionItem)
        assert cassini.name == "Cassini"
        assert cassini.count == 42
        assert cassini.nodes == ["img", "ppi"]

    async def test_list_missions_with_node_filter(self):
        """Node filter is forwarded to the client."""
        mock_missions = [{"name": "Juno", "count": 15, "nodes": ["ppi"]}]
        with patch(_LIST_MISSIONS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_missions = AsyncMock(return_value=mock_missions)

            tool = PDSCatalogListMissionsTool()
            result = await tool.arun(PDSCatalogListMissionsInputSchema(node="ppi"))

        mock_client.list_missions.assert_called_once_with(node="ppi", limit=50)
        assert result.count == 1

    async def test_list_missions_with_limit(self):
        """Limit parameter is forwarded to the client."""
        with patch(_LIST_MISSIONS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_missions = AsyncMock(return_value=[])

            tool = PDSCatalogListMissionsTool()
            await tool.arun(PDSCatalogListMissionsInputSchema(limit=5))

        mock_client.list_missions.assert_called_once_with(node=None, limit=5)

    async def test_list_missions_empty(self):
        """Empty results return count=0 and empty missions list."""
        with patch(_LIST_MISSIONS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_missions = AsyncMock(return_value=[])

            tool = PDSCatalogListMissionsTool()
            result = await tool.arun(PDSCatalogListMissionsInputSchema())

        assert result.status == "success"
        assert result.count == 0
        assert result.missions == []

    async def test_list_missions_catalog_client_error(self):
        """PDSCatalogClientError is re-raised."""
        with patch(_LIST_MISSIONS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_missions = AsyncMock(side_effect=PDSCatalogClientError("broken"))

            tool = PDSCatalogListMissionsTool()
            with pytest.raises(PDSCatalogClientError, match="broken"):
                await tool.arun(PDSCatalogListMissionsInputSchema())

    async def test_list_missions_unexpected_error(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_LIST_MISSIONS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_missions = AsyncMock(side_effect=KeyError("missing key"))

            tool = PDSCatalogListMissionsTool()
            with pytest.raises(RuntimeError, match="Internal error listing missions"):
                await tool.arun(PDSCatalogListMissionsInputSchema())

    async def test_list_missions_with_config(self):
        """Custom catalog_dir config is passed to the client."""
        with patch(_LIST_MISSIONS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_missions = AsyncMock(return_value=[])

            config = PDSCatalogListMissionsToolConfig(catalog_dir="/data/catalog")
            tool = PDSCatalogListMissionsTool(config=config)
            await tool.arun(PDSCatalogListMissionsInputSchema())

        MockClient.assert_called_once_with(catalog_dir="/data/catalog")


# ---------------------------------------------------------------------------
# PDSCatalogListTargetsTool
# ---------------------------------------------------------------------------


class TestPDSCatalogListTargetsTool:
    """Tests for PDSCatalogListTargetsTool."""

    async def test_list_targets_basic(self):
        """List targets returns formatted target items."""
        mock_targets = [
            {"name": "Mars", "count": 100, "nodes": ["geo", "img", "atm"]},
            {"name": "Saturn", "count": 50, "nodes": ["img", "ppi", "rms"]},
            {"name": "Enceladus", "count": 12, "nodes": ["img"]},
        ]
        with patch(_LIST_TARGETS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_targets = AsyncMock(return_value=mock_targets)

            tool = PDSCatalogListTargetsTool()
            result = await tool.arun(PDSCatalogListTargetsInputSchema())

        assert isinstance(result, PDSCatalogListTargetsOutputSchema)
        assert result.status == "success"
        assert result.count == 3
        assert len(result.targets) == 3

        mars = result.targets[0]
        assert isinstance(mars, PDSCatalogTargetItem)
        assert mars.name == "Mars"
        assert mars.count == 100
        assert "geo" in mars.nodes

    async def test_list_targets_with_node_filter(self):
        """Node filter is forwarded to the client."""
        mock_targets = [{"name": "Saturn", "count": 50, "nodes": ["rms"]}]
        with patch(_LIST_TARGETS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_targets = AsyncMock(return_value=mock_targets)

            tool = PDSCatalogListTargetsTool()
            result = await tool.arun(PDSCatalogListTargetsInputSchema(node="rms"))

        mock_client.list_targets.assert_called_once_with(node="rms", limit=50)
        assert result.count == 1

    async def test_list_targets_with_limit(self):
        """Limit parameter is forwarded to the client."""
        with patch(_LIST_TARGETS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_targets = AsyncMock(return_value=[])

            tool = PDSCatalogListTargetsTool()
            await tool.arun(PDSCatalogListTargetsInputSchema(limit=10))

        mock_client.list_targets.assert_called_once_with(node=None, limit=10)

    async def test_list_targets_empty(self):
        """Empty results return count=0 and empty targets list."""
        with patch(_LIST_TARGETS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_targets = AsyncMock(return_value=[])

            tool = PDSCatalogListTargetsTool()
            result = await tool.arun(PDSCatalogListTargetsInputSchema())

        assert result.status == "success"
        assert result.count == 0
        assert result.targets == []

    async def test_list_targets_catalog_client_error(self):
        """PDSCatalogClientError is re-raised."""
        with patch(_LIST_TARGETS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_targets = AsyncMock(side_effect=PDSCatalogClientError("error"))

            tool = PDSCatalogListTargetsTool()
            with pytest.raises(PDSCatalogClientError, match="error"):
                await tool.arun(PDSCatalogListTargetsInputSchema())

    async def test_list_targets_unexpected_error(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_LIST_TARGETS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_targets = AsyncMock(side_effect=ValueError("bad"))

            tool = PDSCatalogListTargetsTool()
            with pytest.raises(RuntimeError, match="Internal error listing targets"):
                await tool.arun(PDSCatalogListTargetsInputSchema())

    async def test_list_targets_with_config(self):
        """Custom catalog_dir config is passed to the client."""
        with patch(_LIST_TARGETS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.list_targets = AsyncMock(return_value=[])

            config = PDSCatalogListTargetsToolConfig(catalog_dir="/targets/dir")
            tool = PDSCatalogListTargetsTool(config=config)
            await tool.arun(PDSCatalogListTargetsInputSchema())

        MockClient.assert_called_once_with(catalog_dir="/targets/dir")


# ---------------------------------------------------------------------------
# PDSCatalogStatsTool
# ---------------------------------------------------------------------------


class TestPDSCatalogStatsTool:
    """Tests for PDSCatalogStatsTool."""

    @pytest.fixture
    def mock_stats(self):
        return {
            "total_datasets": 500,
            "by_node": {"img": 150, "ppi": 100, "sbn": 80, "geo": 70, "atm": 40, "rms": 35, "naif": 25},
            "by_pds_version": {"PDS3": 200, "PDS4": 300},
            "by_type": {"volume": 200, "bundle": 150, "collection": 150},
            "missions_count": 45,
            "targets_count": 120,
        }

    async def test_stats_basic(self, mock_stats):
        """Stats tool returns all catalog statistics."""
        with patch(_STATS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_stats = AsyncMock(return_value=mock_stats)

            tool = PDSCatalogStatsTool()
            result = await tool.arun(PDSCatalogStatsInputSchema())

        assert isinstance(result, PDSCatalogStatsOutputSchema)
        assert result.status == "success"
        assert result.total_datasets == 500
        assert result.by_node == {"img": 150, "ppi": 100, "sbn": 80, "geo": 70, "atm": 40, "rms": 35, "naif": 25}
        assert result.by_pds_version == {"PDS3": 200, "PDS4": 300}
        assert result.by_type == {"volume": 200, "bundle": 150, "collection": 150}
        assert result.missions_count == 45
        assert result.targets_count == 120

    async def test_stats_empty_catalog(self):
        """Stats for an empty catalog."""
        empty_stats = {
            "total_datasets": 0,
            "by_node": {},
            "by_pds_version": {},
            "by_type": {},
            "missions_count": 0,
            "targets_count": 0,
        }
        with patch(_STATS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_stats = AsyncMock(return_value=empty_stats)

            tool = PDSCatalogStatsTool()
            result = await tool.arun(PDSCatalogStatsInputSchema())

        assert result.status == "success"
        assert result.total_datasets == 0
        assert result.missions_count == 0
        assert result.targets_count == 0

    async def test_stats_catalog_client_error(self):
        """PDSCatalogClientError is re-raised."""
        with patch(_STATS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_stats = AsyncMock(side_effect=PDSCatalogClientError("stats error"))

            tool = PDSCatalogStatsTool()
            with pytest.raises(PDSCatalogClientError, match="stats error"):
                await tool.arun(PDSCatalogStatsInputSchema())

    async def test_stats_unexpected_error(self):
        """Generic exceptions are wrapped in RuntimeError."""
        with patch(_STATS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_stats = AsyncMock(side_effect=OSError("io problem"))

            tool = PDSCatalogStatsTool()
            with pytest.raises(RuntimeError, match="Internal error retrieving stats"):
                await tool.arun(PDSCatalogStatsInputSchema())

    async def test_stats_with_config(self, mock_stats):
        """Custom catalog_dir config is passed to the client."""
        with patch(_STATS_CLIENT) as MockClient:
            mock_client = MockClient.return_value
            mock_client.get_stats = AsyncMock(return_value=mock_stats)

            config = PDSCatalogStatsToolConfig(catalog_dir="/stats/dir")
            tool = PDSCatalogStatsTool(config=config)
            await tool.arun(PDSCatalogStatsInputSchema())

        MockClient.assert_called_once_with(catalog_dir="/stats/dir")


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    """Tests for input schema validation."""

    def test_search_input_defaults(self):
        """SearchInputSchema has correct defaults."""
        schema = PDSCatalogSearchInputSchema()
        assert schema.query is None
        assert schema.node is None
        assert schema.mission is None
        assert schema.instrument is None
        assert schema.target is None
        assert schema.pds_version is None
        assert schema.dataset_type is None
        assert schema.start_date is None
        assert schema.stop_date is None
        assert schema.limit == 20
        assert schema.offset == 0
        assert schema.fields == "summary"

    def test_search_input_invalid_node(self):
        """Invalid node value raises validation error."""
        with pytest.raises(Exception):
            PDSCatalogSearchInputSchema(node="invalid_node")

    def test_search_input_invalid_pds_version(self):
        """Invalid pds_version raises validation error."""
        with pytest.raises(Exception):
            PDSCatalogSearchInputSchema(pds_version="PDS5")

    def test_search_input_invalid_dataset_type(self):
        """Invalid dataset_type raises validation error."""
        with pytest.raises(Exception):
            PDSCatalogSearchInputSchema(dataset_type="invalid_type")

    def test_search_input_invalid_fields(self):
        """Invalid fields value raises validation error."""
        with pytest.raises(Exception):
            PDSCatalogSearchInputSchema(fields="invalid_profile")

    def test_search_input_limit_bounds(self):
        """Limit must be between 1 and 50."""
        with pytest.raises(Exception):
            PDSCatalogSearchInputSchema(limit=0)
        with pytest.raises(Exception):
            PDSCatalogSearchInputSchema(limit=51)

    def test_search_input_offset_non_negative(self):
        """Offset must be >= 0."""
        with pytest.raises(Exception):
            PDSCatalogSearchInputSchema(offset=-1)

    def test_list_missions_input_defaults(self):
        """ListMissionsInputSchema has correct defaults."""
        schema = PDSCatalogListMissionsInputSchema()
        assert schema.node is None
        assert schema.limit == 50

    def test_list_targets_input_defaults(self):
        """ListTargetsInputSchema has correct defaults."""
        schema = PDSCatalogListTargetsInputSchema()
        assert schema.node is None
        assert schema.limit == 50

    def test_get_dataset_input_requires_id(self):
        """GetDatasetInputSchema requires dataset_id."""
        with pytest.raises(Exception):
            PDSCatalogGetDatasetInputSchema()

    def test_stats_input_no_params(self):
        """StatsInputSchema takes no parameters."""
        schema = PDSCatalogStatsInputSchema()
        assert schema is not None
