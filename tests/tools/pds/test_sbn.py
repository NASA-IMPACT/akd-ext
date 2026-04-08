"""Unit tests for SBN CATCH (Small Bodies Node) tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from akd_ext.tools.pds.sbn.search_object import (
    SBNSearchObjectInputSchema,
    SBNSearchObjectOutputSchema,
    SBNSearchObjectTool,
    SBNSearchObjectToolConfig,
)
from akd_ext.tools.pds.sbn.search_coordinates import (
    SBNSearchCoordinatesInputSchema,
    SBNSearchCoordinatesOutputSchema,
    SBNSearchCoordinatesTool,
    SBNSearchCoordinatesToolConfig,
)
from akd_ext.tools.pds.sbn.list_sources import (
    SBNListSourcesInputSchema,
    SBNListSourcesOutputSchema,
    SBNListSourcesTool,
    SBNListSourcesToolConfig,
    SBNSourceSummary,
)
from akd_ext.tools.pds.sbn.types import ESSENTIAL_FIELDS, FIELD_PROFILES, SUMMARY_FIELDS, filter_observation
from akd_ext.tools.pds.utils.sbn_client import SBNCatchClientError

# Patch paths – must match where SBNCatchClient is looked up at runtime
_SEARCH_OBJECT_CLIENT = "akd_ext.tools.pds.sbn.search_object.SBNCatchClient"
_SEARCH_COORDS_CLIENT = "akd_ext.tools.pds.sbn.search_coordinates.SBNCatchClient"
_LIST_SOURCES_CLIENT = "akd_ext.tools.pds.sbn.list_sources.SBNCatchClient"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_observation(**overrides):
    """Create a mock CatchObservation with sensible defaults.

    Returns a MagicMock that behaves like a Pydantic CatchObservation,
    with model_dump(exclude_none=True) returning a dict of observation fields.
    """
    defaults = {
        "product_id": "neat_obs_001",
        "source": "neat_palomar_tricam",
        "date": "2020-01-15",
        "archive_url": "https://example.com/archive/neat_obs_001",
        "ra": 123.45,
        "dec": -30.5,
        "vmag": 18.5,
        "filter": "V",
        "exposure": 60.0,
    }
    defaults.update(overrides)

    obs = MagicMock()
    for key, value in defaults.items():
        setattr(obs, key, value)

    obs.model_dump = MagicMock(return_value={k: v for k, v in defaults.items() if v is not None})
    return obs


def _make_mock_source_status(**overrides):
    """Create a mock CatchSourceStatus."""
    defaults = {
        "source": "neat_palomar_tricam",
        "status": "success",
        "count": 5,
    }
    defaults.update(overrides)

    status = MagicMock()
    for key, value in defaults.items():
        setattr(status, key, value)
    return status


def _make_mock_results_response(**overrides):
    """Create a mock CatchResultsResponse for search_and_wait."""
    response = MagicMock()
    response.error = overrides.get("error", None)
    response.observations = overrides.get("observations", [_make_mock_observation()])
    response.source_status = overrides.get("source_status", [_make_mock_source_status()])
    return response


def _make_mock_fixed_response(**overrides):
    """Create a mock CatchFixedResponse for search_fixed_target."""
    response = MagicMock()
    response.error = overrides.get("error", None)
    response.observations = overrides.get("observations", [_make_mock_observation()])
    return response


def _make_mock_catch_source(**overrides):
    """Create a mock CatchSource for list_sources."""
    defaults = {
        "source": "neat_palomar_tricam",
        "source_name": "NEAT Palomar Tri-Cam",
        "count": 12345,
        "start_date": "1999-01-01",
        "stop_date": "2007-12-31",
        "nights": 2500,
        "updated": "2024-06-01T00:00:00Z",
    }
    defaults.update(overrides)

    src = MagicMock()
    for key, value in defaults.items():
        setattr(src, key, value)
    return src


def _make_mock_sources_response(**overrides):
    """Create a mock CatchSourcesResponse for list_sources."""
    response = MagicMock()
    response.error = overrides.get("error", None)
    response.sources = overrides.get("sources", [_make_mock_catch_source()])
    return response


# ---------------------------------------------------------------------------
# SBNSearchObjectTool
# ---------------------------------------------------------------------------


class TestSBNSearchObjectTool:
    """Tests for SBNSearchObjectTool."""

    async def test_basic_search(self):
        """Basic search returns observations for a target."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(return_value=_make_mock_results_response())

            tool = SBNSearchObjectTool()
            result = await tool.arun(SBNSearchObjectInputSchema(target="65803"))

        assert isinstance(result, SBNSearchObjectOutputSchema)
        assert result.target == "65803"
        assert result.count == 1
        assert result.total_available == 1
        assert result.has_more is False
        assert len(result.observations) == 1

    async def test_search_forwards_target(self):
        """Target designation is forwarded to the client."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(return_value=_make_mock_results_response())

            tool = SBNSearchObjectTool()
            await tool.arun(SBNSearchObjectInputSchema(target="1P/Halley"))

        call_kwargs = mock_client.search_and_wait.call_args.kwargs
        assert call_kwargs["target"] == "1P/Halley"

    async def test_search_forwards_sources(self):
        """Sources filter is forwarded to the client."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(return_value=_make_mock_results_response())

            tool = SBNSearchObjectTool()
            await tool.arun(
                SBNSearchObjectInputSchema(target="Ceres", sources=["neat_palomar_tricam", "ps1dr2"])
            )

        call_kwargs = mock_client.search_and_wait.call_args.kwargs
        assert call_kwargs["sources"] == ["neat_palomar_tricam", "ps1dr2"]

    async def test_search_forwards_date_range(self):
        """Date range filters are forwarded to the client."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(return_value=_make_mock_results_response())

            tool = SBNSearchObjectTool()
            await tool.arun(
                SBNSearchObjectInputSchema(
                    target="Didymos",
                    start_date="2020-01-01",
                    stop_date="2020-12-31",
                )
            )

        call_kwargs = mock_client.search_and_wait.call_args.kwargs
        assert call_kwargs["start_date"] == "2020-01-01"
        assert call_kwargs["stop_date"] == "2020-12-31"

    async def test_search_forwards_cached_and_timeout(self):
        """Cached and timeout parameters are forwarded to the client."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(return_value=_make_mock_results_response())

            tool = SBNSearchObjectTool()
            await tool.arun(
                SBNSearchObjectInputSchema(target="Vesta", cached=False, timeout=300.0)
            )

        call_kwargs = mock_client.search_and_wait.call_args.kwargs
        assert call_kwargs["cached"] is False
        assert call_kwargs["timeout"] == 300.0

    async def test_search_essential_fields(self):
        """Essential field profile filters observations to minimal fields."""
        obs = _make_mock_observation(
            rh=2.5,
            delta=1.8,
            phase=15.0,
        )
        # Add the extra fields to model_dump output
        dump = obs.model_dump.return_value
        dump["rh"] = 2.5
        dump["delta"] = 1.8
        dump["phase"] = 15.0

        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(
                return_value=_make_mock_results_response(observations=[obs])
            )

            tool = SBNSearchObjectTool()
            result = await tool.arun(
                SBNSearchObjectInputSchema(target="65803", fields="essential")
            )

        assert result.fields == "essential"
        obs_dict = result.observations[0]
        assert "product_id" in obs_dict
        assert "source" in obs_dict
        assert "date" in obs_dict
        assert "archive_url" in obs_dict
        # Summary/full fields should not be present
        assert "ra" not in obs_dict
        assert "vmag" not in obs_dict
        assert "rh" not in obs_dict

    async def test_search_summary_fields(self):
        """Summary field profile includes essential + ra, dec, vmag, filter, exposure."""
        obs = _make_mock_observation(rh=2.5, delta=1.8)
        dump = obs.model_dump.return_value
        dump["rh"] = 2.5
        dump["delta"] = 1.8

        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(
                return_value=_make_mock_results_response(observations=[obs])
            )

            tool = SBNSearchObjectTool()
            result = await tool.arun(
                SBNSearchObjectInputSchema(target="65803", fields="summary")
            )

        assert result.fields == "summary"
        obs_dict = result.observations[0]
        assert "product_id" in obs_dict
        assert "ra" in obs_dict
        assert "dec" in obs_dict
        assert "vmag" in obs_dict
        assert "filter" in obs_dict
        assert "exposure" in obs_dict
        # Full-only fields should not be present
        assert "rh" not in obs_dict
        assert "delta" not in obs_dict

    async def test_search_full_fields(self):
        """Full field profile includes all available fields."""
        obs = _make_mock_observation(
            rh=2.5, delta=1.8, phase=15.0, dra=0.5, ddec=-0.3,
            seeing=2.1, airmass=1.3, maglimit=21.0, cutout_url="https://example.com/cutout",
            preview_url="https://example.com/preview", mjd_start=58863.5,
        )
        dump = obs.model_dump.return_value
        dump.update({
            "rh": 2.5, "delta": 1.8, "phase": 15.0, "dra": 0.5, "ddec": -0.3,
            "seeing": 2.1, "airmass": 1.3, "maglimit": 21.0,
            "cutout_url": "https://example.com/cutout",
            "preview_url": "https://example.com/preview", "mjd_start": 58863.5,
        })

        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(
                return_value=_make_mock_results_response(observations=[obs])
            )

            tool = SBNSearchObjectTool()
            result = await tool.arun(
                SBNSearchObjectInputSchema(target="65803", fields="full")
            )

        assert result.fields == "full"
        obs_dict = result.observations[0]
        assert "product_id" in obs_dict
        assert "ra" in obs_dict
        assert "rh" in obs_dict
        assert "delta" in obs_dict
        assert "phase" in obs_dict
        assert "seeing" in obs_dict
        assert "airmass" in obs_dict
        assert "maglimit" in obs_dict
        assert "cutout_url" in obs_dict
        assert "preview_url" in obs_dict
        assert "mjd_start" in obs_dict

    async def test_search_pagination_has_more(self):
        """Pagination with more results available sets has_more=True."""
        observations = [_make_mock_observation(product_id=f"obs_{i}") for i in range(5)]
        for i, obs in enumerate(observations):
            obs.model_dump.return_value = {
                "product_id": f"obs_{i}",
                "source": "neat_palomar_tricam",
                "date": "2020-01-15",
                "archive_url": f"https://example.com/obs_{i}",
                "ra": 123.45,
                "dec": -30.5,
                "vmag": 18.5,
                "filter": "V",
                "exposure": 60.0,
            }

        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(
                return_value=_make_mock_results_response(observations=observations)
            )

            tool = SBNSearchObjectTool()
            result = await tool.arun(
                SBNSearchObjectInputSchema(target="65803", limit=2, offset=0)
            )

        assert result.count == 2
        assert result.total_available == 5
        assert result.limit == 2
        assert result.offset == 0
        assert result.has_more is True

    async def test_search_pagination_no_more(self):
        """Pagination at end of results sets has_more=False."""
        observations = [_make_mock_observation(product_id=f"obs_{i}") for i in range(3)]
        for i, obs in enumerate(observations):
            obs.model_dump.return_value = {
                "product_id": f"obs_{i}",
                "source": "neat_palomar_tricam",
                "date": "2020-01-15",
                "archive_url": f"https://example.com/obs_{i}",
                "ra": 123.45,
                "dec": -30.5,
            }

        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(
                return_value=_make_mock_results_response(observations=observations)
            )

            tool = SBNSearchObjectTool()
            result = await tool.arun(
                SBNSearchObjectInputSchema(target="65803", limit=10, offset=0)
            )

        assert result.count == 3
        assert result.total_available == 3
        assert result.has_more is False

    async def test_search_pagination_with_offset(self):
        """Offset skips first N observations."""
        observations = [_make_mock_observation(product_id=f"obs_{i}") for i in range(5)]
        for i, obs in enumerate(observations):
            obs.model_dump.return_value = {
                "product_id": f"obs_{i}",
                "source": "neat_palomar_tricam",
                "date": "2020-01-15",
                "archive_url": f"https://example.com/obs_{i}",
                "ra": 123.45,
                "dec": -30.5,
            }

        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(
                return_value=_make_mock_results_response(observations=observations)
            )

            tool = SBNSearchObjectTool()
            result = await tool.arun(
                SBNSearchObjectInputSchema(target="65803", limit=2, offset=3)
            )

        assert result.count == 2
        assert result.total_available == 5
        assert result.offset == 3
        assert result.has_more is False
        assert result.observations[0]["product_id"] == "obs_3"
        assert result.observations[1]["product_id"] == "obs_4"

    async def test_search_source_status(self):
        """Source status is included in the response."""
        source_statuses = [
            _make_mock_source_status(source="neat_palomar_tricam", status="success", count=3),
            _make_mock_source_status(source="ps1dr2", status="success", count=2),
        ]

        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(
                return_value=_make_mock_results_response(source_status=source_statuses)
            )

            tool = SBNSearchObjectTool()
            result = await tool.arun(SBNSearchObjectInputSchema(target="65803"))

        assert len(result.source_status) == 2
        assert result.source_status[0].source == "neat_palomar_tricam"
        assert result.source_status[0].status == "success"
        assert result.source_status[0].count == 3
        assert result.source_status[1].source == "ps1dr2"

    async def test_search_empty_results(self):
        """Empty search returns count=0 and empty observations list."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(
                return_value=_make_mock_results_response(observations=[], source_status=[])
            )

            tool = SBNSearchObjectTool()
            result = await tool.arun(SBNSearchObjectInputSchema(target="nonexistent_object"))

        assert result.count == 0
        assert result.total_available == 0
        assert result.observations == []
        assert result.has_more is False

    async def test_search_response_error_raises(self):
        """Response with error field raises SBNCatchClientError."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(
                return_value=_make_mock_results_response(error="Target not found")
            )

            tool = SBNSearchObjectTool()
            with pytest.raises(SBNCatchClientError, match="Target not found"):
                await tool.arun(SBNSearchObjectInputSchema(target="bad_target"))

    async def test_search_client_error_raises(self):
        """SBNCatchClientError from client is re-raised."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(
                side_effect=SBNCatchClientError("connection failed")
            )

            tool = SBNSearchObjectTool()
            with pytest.raises(SBNCatchClientError, match="connection failed"):
                await tool.arun(SBNSearchObjectInputSchema(target="65803"))

    async def test_search_unexpected_error_raises_runtime_error(self):
        """Unexpected exceptions are wrapped in RuntimeError."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(side_effect=TypeError("bad type"))

            tool = SBNSearchObjectTool()
            with pytest.raises(RuntimeError, match="Internal error"):
                await tool.arun(SBNSearchObjectInputSchema(target="65803"))

    async def test_search_with_config(self):
        """Custom config values are passed to the client."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(return_value=_make_mock_results_response())

            config = SBNSearchObjectToolConfig(
                base_url="https://custom.api.url/",
                timeout=30.0,
                max_retries=5,
            )
            tool = SBNSearchObjectTool(config=config)
            await tool.arun(SBNSearchObjectInputSchema(target="65803"))

        MockClient.assert_called_once_with(
            base_url="https://custom.api.url/",
            timeout=30.0,
            max_retries=5,
        )

    async def test_search_all_filters_combined(self):
        """All search parameters are forwarded to the client."""
        with patch(_SEARCH_OBJECT_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_and_wait = AsyncMock(return_value=_make_mock_results_response())

            tool = SBNSearchObjectTool()
            result = await tool.arun(
                SBNSearchObjectInputSchema(
                    target="1P/Halley",
                    sources=["neat_palomar_tricam"],
                    start_date="2000-01-01",
                    stop_date="2010-12-31",
                    cached=False,
                    timeout=180.0,
                    limit=5,
                    offset=2,
                    fields="full",
                )
            )

        call_kwargs = mock_client.search_and_wait.call_args.kwargs
        assert call_kwargs["target"] == "1P/Halley"
        assert call_kwargs["sources"] == ["neat_palomar_tricam"]
        assert call_kwargs["start_date"] == "2000-01-01"
        assert call_kwargs["stop_date"] == "2010-12-31"
        assert call_kwargs["cached"] is False
        assert call_kwargs["timeout"] == 180.0
        assert result.fields == "full"
        assert result.offset == 2
        assert result.limit == 5


# ---------------------------------------------------------------------------
# SBNSearchCoordinatesTool
# ---------------------------------------------------------------------------


class TestSBNSearchCoordinatesTool:
    """Tests for SBNSearchCoordinatesTool."""

    async def test_basic_search(self):
        """Basic coordinate search returns observations."""
        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(return_value=_make_mock_fixed_response())

            tool = SBNSearchCoordinatesTool()
            result = await tool.arun(
                SBNSearchCoordinatesInputSchema(ra="12:34:56.7", dec="-30:15:00.0")
            )

        assert isinstance(result, SBNSearchCoordinatesOutputSchema)
        assert result.ra == "12:34:56.7"
        assert result.dec == "-30:15:00.0"
        assert result.radius == 10.0  # default
        assert result.count == 1
        assert result.total_available == 1
        assert result.has_more is False
        assert len(result.observations) == 1

    async def test_search_forwards_coordinates(self):
        """RA, Dec, and radius are forwarded to the client."""
        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(return_value=_make_mock_fixed_response())

            tool = SBNSearchCoordinatesTool()
            await tool.arun(
                SBNSearchCoordinatesInputSchema(ra="185.5", dec="45.2", radius=30.0)
            )

        call_kwargs = mock_client.search_fixed_target.call_args.kwargs
        assert call_kwargs["ra"] == "185.5"
        assert call_kwargs["dec"] == "45.2"
        assert call_kwargs["radius"] == 30.0

    async def test_search_forwards_sources(self):
        """Sources filter is forwarded to the client."""
        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(return_value=_make_mock_fixed_response())

            tool = SBNSearchCoordinatesTool()
            await tool.arun(
                SBNSearchCoordinatesInputSchema(
                    ra="123.45", dec="-30.5", sources=["ps1dr2", "skymapper_dr4"]
                )
            )

        call_kwargs = mock_client.search_fixed_target.call_args.kwargs
        assert call_kwargs["sources"] == ["ps1dr2", "skymapper_dr4"]

    async def test_search_forwards_date_range(self):
        """Date range filters are forwarded to the client."""
        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(return_value=_make_mock_fixed_response())

            tool = SBNSearchCoordinatesTool()
            await tool.arun(
                SBNSearchCoordinatesInputSchema(
                    ra="123.45",
                    dec="-30.5",
                    start_date="2015-01-01",
                    stop_date="2020-12-31",
                )
            )

        call_kwargs = mock_client.search_fixed_target.call_args.kwargs
        assert call_kwargs["start_date"] == "2015-01-01"
        assert call_kwargs["stop_date"] == "2020-12-31"

    async def test_search_essential_fields(self):
        """Essential field profile filters to minimal fields."""
        obs = _make_mock_observation(rh=2.5, vmag=18.5)
        dump = obs.model_dump.return_value
        dump["rh"] = 2.5

        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(
                return_value=_make_mock_fixed_response(observations=[obs])
            )

            tool = SBNSearchCoordinatesTool()
            result = await tool.arun(
                SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5", fields="essential")
            )

        assert result.fields == "essential"
        obs_dict = result.observations[0]
        assert "product_id" in obs_dict
        assert "source" in obs_dict
        assert "date" in obs_dict
        assert "archive_url" in obs_dict
        assert "ra" not in obs_dict
        assert "vmag" not in obs_dict
        assert "rh" not in obs_dict

    async def test_search_summary_fields(self):
        """Summary field profile includes essential + key observation fields."""
        obs = _make_mock_observation(rh=2.5)
        dump = obs.model_dump.return_value
        dump["rh"] = 2.5

        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(
                return_value=_make_mock_fixed_response(observations=[obs])
            )

            tool = SBNSearchCoordinatesTool()
            result = await tool.arun(
                SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5", fields="summary")
            )

        obs_dict = result.observations[0]
        assert "product_id" in obs_dict
        assert "ra" in obs_dict
        assert "dec" in obs_dict
        assert "vmag" in obs_dict
        assert "filter" in obs_dict
        assert "exposure" in obs_dict
        assert "rh" not in obs_dict

    async def test_search_full_fields(self):
        """Full field profile includes all available fields."""
        obs = _make_mock_observation(
            rh=2.5, delta=1.8, phase=15.0, seeing=2.1, airmass=1.3,
            maglimit=21.0, mjd_start=58863.5,
        )
        dump = obs.model_dump.return_value
        dump.update({
            "rh": 2.5, "delta": 1.8, "phase": 15.0,
            "seeing": 2.1, "airmass": 1.3, "maglimit": 21.0, "mjd_start": 58863.5,
        })

        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(
                return_value=_make_mock_fixed_response(observations=[obs])
            )

            tool = SBNSearchCoordinatesTool()
            result = await tool.arun(
                SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5", fields="full")
            )

        obs_dict = result.observations[0]
        assert "rh" in obs_dict
        assert "delta" in obs_dict
        assert "phase" in obs_dict
        assert "seeing" in obs_dict
        assert "airmass" in obs_dict
        assert "maglimit" in obs_dict
        assert "mjd_start" in obs_dict

    async def test_search_pagination_has_more(self):
        """Pagination with more results sets has_more=True."""
        observations = [_make_mock_observation(product_id=f"fixed_{i}") for i in range(5)]
        for i, obs in enumerate(observations):
            obs.model_dump.return_value = {
                "product_id": f"fixed_{i}",
                "source": "ps1dr2",
                "date": "2018-06-15",
                "archive_url": f"https://example.com/fixed_{i}",
                "ra": 185.5,
                "dec": 45.2,
            }

        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(
                return_value=_make_mock_fixed_response(observations=observations)
            )

            tool = SBNSearchCoordinatesTool()
            result = await tool.arun(
                SBNSearchCoordinatesInputSchema(ra="185.5", dec="45.2", limit=2, offset=0)
            )

        assert result.count == 2
        assert result.total_available == 5
        assert result.has_more is True

    async def test_search_pagination_no_more(self):
        """Pagination at end of results sets has_more=False."""
        observations = [_make_mock_observation(product_id=f"fixed_{i}") for i in range(3)]
        for i, obs in enumerate(observations):
            obs.model_dump.return_value = {
                "product_id": f"fixed_{i}",
                "source": "ps1dr2",
                "date": "2018-06-15",
                "archive_url": f"https://example.com/fixed_{i}",
            }

        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(
                return_value=_make_mock_fixed_response(observations=observations)
            )

            tool = SBNSearchCoordinatesTool()
            result = await tool.arun(
                SBNSearchCoordinatesInputSchema(ra="185.5", dec="45.2", limit=10, offset=0)
            )

        assert result.count == 3
        assert result.total_available == 3
        assert result.has_more is False

    async def test_search_pagination_with_offset(self):
        """Offset skips first N observations."""
        observations = [_make_mock_observation(product_id=f"fixed_{i}") for i in range(5)]
        for i, obs in enumerate(observations):
            obs.model_dump.return_value = {
                "product_id": f"fixed_{i}",
                "source": "ps1dr2",
                "date": "2018-06-15",
                "archive_url": f"https://example.com/fixed_{i}",
                "ra": 185.5,
                "dec": 45.2,
            }

        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(
                return_value=_make_mock_fixed_response(observations=observations)
            )

            tool = SBNSearchCoordinatesTool()
            result = await tool.arun(
                SBNSearchCoordinatesInputSchema(ra="185.5", dec="45.2", limit=2, offset=4)
            )

        assert result.count == 1
        assert result.total_available == 5
        assert result.offset == 4
        assert result.has_more is False
        assert result.observations[0]["product_id"] == "fixed_4"

    async def test_search_empty_results(self):
        """Empty search returns count=0 and empty observations."""
        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(
                return_value=_make_mock_fixed_response(observations=[])
            )

            tool = SBNSearchCoordinatesTool()
            result = await tool.arun(
                SBNSearchCoordinatesInputSchema(ra="0.0", dec="90.0")
            )

        assert result.count == 0
        assert result.total_available == 0
        assert result.observations == []
        assert result.has_more is False

    async def test_search_response_error_raises(self):
        """Response with error field raises SBNCatchClientError."""
        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(
                return_value=_make_mock_fixed_response(error="Invalid coordinates")
            )

            tool = SBNSearchCoordinatesTool()
            with pytest.raises(SBNCatchClientError, match="Invalid coordinates"):
                await tool.arun(
                    SBNSearchCoordinatesInputSchema(ra="bad", dec="bad")
                )

    async def test_search_client_error_raises(self):
        """SBNCatchClientError from client is re-raised."""
        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(
                side_effect=SBNCatchClientError("API timeout")
            )

            tool = SBNSearchCoordinatesTool()
            with pytest.raises(SBNCatchClientError, match="API timeout"):
                await tool.arun(
                    SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5")
                )

    async def test_search_unexpected_error_raises_runtime_error(self):
        """Unexpected exceptions are wrapped in RuntimeError."""
        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(side_effect=ValueError("bad value"))

            tool = SBNSearchCoordinatesTool()
            with pytest.raises(RuntimeError, match="Internal error"):
                await tool.arun(
                    SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5")
                )

    async def test_search_with_config(self):
        """Custom config values are passed to the client."""
        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(return_value=_make_mock_fixed_response())

            config = SBNSearchCoordinatesToolConfig(
                base_url="https://custom.url/",
                timeout=90.0,
                max_retries=2,
            )
            tool = SBNSearchCoordinatesTool(config=config)
            await tool.arun(SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5"))

        MockClient.assert_called_once_with(
            base_url="https://custom.url/",
            timeout=90.0,
            max_retries=2,
        )

    async def test_search_all_filters_combined(self):
        """All search parameters are forwarded to the client."""
        with patch(_SEARCH_COORDS_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.search_fixed_target = AsyncMock(return_value=_make_mock_fixed_response())

            tool = SBNSearchCoordinatesTool()
            result = await tool.arun(
                SBNSearchCoordinatesInputSchema(
                    ra="12:34:56.7",
                    dec="+45:30:00.0",
                    radius=60.0,
                    sources=["neat_palomar_tricam", "catalina_bigelow"],
                    start_date="2005-01-01",
                    stop_date="2015-12-31",
                    limit=5,
                    offset=3,
                    fields="essential",
                )
            )

        call_kwargs = mock_client.search_fixed_target.call_args.kwargs
        assert call_kwargs["ra"] == "12:34:56.7"
        assert call_kwargs["dec"] == "+45:30:00.0"
        assert call_kwargs["radius"] == 60.0
        assert call_kwargs["sources"] == ["neat_palomar_tricam", "catalina_bigelow"]
        assert call_kwargs["start_date"] == "2005-01-01"
        assert call_kwargs["stop_date"] == "2015-12-31"
        assert result.fields == "essential"
        assert result.offset == 3
        assert result.limit == 5


# ---------------------------------------------------------------------------
# SBNListSourcesTool
# ---------------------------------------------------------------------------


class TestSBNListSourcesTool:
    """Tests for SBNListSourcesTool."""

    async def test_basic_list(self):
        """List sources returns available data sources."""
        sources = [
            _make_mock_catch_source(
                source="neat_palomar_tricam",
                source_name="NEAT Palomar Tri-Cam",
                count=12345,
                start_date="1999-01-01",
                stop_date="2007-12-31",
                nights=2500,
                updated="2024-06-01T00:00:00Z",
            ),
            _make_mock_catch_source(
                source="ps1dr2",
                source_name="Pan-STARRS 1 DR2",
                count=98765,
                start_date="2010-05-01",
                stop_date="2014-03-31",
                nights=1200,
                updated="2024-06-15T00:00:00Z",
            ),
        ]

        with patch(_LIST_SOURCES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_sources = AsyncMock(
                return_value=_make_mock_sources_response(sources=sources)
            )

            tool = SBNListSourcesTool()
            result = await tool.arun(SBNListSourcesInputSchema())

        assert isinstance(result, SBNListSourcesOutputSchema)
        assert result.total_sources == 2
        assert len(result.sources) == 2

        neat = result.sources[0]
        assert isinstance(neat, SBNSourceSummary)
        assert neat.source == "neat_palomar_tricam"
        assert neat.source_name == "NEAT Palomar Tri-Cam"
        assert neat.count == 12345
        assert neat.start_date == "1999-01-01"
        assert neat.stop_date == "2007-12-31"
        assert neat.nights == 2500
        assert neat.updated == "2024-06-01T00:00:00Z"

        ps1 = result.sources[1]
        assert ps1.source == "ps1dr2"
        assert ps1.source_name == "Pan-STARRS 1 DR2"
        assert ps1.count == 98765

    async def test_list_empty_sources(self):
        """Empty sources list returns total_sources=0."""
        with patch(_LIST_SOURCES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_sources = AsyncMock(
                return_value=_make_mock_sources_response(sources=[])
            )

            tool = SBNListSourcesTool()
            result = await tool.arun(SBNListSourcesInputSchema())

        assert result.total_sources == 0
        assert result.sources == []

    async def test_list_response_error_raises(self):
        """Response with error field raises SBNCatchClientError."""
        with patch(_LIST_SOURCES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_sources = AsyncMock(
                return_value=_make_mock_sources_response(error="Service unavailable")
            )

            tool = SBNListSourcesTool()
            with pytest.raises(SBNCatchClientError, match="Service unavailable"):
                await tool.arun(SBNListSourcesInputSchema())

    async def test_list_client_error_raises(self):
        """SBNCatchClientError from client is re-raised."""
        with patch(_LIST_SOURCES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_sources = AsyncMock(
                side_effect=SBNCatchClientError("request failed")
            )

            tool = SBNListSourcesTool()
            with pytest.raises(SBNCatchClientError, match="request failed"):
                await tool.arun(SBNListSourcesInputSchema())

    async def test_list_unexpected_error_raises_runtime_error(self):
        """Unexpected exceptions are wrapped in RuntimeError."""
        with patch(_LIST_SOURCES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_sources = AsyncMock(side_effect=OSError("network error"))

            tool = SBNListSourcesTool()
            with pytest.raises(RuntimeError, match="Internal error"):
                await tool.arun(SBNListSourcesInputSchema())

    async def test_list_with_config(self):
        """Custom config values are passed to the client."""
        with patch(_LIST_SOURCES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_sources = AsyncMock(return_value=_make_mock_sources_response())

            config = SBNListSourcesToolConfig(
                base_url="https://custom.catch.url/",
                timeout=45.0,
                max_retries=1,
            )
            tool = SBNListSourcesTool(config=config)
            await tool.arun(SBNListSourcesInputSchema())

        MockClient.assert_called_once_with(
            base_url="https://custom.catch.url/",
            timeout=45.0,
            max_retries=1,
        )

    async def test_list_source_with_none_optional_fields(self):
        """Sources with None optional fields are handled gracefully."""
        src = _make_mock_catch_source(
            source="spacewatch_0.9m",
            source_name=None,
            count=500,
            start_date=None,
            stop_date=None,
            nights=None,
            updated=None,
        )

        with patch(_LIST_SOURCES_CLIENT) as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.list_sources = AsyncMock(
                return_value=_make_mock_sources_response(sources=[src])
            )

            tool = SBNListSourcesTool()
            result = await tool.arun(SBNListSourcesInputSchema())

        assert result.total_sources == 1
        source = result.sources[0]
        assert source.source == "spacewatch_0.9m"
        assert source.source_name is None
        assert source.count == 500
        assert source.start_date is None
        assert source.stop_date is None
        assert source.nights is None
        assert source.updated is None


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestSBNSchemaValidation:
    """Tests for SBN input schema validation."""

    def test_search_object_input_requires_target(self):
        """SBNSearchObjectInputSchema requires target."""
        with pytest.raises(Exception):
            SBNSearchObjectInputSchema()

    def test_search_object_input_defaults(self):
        """SBNSearchObjectInputSchema has correct defaults."""
        schema = SBNSearchObjectInputSchema(target="65803")
        assert schema.target == "65803"
        assert schema.sources is None
        assert schema.start_date is None
        assert schema.stop_date is None
        assert schema.cached is True
        assert schema.timeout == 120.0
        assert schema.limit == 10
        assert schema.offset == 0
        assert schema.fields == "summary"

    def test_search_object_input_limit_bounds(self):
        """Limit must be between 1 and 10."""
        with pytest.raises(Exception):
            SBNSearchObjectInputSchema(target="65803", limit=0)
        with pytest.raises(Exception):
            SBNSearchObjectInputSchema(target="65803", limit=11)

    def test_search_object_input_offset_non_negative(self):
        """Offset must be >= 0."""
        with pytest.raises(Exception):
            SBNSearchObjectInputSchema(target="65803", offset=-1)

    def test_search_object_input_invalid_fields(self):
        """Invalid fields value raises validation error."""
        with pytest.raises(Exception):
            SBNSearchObjectInputSchema(target="65803", fields="invalid")

    def test_search_object_input_timeout_bounds(self):
        """Timeout must be > 0 and <= 600."""
        with pytest.raises(Exception):
            SBNSearchObjectInputSchema(target="65803", timeout=0)
        with pytest.raises(Exception):
            SBNSearchObjectInputSchema(target="65803", timeout=601)

    def test_search_coordinates_input_requires_ra_dec(self):
        """SBNSearchCoordinatesInputSchema requires ra and dec."""
        with pytest.raises(Exception):
            SBNSearchCoordinatesInputSchema()
        with pytest.raises(Exception):
            SBNSearchCoordinatesInputSchema(ra="123.45")
        with pytest.raises(Exception):
            SBNSearchCoordinatesInputSchema(dec="-30.5")

    def test_search_coordinates_input_defaults(self):
        """SBNSearchCoordinatesInputSchema has correct defaults."""
        schema = SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5")
        assert schema.ra == "123.45"
        assert schema.dec == "-30.5"
        assert schema.radius == 10.0
        assert schema.sources is None
        assert schema.start_date is None
        assert schema.stop_date is None
        assert schema.limit == 10
        assert schema.offset == 0
        assert schema.fields == "summary"

    def test_search_coordinates_input_limit_bounds(self):
        """Limit must be between 1 and 10."""
        with pytest.raises(Exception):
            SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5", limit=0)
        with pytest.raises(Exception):
            SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5", limit=11)

    def test_search_coordinates_input_radius_bounds(self):
        """Radius must be > 0 and <= 120."""
        with pytest.raises(Exception):
            SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5", radius=0)
        with pytest.raises(Exception):
            SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5", radius=121)

    def test_search_coordinates_input_offset_non_negative(self):
        """Offset must be >= 0."""
        with pytest.raises(Exception):
            SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5", offset=-1)

    def test_search_coordinates_input_invalid_fields(self):
        """Invalid fields value raises validation error."""
        with pytest.raises(Exception):
            SBNSearchCoordinatesInputSchema(ra="123.45", dec="-30.5", fields="invalid")

    def test_list_sources_input_no_params(self):
        """SBNListSourcesInputSchema takes no parameters."""
        schema = SBNListSourcesInputSchema()
        assert schema is not None


# ---------------------------------------------------------------------------
# Types and helpers tests
# ---------------------------------------------------------------------------


class TestSBNTypes:
    """Tests for SBN shared types and helper functions."""

    def test_field_profiles_keys(self):
        """FIELD_PROFILES contains essential, summary, and full profiles."""
        assert "essential" in FIELD_PROFILES
        assert "summary" in FIELD_PROFILES
        assert "full" in FIELD_PROFILES

    def test_essential_fields_subset_of_summary(self):
        """Essential fields are a subset of summary fields."""
        assert ESSENTIAL_FIELDS.issubset(SUMMARY_FIELDS)

    def test_summary_fields_subset_of_full(self):
        """Summary fields are a subset of full fields."""
        full_fields = FIELD_PROFILES["full"]
        assert SUMMARY_FIELDS.issubset(full_fields)

    def test_filter_observation_essential(self):
        """filter_observation with essential fields returns only essential keys."""
        obs_dict = {
            "product_id": "obs_001",
            "source": "neat_palomar_tricam",
            "date": "2020-01-15",
            "archive_url": "https://example.com",
            "ra": 123.45,
            "dec": -30.5,
            "vmag": 18.5,
            "rh": 2.5,
        }
        filtered = filter_observation(obs_dict, ESSENTIAL_FIELDS)
        assert set(filtered.keys()) == {"product_id", "source", "date", "archive_url"}

    def test_filter_observation_excludes_none(self):
        """filter_observation excludes None values."""
        obs_dict = {
            "product_id": "obs_001",
            "source": "neat_palomar_tricam",
            "date": None,
            "archive_url": "https://example.com",
        }
        filtered = filter_observation(obs_dict, ESSENTIAL_FIELDS)
        assert "date" not in filtered
        assert "product_id" in filtered

    def test_filter_observation_summary(self):
        """filter_observation with summary fields returns essential + summary keys."""
        obs_dict = {
            "product_id": "obs_001",
            "source": "neat_palomar_tricam",
            "date": "2020-01-15",
            "archive_url": "https://example.com",
            "ra": 123.45,
            "dec": -30.5,
            "vmag": 18.5,
            "filter": "V",
            "exposure": 60.0,
            "rh": 2.5,
            "delta": 1.8,
        }
        filtered = filter_observation(obs_dict, SUMMARY_FIELDS)
        assert "product_id" in filtered
        assert "ra" in filtered
        assert "vmag" in filtered
        assert "filter" in filtered
        assert "exposure" in filtered
        assert "rh" not in filtered
        assert "delta" not in filtered

    def test_filter_observation_full(self):
        """filter_observation with full fields returns all recognized keys."""
        full_fields = FIELD_PROFILES["full"]
        obs_dict = {
            "product_id": "obs_001",
            "source": "neat_palomar_tricam",
            "date": "2020-01-15",
            "archive_url": "https://example.com",
            "ra": 123.45,
            "dec": -30.5,
            "vmag": 18.5,
            "rh": 2.5,
            "delta": 1.8,
            "phase": 15.0,
            "dra": 0.5,
            "ddec": -0.3,
            "seeing": 2.1,
            "airmass": 1.3,
            "maglimit": 21.0,
            "cutout_url": "https://example.com/cutout",
            "preview_url": "https://example.com/preview",
            "mjd_start": 58863.5,
            "unknown_field": "should_be_excluded",
        }
        filtered = filter_observation(obs_dict, full_fields)
        assert "rh" in filtered
        assert "delta" in filtered
        assert "phase" in filtered
        assert "seeing" in filtered
        assert "airmass" in filtered
        assert "maglimit" in filtered
        assert "cutout_url" in filtered
        assert "preview_url" in filtered
        assert "mjd_start" in filtered
        assert "unknown_field" not in filtered
