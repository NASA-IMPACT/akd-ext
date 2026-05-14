"""Tests for the EONET Search Tool."""

from datetime import date, datetime, timedelta, timezone

import pytest
from akd_ext.structures import EONETCategory, EONETStatus
from akd_ext.tools import (
    EONETEvent,
    EONETSearchInputSchema,
    EONETSearchTool,
    EONETSearchToolConfig,
)


# ── Unit tests: input schema validation (no network) ────────────────────────


@pytest.mark.unit
def test_input_rejects_days_with_start_end():
    """days and explicit start/end are mutually exclusive."""
    with pytest.raises(ValueError, match="Use either 'days' or"):
        EONETSearchInputSchema(days=7, start=date(2026, 1, 1), end=date(2026, 1, 31))


@pytest.mark.unit
def test_input_requires_paired_start_end():
    """start without end (and vice-versa) is invalid."""
    with pytest.raises(ValueError, match="must be provided together"):
        EONETSearchInputSchema(start=date(2026, 1, 1))
    with pytest.raises(ValueError, match="must be provided together"):
        EONETSearchInputSchema(end=date(2026, 1, 31))


@pytest.mark.unit
def test_input_rejects_start_after_end():
    """start must be on or before end."""
    with pytest.raises(ValueError, match="must be on or before"):
        EONETSearchInputSchema(start=date(2026, 2, 1), end=date(2026, 1, 1))


@pytest.mark.unit
def test_input_rejects_bbox_out_of_range():
    """bbox lon/lat must be valid Earth coordinates."""
    with pytest.raises(ValueError, match="Longitudes must be in"):
        EONETSearchInputSchema(bbox=(200.0, 0.0, 210.0, 10.0))
    with pytest.raises(ValueError, match="Latitudes must be in"):
        EONETSearchInputSchema(bbox=(0.0, -100.0, 10.0, 10.0))


@pytest.mark.unit
def test_input_rejects_inverted_bbox():
    """min must be <= max for both axes."""
    with pytest.raises(ValueError, match="min_lon, min_lat, max_lon, max_lat"):
        EONETSearchInputSchema(bbox=(10.0, 0.0, -10.0, 5.0))


@pytest.mark.unit
def test_input_magnitude_requires_id():
    """magnitude_min/max are unusable without a magnitude_id."""
    with pytest.raises(ValueError, match="magnitude_id is required"):
        EONETSearchInputSchema(magnitude_min=10.0)
    with pytest.raises(ValueError, match="magnitude_id is required"):
        EONETSearchInputSchema(magnitude_max=100.0)


@pytest.mark.unit
def test_input_accepts_valid_combinations():
    """Sanity-check that legal combinations parse cleanly."""
    # Just days
    EONETSearchInputSchema(category=EONETCategory.WILDFIRES, days=30, limit=5)
    # Date range
    EONETSearchInputSchema(start=date(2026, 1, 1), end=date(2026, 2, 1))
    # bbox + magnitude
    EONETSearchInputSchema(
        bbox=(-130.0, 20.0, -60.0, 50.0),
        magnitude_id="kts",
        magnitude_min=34.0,
    )


@pytest.mark.unit
def test_tool_metadata():
    """Tool name auto-derives from class name; description comes from docstring."""
    tool = EONETSearchTool()
    assert tool.name == "eonet_search_tool"
    assert tool.description
    assert "EONET" in tool.description


# ── Integration tests: live EONET API ────────────────────────────────────────


@pytest.mark.integration
async def test_basic_open_events():
    """Default open-events query returns parsed events with required fields."""
    tool = EONETSearchTool()
    result = await tool.arun(EONETSearchInputSchema(days=30, limit=5))

    assert result.results is not None
    assert isinstance(result.results, list)
    assert len(result.results) <= 5

    for ev in result.results:
        assert isinstance(ev, EONETEvent)
        assert ev.id.startswith("EONET_")
        assert ev.title
        assert ev.link.startswith("https://eonet.gsfc.nasa.gov/")
        assert ev.categories, f"Event {ev.id} has no categories"
        assert ev.sources, f"Event {ev.id} has no sources (provenance missing)"
        assert ev.geometry, f"Event {ev.id} has no geometry"

    assert result.extra is not None
    assert "request_url" in result.extra
    assert "params_echo" in result.extra


@pytest.mark.integration
async def test_category_filter_wildfires():
    """category=wildfires returns only wildfire events."""
    tool = EONETSearchTool()
    result = await tool.arun(EONETSearchInputSchema(category=EONETCategory.WILDFIRES, days=60, limit=10))

    assert result.results is not None
    for ev in result.results:
        category_ids = [c.id for c in ev.categories]
        assert "wildfires" in category_ids, f"Event {ev.id} has categories {category_ids}"


@pytest.mark.integration
async def test_status_closed_events():
    """status=closed returns only events that have a closure timestamp."""
    tool = EONETSearchTool()
    result = await tool.arun(EONETSearchInputSchema(status=EONETStatus.CLOSED, days=90, limit=5))

    assert result.results is not None
    for ev in result.results:
        assert ev.closed is not None, f"Event {ev.id} marked closed but has no closed timestamp"
        assert isinstance(ev.closed, datetime)


@pytest.mark.integration
async def test_status_all_events():
    """status=all is accepted and returns a mix (or at least events)."""
    tool = EONETSearchTool()
    result = await tool.arun(EONETSearchInputSchema(status=EONETStatus.ALL, days=30, limit=5))
    assert result.results is not None


@pytest.mark.integration
async def test_date_range_filter():
    """Explicit start/end is accepted and returns events with timestamps in range."""
    tool = EONETSearchTool()
    end = date.today()
    start = end - timedelta(days=60)
    result = await tool.arun(
        EONETSearchInputSchema(
            status=EONETStatus.ALL,
            start=start,
            end=end,
            limit=5,
        )
    )

    assert result.results is not None
    # When events are returned, their geometry timestamps should overlap the requested window.
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    for ev in result.results:
        assert ev.t_start is not None and ev.t_end is not None
        # Geometry window should overlap requested window (>= start and <= end).
        assert ev.t_end >= start_dt
        assert ev.t_start <= end_dt


@pytest.mark.integration
async def test_bbox_filter_pacific():
    """A Pacific bbox should constrain returned event geometries to within (or overlapping) it."""
    tool = EONETSearchTool()
    # Wide Pacific window — high chance of severe storms / volcanoes.
    bbox = (100.0, -30.0, 180.0, 30.0)
    result = await tool.arun(EONETSearchInputSchema(status=EONETStatus.OPEN, days=60, bbox=bbox, limit=5))

    assert result.results is not None
    # The API filters server-side. We verify each returned event's bbox overlaps our request.
    req_min_lon, req_min_lat, req_max_lon, req_max_lat = bbox
    for ev in result.results:
        assert ev.bbox is not None, f"Event {ev.id} has no derived bbox"
        ev_min_lon, ev_min_lat, ev_max_lon, ev_max_lat = ev.bbox
        # Standard bbox overlap test
        overlap = (
            ev_min_lon <= req_max_lon
            and ev_max_lon >= req_min_lon
            and ev_min_lat <= req_max_lat
            and ev_max_lat >= req_min_lat
        )
        assert overlap, f"Event {ev.id} bbox {ev.bbox} does not overlap request bbox {bbox}"


@pytest.mark.integration
async def test_limit_parameter_respected():
    """The 'limit' field caps the result count."""
    tool = EONETSearchTool()
    result = await tool.arun(EONETSearchInputSchema(status=EONETStatus.ALL, days=30, limit=3))
    assert result.results is not None
    assert len(result.results) <= 3


@pytest.mark.integration
async def test_derived_envelope_populated():
    """Derived bbox / t_start / t_end are populated and consistent with geometry."""
    tool = EONETSearchTool()
    result = await tool.arun(EONETSearchInputSchema(days=30, limit=5))

    for ev in result.results:
        assert ev.bbox is not None, f"Event {ev.id} should have a derived bbox"
        assert ev.t_start is not None and ev.t_end is not None
        assert ev.t_start <= ev.t_end

        # bbox should enclose every Point geometry's coordinates
        min_lon, min_lat, max_lon, max_lat = ev.bbox
        for g in ev.geometry:
            if g.type == "Point":
                lon, lat = g.coordinates[0], g.coordinates[1]
                assert min_lon <= lon <= max_lon, f"Event {ev.id}: point lon {lon} outside derived bbox lon range"
                assert min_lat <= lat <= max_lat, f"Event {ev.id}: point lat {lat} outside derived bbox lat range"


@pytest.mark.integration
async def test_no_results_for_narrow_window():
    """A tiny bbox over open ocean for a short window may return 0 results — must not error."""
    tool = EONETSearchTool()
    # 0.1°-by-0.1° box in mid-Atlantic, 1-day window
    result = await tool.arun(
        EONETSearchInputSchema(
            status=EONETStatus.OPEN,
            days=1,
            bbox=(-30.0, 0.0, -29.9, 0.1),
            limit=5,
        )
    )
    assert result.results is not None
    assert isinstance(result.results, list)


@pytest.mark.integration
async def test_config_sources_filter():
    """Configuring sources= scopes the request to those upstream providers."""
    config = EONETSearchToolConfig(sources=["InciWeb"])
    tool = EONETSearchTool(config=config)
    result = await tool.arun(EONETSearchInputSchema(category=EONETCategory.WILDFIRES, days=60, limit=5))

    assert result.results is not None
    # Every returned event should have at least one InciWeb source entry
    for ev in result.results:
        source_ids = [s.id for s in ev.sources]
        assert "InciWeb" in source_ids, f"Event {ev.id} sources {source_ids} missing InciWeb"


@pytest.mark.integration
async def test_extra_metadata_shape():
    """`extra` carries total_count, request_url, and the echoed params."""
    tool = EONETSearchTool()
    result = await tool.arun(EONETSearchInputSchema(days=14, limit=3))

    assert result.extra is not None
    assert result.extra.get("total_count") == len(result.results)
    assert "events" in result.extra.get("request_url", "")
    params = result.extra.get("params_echo", {})
    assert params.get("days") == "14"
    assert params.get("limit") == "3"
