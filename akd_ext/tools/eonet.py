"""
NASA EONET (Earth Observatory Natural Event Tracker) v3 search tool.

This tool wraps the EONET v3 /events endpoint to enable filtering natural events
(wildfires, severe storms, volcanoes, floods, earthquakes, sea/lake ice,
landslides, etc.) by category, lifecycle status, time range, geographic bounding
box, and magnitude. Each returned event carries its full geometry timeline,
upstream source provenance, and derived spatiotemporal envelopes (bbox, t_start,
t_end) that downstream tools (CMR queries, Worldview deep links) can consume
directly.

EONET aggregates event metadata from authoritative providers (USGS, JTWC,
InciWeb, SI Volcano, etc.). The API is public and requires no authentication.
See https://eonet.gsfc.nasa.gov/docs/v3.
"""

import os
from collections.abc import Iterable
from datetime import date, datetime
from typing import Any, Literal

import httpx
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from loguru import logger
from pydantic import BaseModel, Field, model_validator

from akd_ext.mcp import mcp_tool
from akd_ext.structures import EONETCategory, EONETStatus


class EONETSearchToolConfig(BaseToolConfig):
    """Instance-level configuration for EONETSearchTool."""

    base_url: str = Field(
        default=os.getenv("EONET_BASE_URL", "https://eonet.gsfc.nasa.gov/api/v3"),
        description="Base URL for the EONET v3 API.",
    )
    timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds.",
    )
    sources: list[str] | None = Field(
        default=None,
        description=(
            "Optional allowlist of EONET source IDs (e.g., ['InciWeb', 'USGS_EHP']). "
            "If set, all queries are scoped to these upstream sources."
        ),
    )


class EONETSource(BaseModel):
    """An upstream data provider entry attached to an EONET event."""

    id: str = Field(..., description="Source ID (e.g., 'InciWeb', 'USGS_EHP', 'JTWC').")
    url: str = Field(..., description="Upstream provider URL for this event (provenance).")


class EONETCategoryRef(BaseModel):
    """A category assignment on an EONET event."""

    id: str = Field(..., description="Category ID (e.g., 'wildfires').")
    title: str = Field(..., description="Human-readable category title (e.g., 'Wildfires').")


class EONETGeometry(BaseModel):
    """A single time-stamped geometry observation for an EONET event."""

    date: datetime = Field(..., description="Timestamp of this geometry observation (UTC).")
    type: Literal["Point", "Polygon"] = Field(..., description="GeoJSON geometry type.")
    coordinates: list[Any] = Field(
        ...,
        description="GeoJSON coordinates. Point: [lon, lat]. Polygon: list of linear rings.",
    )
    magnitude_value: float | None = Field(
        default=None,
        description="Magnitude scalar at this timestamp, if reported by the source.",
    )
    magnitude_unit: str | None = Field(
        default=None,
        description="Magnitude unit (e.g., 'kts', 'acres'), if reported.",
    )


class EONETEvent(BaseModel):
    """A single natural event record from EONET v3 with derived spatiotemporal helpers."""

    id: str = Field(..., description="EONET event ID (e.g., 'EONET_19986').")
    title: str = Field(..., description="Event title.")
    description: str | None = Field(default=None, description="Event description (often empty).")
    link: str = Field(..., description="EONET event landing-page URL.")
    closed: datetime | None = Field(
        default=None,
        description="Closure timestamp; None if the event is still open.",
    )
    categories: list[EONETCategoryRef] = Field(
        default_factory=list,
        description="Event categories.",
    )
    sources: list[EONETSource] = Field(
        default_factory=list,
        description="Upstream sources for provenance.",
    )
    geometry: list[EONETGeometry] = Field(
        default_factory=list,
        description="Time-stamped geometries for this event.",
    )

    bbox: list[float] | None = Field(
        default=None,
        min_length=4,
        max_length=4,
        description="Derived envelope across all geometries in standard (min_lon, min_lat, max_lon, max_lat) order.",
    )
    t_start: datetime | None = Field(
        default=None,
        description="Earliest geometry timestamp (UTC).",
    )
    t_end: datetime | None = Field(
        default=None,
        description="Latest geometry timestamp (UTC).",
    )


class EONETSearchInputSchema(InputSchema):
    """Filters for an EONET v3 event search."""

    category: EONETCategory | None = Field(
        default=None,
        description="Event category to filter on. Omit for all categories.",
    )
    status: EONETStatus = Field(
        default=EONETStatus.OPEN,
        description="Event lifecycle: 'open' (active), 'closed' (ended), or 'all'.",
    )
    days: int | None = Field(
        default=None,
        ge=1,
        le=365,
        description="Restrict to events updated in the last N days. Mutually exclusive with start/end.",
    )
    start: date | None = Field(
        default=None,
        description="Start date (YYYY-MM-DD). Use with 'end'. Mutually exclusive with 'days'.",
    )
    end: date | None = Field(
        default=None,
        description="End date (YYYY-MM-DD). Use with 'start'. Mutually exclusive with 'days'.",
    )
    bbox: list[float] | None = Field(
        default=None,
        min_length=4,
        max_length=4,
        description=(
            "Bounding box in standard (min_lon, min_lat, max_lon, max_lat) order. "
            "Translated to EONET's (minLon, maxLat, maxLon, minLat) request format internally."
        ),
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of events to return.",
    )
    magnitude_id: str | None = Field(
        default=None,
        description="Magnitude type ID (e.g., 'kts' wind speed, 'ac' acres). See EONET /magnitudes.",
    )
    magnitude_min: float | None = Field(
        default=None,
        description="Minimum magnitude value. Requires magnitude_id.",
    )
    magnitude_max: float | None = Field(
        default=None,
        description="Maximum magnitude value. Requires magnitude_id.",
    )

    @model_validator(mode="after")
    def _validate_combinations(self) -> "EONETSearchInputSchema":
        if self.days is not None and (self.start is not None or self.end is not None):
            raise ValueError("Use either 'days' or ('start' and 'end'), not both.")
        if (self.start is None) != (self.end is None):
            raise ValueError("'start' and 'end' must be provided together.")
        if self.start and self.end and self.start > self.end:
            raise ValueError("'start' must be on or before 'end'.")
        if self.bbox is not None:
            min_lon, min_lat, max_lon, max_lat = self.bbox
            if not (-180.0 <= min_lon <= 180.0 and -180.0 <= max_lon <= 180.0):
                raise ValueError("Longitudes must be in [-180, 180].")
            if not (-90.0 <= min_lat <= 90.0 and -90.0 <= max_lat <= 90.0):
                raise ValueError("Latitudes must be in [-90, 90].")
            if min_lon > max_lon or min_lat > max_lat:
                raise ValueError("bbox must be (min_lon, min_lat, max_lon, max_lat) with min <= max.")
        if (self.magnitude_min is not None or self.magnitude_max is not None) and self.magnitude_id is None:
            raise ValueError("magnitude_id is required when magnitude_min or magnitude_max is set.")
        return self


class EONETSearchOutputSchema(OutputSchema):
    """Output schema for EONET event search results."""

    results: list[EONETEvent] = Field(
        default_factory=list,
        description="Matching natural events.",
    )
    extra: dict[str, Any] | None = Field(
        default=None,
        description="Auxiliary metadata: total_count, request_url, params_echo.",
    )


def _flatten_positions(coords: Any) -> Iterable[tuple[float, float]]:
    """Yield (lon, lat) pairs from any GeoJSON coordinate structure (Point/Polygon/nested)."""
    if not coords:
        return
    if isinstance(coords[0], (int, float)):
        yield float(coords[0]), float(coords[1])
        return
    for sub in coords:
        yield from _flatten_positions(sub)


def _compute_bbox(geometries: list[EONETGeometry]) -> list[float] | None:
    """Compute [min_lon, min_lat, max_lon, max_lat] across all geometries; None if empty."""
    lons: list[float] = []
    lats: list[float] = []
    for g in geometries:
        for lon, lat in _flatten_positions(g.coordinates):
            lons.append(lon)
            lats.append(lat)
    if not lons:
        return None
    return [min(lons), min(lats), max(lons), max(lats)]


@mcp_tool
class EONETSearchTool(BaseTool[EONETSearchInputSchema, EONETSearchOutputSchema]):
    """
    Search NASA's EONET (Earth Observatory Natural Event Tracker) v3 for natural events.

    EONET tracks ongoing and past natural events worldwide — wildfires, severe storms,
    volcanoes, floods, earthquakes, sea/lake ice, landslides, drought, dust/haze,
    snow, temperature extremes, water color anomalies, and manmade events. Event
    metadata is sourced from authoritative providers (USGS, JTWC, InciWeb,
    SI Volcano, etc.). The API is public; no authentication required.

    This tool wraps the GET /events endpoint and returns parsed events with their
    full geometry timeline plus derived helpers — bbox (in standard GeoJSON order),
    t_start, and t_end — so downstream tools (CMR queries, Worldview deep links)
    can consume the spatiotemporal envelope without parsing GeoJSON.

    Input parameters (LLM-controllable per call):
    - category: EONETCategory enum (wildfires, severeStorms, volcanoes, etc.). Omit for all.
    - status: 'open' (default), 'closed', or 'all'.
    - days: Restrict to events updated in the last N days (1-365). Mutually exclusive with start/end.
    - start, end: Explicit date range (YYYY-MM-DD). Both required together.
    - bbox: (min_lon, min_lat, max_lon, max_lat) — standard GeoJSON order; tool converts internally.
    - limit: Max number of events (1-100, default 10).
    - magnitude_id, magnitude_min, magnitude_max: Magnitude filtering (see EONET /magnitudes).

    Configuration parameters (instance-level):
    - base_url: EONET API base. Defaults to env EONET_BASE_URL or production.
    - timeout: HTTP request timeout (default 30s).
    - sources: Optional allowlist of upstream source IDs (e.g., ['InciWeb', 'USGS_EHP']).

    Returns events with:
    - id, title, description, link, closed (timestamp or None)
    - categories (id+title), sources (id+url for provenance)
    - geometry: list of time-stamped Point/Polygon observations with optional magnitude
    - Derived: bbox in (min_lon, min_lat, max_lon, max_lat) order, t_start, t_end
    """

    input_schema = EONETSearchInputSchema
    output_schema = EONETSearchOutputSchema
    config_schema = EONETSearchToolConfig

    def _build_params(self, params: EONETSearchInputSchema) -> dict[str, str]:
        """Build EONET v3 query string parameters from validated input."""
        out: dict[str, str] = {"status": params.status.value, "limit": str(params.limit)}
        if params.category is not None:
            out["category"] = params.category.value
        if params.days is not None:
            out["days"] = str(params.days)
        if params.start is not None and params.end is not None:
            out["start"] = params.start.isoformat()
            out["end"] = params.end.isoformat()
        if params.bbox is not None:
            min_lon, min_lat, max_lon, max_lat = params.bbox
            # EONET expects (minLon, maxLat, maxLon, minLat) — top-left, bottom-right.
            out["bbox"] = f"{min_lon},{max_lat},{max_lon},{min_lat}"
        if params.magnitude_id is not None:
            out["magID"] = params.magnitude_id
        if params.magnitude_min is not None:
            out["magMin"] = str(params.magnitude_min)
        if params.magnitude_max is not None:
            out["magMax"] = str(params.magnitude_max)
        if self.config.sources:
            out["source"] = ",".join(self.config.sources)
        return out

    def _parse_geometry(self, raw: dict[str, Any]) -> EONETGeometry:
        return EONETGeometry(
            date=raw["date"],
            type=raw["type"],
            coordinates=raw.get("coordinates", []),
            magnitude_value=raw.get("magnitudeValue"),
            magnitude_unit=raw.get("magnitudeUnit"),
        )

    def _parse_event(self, raw: dict[str, Any]) -> EONETEvent:
        geometries = [self._parse_geometry(g) for g in raw.get("geometry", []) or []]
        timestamps = [g.date for g in geometries]
        return EONETEvent(
            id=raw["id"],
            title=raw.get("title", ""),
            description=raw.get("description"),
            link=raw.get("link", ""),
            closed=raw.get("closed"),
            categories=[EONETCategoryRef(**c) for c in raw.get("categories", []) or []],
            sources=[EONETSource(**s) for s in raw.get("sources", []) or []],
            geometry=geometries,
            bbox=_compute_bbox(geometries),
            t_start=min(timestamps) if timestamps else None,
            t_end=max(timestamps) if timestamps else None,
        )

    async def _arun(self, params: EONETSearchInputSchema) -> EONETSearchOutputSchema:
        """Execute an EONET v3 /events query and return parsed results."""
        query_params = self._build_params(params)
        url = f"{self.config.base_url.rstrip('/')}/events"
        logger.debug(f"EONET request: {url} params={query_params}")

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.get(url, params=query_params)
                response.raise_for_status()
                data = response.json()
            except httpx.TimeoutException as e:
                msg = f"EONET API request timed out after {self.config.timeout}s"
                raise TimeoutError(msg) from e
            except httpx.HTTPStatusError as e:
                msg = f"EONET API returned status {e.response.status_code}: {e.response.text}"
                raise RuntimeError(msg) from e
            except Exception as e:
                msg = f"Failed to query EONET API: {e}"
                raise RuntimeError(msg) from e

        raw_events = data.get("events", []) or []
        events = [self._parse_event(ev) for ev in raw_events]

        return EONETSearchOutputSchema(
            results=events,
            extra={
                "total_count": len(events),
                "request_url": str(response.request.url),
                "params_echo": query_params,
            },
        )
