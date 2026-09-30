"""Geocode tool — convert a place name to a bounding box.

Uses the free Nominatim (OpenStreetMap) API, rate-limited via the shared
throttle in ``_nominatim`` (1 req/sec across geocode + reverse_geocode).
"""

from __future__ import annotations

import asyncio

import requests
from pydantic import ConfigDict, Field

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from akd_ext.mcp import mcp_tool
from akd_ext.tools._nominatim import nominatim_get

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


class GeoCodeInput(InputSchema):
    """Place name or description to geocode."""

    query: str = Field(
        ...,
        description=(
            "Place name, event/location description, or address to geocode. "
            "Examples: 'Sioux Falls, SD', 'Houston Texas', 'Iowa'."
        ),
    )


class GeoCodeOutput(OutputSchema):
    """Bounding box result or candidate list from geocoding."""

    model_config = ConfigDict(extra="ignore")

    bbox: list[float] | None = Field(
        default=None,
        description="Bounding box [west, south, east, north] in EPSG:4326.",
    )
    display_name: str | None = Field(
        default=None, description="Full display name of the matched location."
    )
    candidates: list[dict] | None = Field(
        default=None,
        description="Multiple candidate matches when the query is ambiguous.",
    )
    message: str = Field(default="")


class GeoCodeConfig(BaseToolConfig):
    """Configuration for the geocode tool."""

    name: str = Field(default="geocode", description="Tool name")
    description: str = Field(
        default=(
            "Convert a place name or description to a bounding box "
            "[west, south, east, north]. Returns a single bbox when "
            "unambiguous, or a candidates list when multiple matches "
            "are found."
        ),
    )


def _geocode_location(query: str) -> dict:
    """Call Nominatim search API (rate-limited via the shared throttle)."""
    params = {"q": query, "format": "json", "limit": 5}
    try:
        resp = nominatim_get(NOMINATIM_URL, params)
        resp.raise_for_status()
        results = resp.json()
    except requests.RequestException as e:
        return {"message": f"Geocoding service unavailable: {e}"}

    if not results:
        return {
            "message": f"No results for '{query}'. Try rephrasing or provide coordinates."
        }

    def _parse_bbox(r: dict) -> list:
        bb = r["boundingbox"]  # [south, north, west, east]
        return [float(bb[2]), float(bb[0]), float(bb[3]), float(bb[1])]

    if len(results) == 1:
        return {
            "bbox": _parse_bbox(results[0]),
            "display_name": results[0]["display_name"],
            "message": "ok",
        }

    candidates = [
        {"display_name": r["display_name"], "bbox": _parse_bbox(r)}
        for r in results[:3]
    ]
    return {
        "candidates": candidates,
        "message": "Multiple matches found. Please choose one.",
    }


@mcp_tool
class GeoCodeTool(BaseTool[GeoCodeInput, GeoCodeOutput]):
    """Convert a place name or description to a bounding box.

    Returns a single bbox [west, south, east, north] when unambiguous,
    or a candidates list when multiple matches are found.
    Nominatim rate limit: 1 req/sec enforced by sleep.
    """

    config_schema = GeoCodeConfig
    input_schema = GeoCodeInput
    output_schema = GeoCodeOutput

    async def _arun(self, params: GeoCodeInput, **kwargs) -> GeoCodeOutput:
        result = await asyncio.to_thread(_geocode_location, params.query)
        return GeoCodeOutput.model_validate(result)
