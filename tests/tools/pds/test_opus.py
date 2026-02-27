"""Unit tests for OPUS (Outer Planets Unified Search) tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from akd_ext.tools.pds.opus.opus_search import (
    OPUSObservationSummary,
    OPUSSearchInputSchema,
    OPUSSearchOutputSchema,
    OPUSSearchTool,
    OPUSSearchToolConfig,
)
from akd_ext.tools.pds.opus.opus_count import (
    OPUSCountInputSchema,
    OPUSCountOutputSchema,
    OPUSCountTool,
    OPUSCountToolConfig,
)
from akd_ext.tools.pds.opus.opus_get_metadata import (
    OPUSGetMetadataInputSchema,
    OPUSGetMetadataOutputSchema,
    OPUSGetMetadataTool,
    OPUSGetMetadataToolConfig,
)
from akd_ext.tools.pds.opus.opus_get_files import (
    OPUSBrowseImages,
    OPUSGetFilesInputSchema,
    OPUSGetFilesOutputSchema,
    OPUSGetFilesTool,
    OPUSGetFilesToolConfig,
)
from akd_ext.tools.pds.opus.types import OPUS_INSTRUMENTS, OPUS_MISSIONS, OPUS_PLANETS
from akd_ext.tools.pds.utils.opus_client import OPUSClient, OPUSClientError

# Patch paths -- must match where OPUSClient is looked up at runtime
_SEARCH_CLIENT = "akd_ext.tools.pds.opus.opus_search.OPUSClient"
_COUNT_CLIENT = "akd_ext.tools.pds.opus.opus_count.OPUSClient"
_GET_METADATA_CLIENT = "akd_ext.tools.pds.opus.opus_get_metadata.OPUSClient"
_GET_FILES_CLIENT = "akd_ext.tools.pds.opus.opus_get_files.OPUSClient"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_observation(**overrides):
    """Create a mock OPUSObservation with sensible defaults."""
    obs = MagicMock()
    obs.opusid = overrides.get("opusid", "co-iss-n1460960653")
    obs.instrument = overrides.get("instrument", "Cassini ISS")
    obs.target = overrides.get("target", "Saturn")
    obs.mission = overrides.get("mission", "Cassini")
    obs.planet = overrides.get("planet", "Saturn")
    obs.time1 = overrides.get("time1", "2004-04-18T00:00:00.000")
    obs.time2 = overrides.get("time2", "2004-04-18T00:01:00.000")
    obs.observation_duration = overrides.get("observation_duration", 60.0)
    return obs


def _make_mock_search_response(**overrides):
    """Create a mock search response."""
    response = MagicMock()
    response.status = overrides.get("status", "success")
    response.available = overrides.get("available", 1)
    response.start_obs = overrides.get("start_obs", 1)
    response.limit = overrides.get("limit", 100)
    response.count = overrides.get("count", 1)
    response.observations = overrides.get("observations", [_make_mock_observation()])
    response.error = overrides.get("error", None)
    return response


def _make_mock_count_response(**overrides):
    """Create a mock count response."""
    response = MagicMock()
    response.status = overrides.get("status", "success")
    response.count = overrides.get("count", 42000)
    response.error = overrides.get("error", None)
    return response


def _make_mock_metadata(**overrides):
    """Create a mock OPUSMetadata."""
    metadata = MagicMock()
    metadata.opusid = overrides.get("opusid", "co-iss-n1460960653")
    metadata.general_constraints = overrides.get(
        "general_constraints",
        {"planet": "Saturn", "target": "Saturn", "mission": "Cassini", "instrument": "Cassini ISS"},
    )
    metadata.pds_constraints = overrides.get(
        "pds_constraints",
        {"bundle_id": "co-iss_0xxx", "dataset_id": "COISS_2001"},
    )
    metadata.image_constraints = overrides.get(
        "image_constraints",
        {"image_type": "Frame", "width": 1024, "height": 1024},
    )
    metadata.wavelength_constraints = overrides.get(
        "wavelength_constraints",
        {"wavelength1": 0.38, "wavelength2": 1.05},
    )
    metadata.ring_geometry_constraints = overrides.get(
        "ring_geometry_constraints",
        {"ring_radius1": 74500.0, "ring_radius2": 140220.0},
    )
    metadata.surface_geometry_constraints = overrides.get(
        "surface_geometry_constraints",
        {"center_latitude": -15.0, "center_longitude": 120.0},
    )
    metadata.instrument_constraints = overrides.get(
        "instrument_constraints",
        {"filter1": "CL1", "filter2": "CL2", "camera": "Narrow Angle"},
    )
    return metadata


def _make_mock_metadata_response(**overrides):
    """Create a mock metadata response."""
    response = MagicMock()
    response.status = overrides.get("status", "success")
    response.metadata = overrides.get("metadata", _make_mock_metadata())
    response.error = overrides.get("error", None)
    return response


def _make_mock_files(**overrides):
    """Create a mock OPUSFiles."""
    files = MagicMock()
    files.opusid = overrides.get("opusid", "co-iss-n1460960653")
    files.raw_files = overrides.get("raw_files", ["https://opus.pds-rings.seti.org/holdings/raw/data.img"])
    files.calibrated_files = overrides.get(
        "calibrated_files", ["https://opus.pds-rings.seti.org/holdings/calibrated/data.img"]
    )
    files.browse_thumb = overrides.get("browse_thumb", "https://opus.pds-rings.seti.org/holdings/thumb.jpg")
    files.browse_small = overrides.get("browse_small", "https://opus.pds-rings.seti.org/holdings/small.jpg")
    files.browse_medium = overrides.get("browse_medium", "https://opus.pds-rings.seti.org/holdings/medium.jpg")
    files.browse_full = overrides.get("browse_full", "https://opus.pds-rings.seti.org/holdings/full.jpg")
    files.all_files = overrides.get(
        "all_files",
        {
            "raw_image": ["https://opus.pds-rings.seti.org/holdings/raw/data.img"],
            "calibrated_image": ["https://opus.pds-rings.seti.org/holdings/calibrated/data.img"],
        },
    )
    return files


def _make_mock_files_response(**overrides):
    """Create a mock files response."""
    response = MagicMock()
    response.status = overrides.get("status", "success")
    response.files = overrides.get("files", _make_mock_files())
    response.error = overrides.get("error", None)
    return response


def _patch_opus_client(patch_path):
    """Set up mock OPUSClient with async context manager support.

    Returns (patcher, mock_client) -- caller must use patcher as context manager.
    The mock_client can then have methods assigned, e.g.:
        mock_client.search_observations = AsyncMock(return_value=...)
    """
    patcher = patch(patch_path)
    MockClient = patcher.start()
    mock_client = AsyncMock()
    MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
    return patcher, MockClient, mock_client


# ---------------------------------------------------------------------------
# OPUSSearchTool
# ---------------------------------------------------------------------------


class TestOPUSSearchTool:
    """Tests for OPUSSearchTool."""

    async def test_basic_search(self):
        """Basic search returns observations."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(return_value=_make_mock_search_response())

            tool = OPUSSearchTool()
            result = await tool.arun(OPUSSearchInputSchema())
        finally:
            patcher.stop()

        assert isinstance(result, OPUSSearchOutputSchema)
        assert result.status == "success"
        assert result.count == 1
        assert result.available == 1
        assert len(result.observations) == 1

    async def test_search_observation_fields(self):
        """Observation summaries contain expected fields."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(return_value=_make_mock_search_response())

            tool = OPUSSearchTool()
            result = await tool.arun(OPUSSearchInputSchema())
        finally:
            patcher.stop()

        obs = result.observations[0]
        assert isinstance(obs, OPUSObservationSummary)
        assert obs.opusid == "co-iss-n1460960653"
        assert obs.instrument == "Cassini ISS"
        assert obs.target == "Saturn"
        assert obs.mission == "Cassini"
        assert obs.planet == "Saturn"
        assert obs.time_start == "2004-04-18T00:00:00.000"
        assert obs.time_end == "2004-04-18T00:01:00.000"
        assert obs.duration_seconds == 60.0

    async def test_search_with_target_filter(self):
        """Target filter is forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(return_value=_make_mock_search_response())

            tool = OPUSSearchTool()
            await tool.arun(OPUSSearchInputSchema(target="Titan"))
        finally:
            patcher.stop()

        call_kwargs = mock_client.search_observations.call_args.kwargs
        assert call_kwargs["target"] == "Titan"

    async def test_search_with_mission_filter(self):
        """Mission filter is forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(return_value=_make_mock_search_response())

            tool = OPUSSearchTool()
            await tool.arun(OPUSSearchInputSchema(mission="Cassini"))
        finally:
            patcher.stop()

        call_kwargs = mock_client.search_observations.call_args.kwargs
        assert call_kwargs["mission"] == "Cassini"

    async def test_search_with_instrument_filter(self):
        """Instrument filter is forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(return_value=_make_mock_search_response())

            tool = OPUSSearchTool()
            await tool.arun(OPUSSearchInputSchema(instrument="Cassini ISS"))
        finally:
            patcher.stop()

        call_kwargs = mock_client.search_observations.call_args.kwargs
        assert call_kwargs["instrument"] == "Cassini ISS"

    async def test_search_with_planet_filter(self):
        """Planet filter is forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(return_value=_make_mock_search_response())

            tool = OPUSSearchTool()
            await tool.arun(OPUSSearchInputSchema(planet="Saturn"))
        finally:
            patcher.stop()

        call_kwargs = mock_client.search_observations.call_args.kwargs
        assert call_kwargs["planet"] == "Saturn"

    async def test_search_with_time_range(self):
        """Time range filters are forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(return_value=_make_mock_search_response())

            tool = OPUSSearchTool()
            await tool.arun(
                OPUSSearchInputSchema(
                    time_min="2004-01-01",
                    time_max="2004-12-31",
                )
            )
        finally:
            patcher.stop()

        call_kwargs = mock_client.search_observations.call_args.kwargs
        assert call_kwargs["time_min"] == "2004-01-01"
        assert call_kwargs["time_max"] == "2004-12-31"

    async def test_search_with_limit_and_startobs(self):
        """Limit and startobs are forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(
                return_value=_make_mock_search_response(start_obs=50, limit=25, count=25, available=200)
            )

            tool = OPUSSearchTool()
            result = await tool.arun(OPUSSearchInputSchema(limit=25, startobs=50))
        finally:
            patcher.stop()

        call_kwargs = mock_client.search_observations.call_args.kwargs
        assert call_kwargs["limit"] == 25
        assert call_kwargs["startobs"] == 50
        assert result.start_obs == 50
        assert result.limit == 25

    async def test_search_pagination(self):
        """Pagination returns correct metadata when more results are available."""
        obs_list = [_make_mock_observation(opusid=f"co-iss-obs-{i}") for i in range(10)]
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(
                return_value=_make_mock_search_response(
                    observations=obs_list,
                    count=10,
                    available=500,
                    start_obs=1,
                    limit=10,
                )
            )

            tool = OPUSSearchTool()
            result = await tool.arun(OPUSSearchInputSchema(limit=10, startobs=1))
        finally:
            patcher.stop()

        assert result.count == 10
        assert result.available == 500
        assert result.start_obs == 1
        assert result.limit == 10
        assert len(result.observations) == 10

    async def test_search_all_filters_combined(self):
        """All filters combined are forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(return_value=_make_mock_search_response())

            tool = OPUSSearchTool()
            await tool.arun(
                OPUSSearchInputSchema(
                    target="Titan",
                    mission="Cassini",
                    instrument="Cassini ISS",
                    planet="Saturn",
                    time_min="2004-01-01",
                    time_max="2017-09-15",
                    limit=50,
                    startobs=10,
                )
            )
        finally:
            patcher.stop()

        call_kwargs = mock_client.search_observations.call_args.kwargs
        assert call_kwargs["target"] == "Titan"
        assert call_kwargs["mission"] == "Cassini"
        assert call_kwargs["instrument"] == "Cassini ISS"
        assert call_kwargs["planet"] == "Saturn"
        assert call_kwargs["time_min"] == "2004-01-01"
        assert call_kwargs["time_max"] == "2017-09-15"
        assert call_kwargs["limit"] == 50
        assert call_kwargs["startobs"] == 10

    async def test_search_empty_results(self):
        """Empty search results return count=0 and empty observations list."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(
                return_value=_make_mock_search_response(
                    count=0, available=0, observations=[]
                )
            )

            tool = OPUSSearchTool()
            result = await tool.arun(OPUSSearchInputSchema(target="Nonexistent"))
        finally:
            patcher.stop()

        assert result.status == "success"
        assert result.count == 0
        assert result.available == 0
        assert result.observations == []

    async def test_search_error_response(self):
        """Error response from API returns error status."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(
                return_value=_make_mock_search_response(
                    status="error", error="Bad request", count=0, available=0, observations=[]
                )
            )

            tool = OPUSSearchTool()
            result = await tool.arun(OPUSSearchInputSchema())
        finally:
            patcher.stop()

        assert result.status == "error"
        assert result.count == 0
        assert result.available == 0
        assert result.observations == []

    async def test_search_client_error_raises(self):
        """OPUSClientError is re-raised."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(
                side_effect=OPUSClientError("connection failed")
            )

            tool = OPUSSearchTool()
            with pytest.raises(OPUSClientError, match="connection failed"):
                await tool.arun(OPUSSearchInputSchema())
        finally:
            patcher.stop()

    async def test_search_unexpected_error_raises_runtime_error(self):
        """Unexpected exceptions are wrapped in RuntimeError."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(
                side_effect=TypeError("bad type")
            )

            tool = OPUSSearchTool()
            with pytest.raises(RuntimeError, match="Internal error"):
                await tool.arun(OPUSSearchInputSchema())
        finally:
            patcher.stop()

    async def test_search_with_config(self):
        """Custom config is passed to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(return_value=_make_mock_search_response())

            config = OPUSSearchToolConfig(
                base_url="https://custom.opus.url/api/",
                timeout=60.0,
                max_retries=5,
            )
            tool = OPUSSearchTool(config=config)
            await tool.arun(OPUSSearchInputSchema())
        finally:
            patcher.stop()

        MockClient.assert_called_once_with(
            base_url="https://custom.opus.url/api/",
            timeout=60.0,
            max_retries=5,
        )

    async def test_search_multiple_observations(self):
        """Search returns multiple observations correctly."""
        obs1 = _make_mock_observation(opusid="co-iss-n1460960653", target="Saturn")
        obs2 = _make_mock_observation(opusid="co-vims-v1460961000", target="Titan", instrument="Cassini VIMS")
        patcher, MockClient, mock_client = _patch_opus_client(_SEARCH_CLIENT)
        try:
            mock_client.search_observations = AsyncMock(
                return_value=_make_mock_search_response(
                    observations=[obs1, obs2],
                    count=2,
                    available=2,
                )
            )

            tool = OPUSSearchTool()
            result = await tool.arun(OPUSSearchInputSchema())
        finally:
            patcher.stop()

        assert result.count == 2
        assert len(result.observations) == 2
        assert result.observations[0].opusid == "co-iss-n1460960653"
        assert result.observations[1].opusid == "co-vims-v1460961000"
        assert result.observations[1].instrument == "Cassini VIMS"


# ---------------------------------------------------------------------------
# OPUSCountTool
# ---------------------------------------------------------------------------


class TestOPUSCountTool:
    """Tests for OPUSCountTool."""

    async def test_basic_count(self):
        """Count returns total matching observations."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(return_value=_make_mock_count_response())

            tool = OPUSCountTool()
            result = await tool.arun(OPUSCountInputSchema())
        finally:
            patcher.stop()

        assert isinstance(result, OPUSCountOutputSchema)
        assert result.status == "success"
        assert result.count == 42000

    async def test_count_with_target_filter(self):
        """Target filter is forwarded and reflected in filters."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(
                return_value=_make_mock_count_response(count=15000)
            )

            tool = OPUSCountTool()
            result = await tool.arun(OPUSCountInputSchema(target="Saturn"))
        finally:
            patcher.stop()

        call_kwargs = mock_client.count_observations.call_args.kwargs
        assert call_kwargs["target"] == "Saturn"
        assert result.count == 15000
        assert result.filters["target"] == "Saturn"

    async def test_count_with_mission_filter(self):
        """Mission filter is forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(return_value=_make_mock_count_response())

            tool = OPUSCountTool()
            result = await tool.arun(OPUSCountInputSchema(mission="Cassini"))
        finally:
            patcher.stop()

        call_kwargs = mock_client.count_observations.call_args.kwargs
        assert call_kwargs["mission"] == "Cassini"
        assert result.filters["mission"] == "Cassini"

    async def test_count_with_instrument_filter(self):
        """Instrument filter is forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(return_value=_make_mock_count_response())

            tool = OPUSCountTool()
            result = await tool.arun(OPUSCountInputSchema(instrument="Cassini ISS"))
        finally:
            patcher.stop()

        call_kwargs = mock_client.count_observations.call_args.kwargs
        assert call_kwargs["instrument"] == "Cassini ISS"
        assert result.filters["instrument"] == "Cassini ISS"

    async def test_count_with_planet_filter(self):
        """Planet filter is forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(return_value=_make_mock_count_response())

            tool = OPUSCountTool()
            result = await tool.arun(OPUSCountInputSchema(planet="Jupiter"))
        finally:
            patcher.stop()

        call_kwargs = mock_client.count_observations.call_args.kwargs
        assert call_kwargs["planet"] == "Jupiter"
        assert result.filters["planet"] == "Jupiter"

    async def test_count_with_time_range(self):
        """Time range filters are forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(return_value=_make_mock_count_response())

            tool = OPUSCountTool()
            result = await tool.arun(
                OPUSCountInputSchema(time_min="2004-01-01", time_max="2004-12-31")
            )
        finally:
            patcher.stop()

        call_kwargs = mock_client.count_observations.call_args.kwargs
        assert call_kwargs["time_min"] == "2004-01-01"
        assert call_kwargs["time_max"] == "2004-12-31"
        assert result.filters["time_min"] == "2004-01-01"
        assert result.filters["time_max"] == "2004-12-31"

    async def test_count_all_filters_combined(self):
        """All filters combined are forwarded to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(return_value=_make_mock_count_response(count=100))

            tool = OPUSCountTool()
            result = await tool.arun(
                OPUSCountInputSchema(
                    target="Titan",
                    mission="Cassini",
                    instrument="Cassini ISS",
                    planet="Saturn",
                    time_min="2004-01-01",
                    time_max="2017-09-15",
                )
            )
        finally:
            patcher.stop()

        call_kwargs = mock_client.count_observations.call_args.kwargs
        assert call_kwargs["target"] == "Titan"
        assert call_kwargs["mission"] == "Cassini"
        assert call_kwargs["instrument"] == "Cassini ISS"
        assert call_kwargs["planet"] == "Saturn"
        assert call_kwargs["time_min"] == "2004-01-01"
        assert call_kwargs["time_max"] == "2017-09-15"
        assert result.count == 100

    async def test_count_filters_dict_populated(self):
        """Filters dict in output contains all applied filters."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(return_value=_make_mock_count_response())

            tool = OPUSCountTool()
            result = await tool.arun(
                OPUSCountInputSchema(target="Saturn", mission="Cassini")
            )
        finally:
            patcher.stop()

        assert result.filters["target"] == "Saturn"
        assert result.filters["mission"] == "Cassini"
        assert result.filters["instrument"] is None
        assert result.filters["planet"] is None
        assert result.filters["time_min"] is None
        assert result.filters["time_max"] is None

    async def test_count_error_response(self):
        """Error response from API returns error status."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(
                return_value=_make_mock_count_response(status="error", error="Bad request", count=0)
            )

            tool = OPUSCountTool()
            result = await tool.arun(OPUSCountInputSchema())
        finally:
            patcher.stop()

        assert result.status == "error"
        assert result.count == 0

    async def test_count_client_error_raises(self):
        """OPUSClientError is re-raised."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(
                side_effect=OPUSClientError("timeout")
            )

            tool = OPUSCountTool()
            with pytest.raises(OPUSClientError, match="timeout"):
                await tool.arun(OPUSCountInputSchema())
        finally:
            patcher.stop()

    async def test_count_unexpected_error_raises_runtime_error(self):
        """Unexpected exceptions are wrapped in RuntimeError."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(
                side_effect=ValueError("bad value")
            )

            tool = OPUSCountTool()
            with pytest.raises(RuntimeError, match="Internal error"):
                await tool.arun(OPUSCountInputSchema())
        finally:
            patcher.stop()

    async def test_count_with_config(self):
        """Custom config is passed to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_COUNT_CLIENT)
        try:
            mock_client.count_observations = AsyncMock(return_value=_make_mock_count_response())

            config = OPUSCountToolConfig(
                base_url="https://custom.opus.url/api/",
                timeout=45.0,
                max_retries=2,
            )
            tool = OPUSCountTool(config=config)
            await tool.arun(OPUSCountInputSchema())
        finally:
            patcher.stop()

        MockClient.assert_called_once_with(
            base_url="https://custom.opus.url/api/",
            timeout=45.0,
            max_retries=2,
        )


# ---------------------------------------------------------------------------
# OPUSGetMetadataTool
# ---------------------------------------------------------------------------


class TestOPUSGetMetadataTool:
    """Tests for OPUSGetMetadataTool."""

    async def test_get_metadata_found(self):
        """Existing observation returns success with full metadata."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(return_value=_make_mock_metadata_response())

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert isinstance(result, OPUSGetMetadataOutputSchema)
        assert result.status == "success"
        assert result.opusid == "co-iss-n1460960653"

    async def test_get_metadata_general_constraints(self):
        """General constraints are populated in the output."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(return_value=_make_mock_metadata_response())

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.general is not None
        assert result.general["planet"] == "Saturn"
        assert result.general["target"] == "Saturn"
        assert result.general["mission"] == "Cassini"

    async def test_get_metadata_pds_constraints(self):
        """PDS constraints are populated in the output."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(return_value=_make_mock_metadata_response())

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.pds is not None
        assert result.pds["bundle_id"] == "co-iss_0xxx"

    async def test_get_metadata_image_constraints(self):
        """Image constraints are populated in the output."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(return_value=_make_mock_metadata_response())

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.image is not None
        assert result.image["image_type"] == "Frame"
        assert result.image["width"] == 1024

    async def test_get_metadata_wavelength_constraints(self):
        """Wavelength constraints are populated in the output."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(return_value=_make_mock_metadata_response())

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.wavelength is not None
        assert result.wavelength["wavelength1"] == 0.38

    async def test_get_metadata_ring_geometry_constraints(self):
        """Ring geometry constraints are populated in the output."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(return_value=_make_mock_metadata_response())

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.ring_geometry is not None
        assert result.ring_geometry["ring_radius1"] == 74500.0

    async def test_get_metadata_surface_geometry_constraints(self):
        """Surface geometry constraints are populated in the output."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(return_value=_make_mock_metadata_response())

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.surface_geometry is not None
        assert result.surface_geometry["center_latitude"] == -15.0

    async def test_get_metadata_instrument_constraints(self):
        """Instrument-specific constraints are populated in the output."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(return_value=_make_mock_metadata_response())

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.instrument_specific is not None
        assert result.instrument_specific["filter1"] == "CL1"
        assert result.instrument_specific["camera"] == "Narrow Angle"

    async def test_get_metadata_not_found(self):
        """Missing metadata returns not_found status."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(
                return_value=_make_mock_metadata_response(metadata=None)
            )

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="nonexistent-obs")
            )
        finally:
            patcher.stop()

        assert result.status == "not_found"
        assert result.opusid == "nonexistent-obs"

    async def test_get_metadata_error_response(self):
        """Error response from API returns error status."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(
                return_value=_make_mock_metadata_response(
                    status="error", error="server error", metadata=MagicMock()
                )
            )

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.status == "error"
        assert result.opusid == "co-iss-n1460960653"

    async def test_get_metadata_client_error_raises(self):
        """OPUSClientError is re-raised."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(
                side_effect=OPUSClientError("connection refused")
            )

            tool = OPUSGetMetadataTool()
            with pytest.raises(OPUSClientError, match="connection refused"):
                await tool.arun(OPUSGetMetadataInputSchema(opusid="any"))
        finally:
            patcher.stop()

    async def test_get_metadata_unexpected_error_raises_runtime_error(self):
        """Unexpected exceptions are wrapped in RuntimeError."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(
                side_effect=KeyError("missing key")
            )

            tool = OPUSGetMetadataTool()
            with pytest.raises(RuntimeError, match="Internal error"):
                await tool.arun(OPUSGetMetadataInputSchema(opusid="any"))
        finally:
            patcher.stop()

    async def test_get_metadata_with_config(self):
        """Custom config is passed to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(return_value=_make_mock_metadata_response())

            config = OPUSGetMetadataToolConfig(
                base_url="https://custom.opus.url/api/",
                timeout=15.0,
                max_retries=1,
            )
            tool = OPUSGetMetadataTool(config=config)
            await tool.arun(OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653"))
        finally:
            patcher.stop()

        MockClient.assert_called_once_with(
            base_url="https://custom.opus.url/api/",
            timeout=15.0,
            max_retries=1,
        )

    async def test_get_metadata_empty_constraints_are_none(self):
        """Empty constraint dicts are returned as None."""
        metadata = _make_mock_metadata(
            general_constraints={"planet": "Saturn"},
            pds_constraints={},
            image_constraints={},
            wavelength_constraints={},
            ring_geometry_constraints={},
            surface_geometry_constraints={},
            instrument_constraints={},
        )
        patcher, MockClient, mock_client = _patch_opus_client(_GET_METADATA_CLIENT)
        try:
            mock_client.get_metadata = AsyncMock(
                return_value=_make_mock_metadata_response(metadata=metadata)
            )

            tool = OPUSGetMetadataTool()
            result = await tool.arun(
                OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.status == "success"
        assert result.general == {"planet": "Saturn"}
        # Empty dicts evaluate to falsy, so the tool returns None for them
        assert result.pds is None
        assert result.image is None
        assert result.wavelength is None
        assert result.ring_geometry is None
        assert result.surface_geometry is None
        assert result.instrument_specific is None


# ---------------------------------------------------------------------------
# OPUSGetFilesTool
# ---------------------------------------------------------------------------


class TestOPUSGetFilesTool:
    """Tests for OPUSGetFilesTool."""

    async def test_get_files_found(self):
        """Existing observation returns success with file URLs."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(return_value=_make_mock_files_response())

            tool = OPUSGetFilesTool()
            result = await tool.arun(
                OPUSGetFilesInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert isinstance(result, OPUSGetFilesOutputSchema)
        assert result.status == "success"
        assert result.opusid == "co-iss-n1460960653"

    async def test_get_files_raw_files(self):
        """Raw file URLs are populated."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(return_value=_make_mock_files_response())

            tool = OPUSGetFilesTool()
            result = await tool.arun(
                OPUSGetFilesInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.raw_files is not None
        assert len(result.raw_files) == 1
        assert "raw" in result.raw_files[0]

    async def test_get_files_calibrated_files(self):
        """Calibrated file URLs are populated."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(return_value=_make_mock_files_response())

            tool = OPUSGetFilesTool()
            result = await tool.arun(
                OPUSGetFilesInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.calibrated_files is not None
        assert len(result.calibrated_files) == 1
        assert "calibrated" in result.calibrated_files[0]

    async def test_get_files_browse_images(self):
        """Browse images at various resolutions are populated."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(return_value=_make_mock_files_response())

            tool = OPUSGetFilesTool()
            result = await tool.arun(
                OPUSGetFilesInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.browse_images is not None
        assert isinstance(result.browse_images, OPUSBrowseImages)
        assert result.browse_images.thumbnail == "https://opus.pds-rings.seti.org/holdings/thumb.jpg"
        assert result.browse_images.small == "https://opus.pds-rings.seti.org/holdings/small.jpg"
        assert result.browse_images.medium == "https://opus.pds-rings.seti.org/holdings/medium.jpg"
        assert result.browse_images.full == "https://opus.pds-rings.seti.org/holdings/full.jpg"

    async def test_get_files_all_file_categories(self):
        """All file categories dict is populated."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(return_value=_make_mock_files_response())

            tool = OPUSGetFilesTool()
            result = await tool.arun(
                OPUSGetFilesInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.all_file_categories is not None
        assert "raw_image" in result.all_file_categories
        assert "calibrated_image" in result.all_file_categories

    async def test_get_files_not_found(self):
        """Missing files returns not_found status."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(
                return_value=_make_mock_files_response(files=None)
            )

            tool = OPUSGetFilesTool()
            result = await tool.arun(
                OPUSGetFilesInputSchema(opusid="nonexistent-obs")
            )
        finally:
            patcher.stop()

        assert result.status == "not_found"
        assert result.opusid == "nonexistent-obs"

    async def test_get_files_error_response(self):
        """Error response from API returns error status."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(
                return_value=_make_mock_files_response(
                    status="error", error="server error", files=MagicMock()
                )
            )

            tool = OPUSGetFilesTool()
            result = await tool.arun(
                OPUSGetFilesInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.status == "error"
        assert result.opusid == "co-iss-n1460960653"

    async def test_get_files_client_error_raises(self):
        """OPUSClientError is re-raised."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(
                side_effect=OPUSClientError("network error")
            )

            tool = OPUSGetFilesTool()
            with pytest.raises(OPUSClientError, match="network error"):
                await tool.arun(OPUSGetFilesInputSchema(opusid="any"))
        finally:
            patcher.stop()

    async def test_get_files_unexpected_error_raises_runtime_error(self):
        """Unexpected exceptions are wrapped in RuntimeError."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(
                side_effect=IOError("disk error")
            )

            tool = OPUSGetFilesTool()
            with pytest.raises(RuntimeError, match="Internal error"):
                await tool.arun(OPUSGetFilesInputSchema(opusid="any"))
        finally:
            patcher.stop()

    async def test_get_files_with_config(self):
        """Custom config is passed to the client."""
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(return_value=_make_mock_files_response())

            config = OPUSGetFilesToolConfig(
                base_url="https://custom.opus.url/api/",
                timeout=20.0,
                max_retries=4,
            )
            tool = OPUSGetFilesTool(config=config)
            await tool.arun(OPUSGetFilesInputSchema(opusid="co-iss-n1460960653"))
        finally:
            patcher.stop()

        MockClient.assert_called_once_with(
            base_url="https://custom.opus.url/api/",
            timeout=20.0,
            max_retries=4,
        )

    async def test_get_files_no_browse_images(self):
        """Files without browse images return None for browse_images."""
        files = _make_mock_files(
            browse_thumb=None,
            browse_small=None,
            browse_medium=None,
            browse_full=None,
        )
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(
                return_value=_make_mock_files_response(files=files)
            )

            tool = OPUSGetFilesTool()
            result = await tool.arun(
                OPUSGetFilesInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.status == "success"
        assert result.browse_images is None

    async def test_get_files_empty_raw_calibrated(self):
        """Files with empty raw/calibrated lists return None for those fields."""
        files = _make_mock_files(raw_files=[], calibrated_files=[], all_files={})
        patcher, MockClient, mock_client = _patch_opus_client(_GET_FILES_CLIENT)
        try:
            mock_client.get_files = AsyncMock(
                return_value=_make_mock_files_response(files=files)
            )

            tool = OPUSGetFilesTool()
            result = await tool.arun(
                OPUSGetFilesInputSchema(opusid="co-iss-n1460960653")
            )
        finally:
            patcher.stop()

        assert result.status == "success"
        # Empty lists are falsy, so the tool returns None
        assert result.raw_files is None
        assert result.calibrated_files is None
        assert result.all_file_categories is None


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestOPUSSchemaValidation:
    """Tests for OPUS input schema validation."""

    # --- OPUSSearchInputSchema ---

    def test_search_input_defaults(self):
        """SearchInputSchema has correct defaults."""
        schema = OPUSSearchInputSchema()
        assert schema.target is None
        assert schema.mission is None
        assert schema.instrument is None
        assert schema.planet is None
        assert schema.time_min is None
        assert schema.time_max is None
        assert schema.limit == 100
        assert schema.startobs == 1

    def test_search_input_limit_bounds_low(self):
        """Limit below 1 raises validation error."""
        with pytest.raises(Exception):
            OPUSSearchInputSchema(limit=0)

    def test_search_input_limit_bounds_high(self):
        """Limit above 1000 raises validation error."""
        with pytest.raises(Exception):
            OPUSSearchInputSchema(limit=1001)

    def test_search_input_limit_valid_min(self):
        """Limit of 1 is valid."""
        schema = OPUSSearchInputSchema(limit=1)
        assert schema.limit == 1

    def test_search_input_limit_valid_max(self):
        """Limit of 1000 is valid."""
        schema = OPUSSearchInputSchema(limit=1000)
        assert schema.limit == 1000

    def test_search_input_startobs_below_one(self):
        """Startobs below 1 raises validation error."""
        with pytest.raises(Exception):
            OPUSSearchInputSchema(startobs=0)

    def test_search_input_startobs_valid(self):
        """Startobs of 1 is valid."""
        schema = OPUSSearchInputSchema(startobs=1)
        assert schema.startobs == 1

    def test_search_input_invalid_mission(self):
        """Invalid mission raises validation error."""
        with pytest.raises(Exception):
            OPUSSearchInputSchema(mission="Invalid Mission")

    def test_search_input_invalid_instrument(self):
        """Invalid instrument raises validation error."""
        with pytest.raises(Exception):
            OPUSSearchInputSchema(instrument="Invalid Instrument")

    def test_search_input_invalid_planet(self):
        """Invalid planet raises validation error."""
        with pytest.raises(Exception):
            OPUSSearchInputSchema(planet="Mars")

    def test_search_input_valid_missions(self):
        """All valid missions are accepted."""
        for mission in ["Cassini", "Voyager 1", "Voyager 2", "Galileo", "New Horizons", "Juno", "Hubble"]:
            schema = OPUSSearchInputSchema(mission=mission)
            assert schema.mission == mission

    def test_search_input_valid_planets(self):
        """All valid planets are accepted."""
        for planet in ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Other"]:
            schema = OPUSSearchInputSchema(planet=planet)
            assert schema.planet == planet

    def test_search_input_valid_instruments(self):
        """Sample valid instruments are accepted."""
        for instrument in ["Cassini ISS", "Cassini VIMS", "Voyager ISS", "Galileo SSI", "Hubble WFC3"]:
            schema = OPUSSearchInputSchema(instrument=instrument)
            assert schema.instrument == instrument

    # --- OPUSCountInputSchema ---

    def test_count_input_defaults(self):
        """CountInputSchema has correct defaults."""
        schema = OPUSCountInputSchema()
        assert schema.target is None
        assert schema.mission is None
        assert schema.instrument is None
        assert schema.planet is None
        assert schema.time_min is None
        assert schema.time_max is None

    def test_count_input_invalid_mission(self):
        """Invalid mission raises validation error."""
        with pytest.raises(Exception):
            OPUSCountInputSchema(mission="Invalid Mission")

    def test_count_input_invalid_planet(self):
        """Invalid planet raises validation error."""
        with pytest.raises(Exception):
            OPUSCountInputSchema(planet="Mars")

    def test_count_input_invalid_instrument(self):
        """Invalid instrument raises validation error."""
        with pytest.raises(Exception):
            OPUSCountInputSchema(instrument="Bad Instrument")

    # --- OPUSGetMetadataInputSchema ---

    def test_get_metadata_input_requires_opusid(self):
        """GetMetadataInputSchema requires opusid."""
        with pytest.raises(Exception):
            OPUSGetMetadataInputSchema()

    def test_get_metadata_input_valid(self):
        """GetMetadataInputSchema accepts a valid opusid."""
        schema = OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
        assert schema.opusid == "co-iss-n1460960653"

    # --- OPUSGetFilesInputSchema ---

    def test_get_files_input_requires_opusid(self):
        """GetFilesInputSchema requires opusid."""
        with pytest.raises(Exception):
            OPUSGetFilesInputSchema()

    def test_get_files_input_valid(self):
        """GetFilesInputSchema accepts a valid opusid."""
        schema = OPUSGetFilesInputSchema(opusid="co-iss-n1460960653")
        assert schema.opusid == "co-iss-n1460960653"


# ---------------------------------------------------------------------------
# Config validation tests
# ---------------------------------------------------------------------------


class TestOPUSConfigValidation:
    """Tests for OPUS tool config defaults and validation."""

    def test_search_config_defaults(self):
        """SearchToolConfig has correct defaults."""
        config = OPUSSearchToolConfig()
        assert "opus" in config.base_url.lower()
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_count_config_defaults(self):
        """CountToolConfig has correct defaults."""
        config = OPUSCountToolConfig()
        assert "opus" in config.base_url.lower()
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_get_metadata_config_defaults(self):
        """GetMetadataToolConfig has correct defaults."""
        config = OPUSGetMetadataToolConfig()
        assert "opus" in config.base_url.lower()
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_get_files_config_defaults(self):
        """GetFilesToolConfig has correct defaults."""
        config = OPUSGetFilesToolConfig()
        assert "opus" in config.base_url.lower()
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_search_config_custom_values(self):
        """SearchToolConfig accepts custom values."""
        config = OPUSSearchToolConfig(
            base_url="https://custom.url/",
            timeout=120.0,
            max_retries=10,
        )
        assert config.base_url == "https://custom.url/"
        assert config.timeout == 120.0
        assert config.max_retries == 10
