"""Reverse geocode tool — convert a bbox to a US state / location name.

Uses the free Nominatim (OpenStreetMap) reverse API on the bbox centroid,
rate-limited via the shared throttle in ``_nominatim`` (1 req/sec across
geocode + reverse_geocode).
"""

from __future__ import annotations

import asyncio

import requests
from pydantic import ConfigDict, Field

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from akd_ext.mcp import mcp_tool
from akd_ext.tools._nominatim import nominatim_get

NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"

# US state name → code
_NAME_TO_CODE: dict[str, str] = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE",
    "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
    "pennsylvania": "PA", "puerto rico": "PR", "rhode island": "RI",
    "south carolina": "SC", "south dakota": "SD", "tennessee": "TN",
    "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA",
    "washington": "WA", "west virginia": "WV", "wisconsin": "WI",
    "wyoming": "WY",
}


class ReverseGeoCodeInput(InputSchema):
    """Bounding box to reverse geocode."""

    bbox: list[float] = Field(
        ...,
        description=(
            "Bounding box [west, south, east, north] in EPSG:4326. "
            "The centroid is used for the reverse lookup."
        ),
    )


class ReverseGeoCodeOutput(OutputSchema):
    """Location info from reverse geocoding a bbox centroid."""

    model_config = ConfigDict(extra="ignore")

    state: str | None = Field(
        default=None, description="US state 2-letter code (e.g., TX, SD)."
    )
    state_name: str | None = Field(
        default=None, description="Full state name."
    )
    county: str | None = Field(
        default=None, description="County name if available."
    )
    country: str | None = Field(
        default=None, description="Country name."
    )
    display_name: str | None = Field(
        default=None, description="Full display name of the centroid location."
    )
    centroid_lat: float | None = Field(
        default=None, description="Latitude of the bbox centroid."
    )
    centroid_lon: float | None = Field(
        default=None, description="Longitude of the bbox centroid."
    )
    message: str = Field(default="")


class ReverseGeoCodeConfig(BaseToolConfig):
    """Configuration for the reverse geocode tool."""

    name: str = Field(default="reverse_geocode", description="Tool name")
    description: str = Field(
        default=(
            "Convert a bounding box [west, south, east, north] to a "
            "location: US state code, state name, county, and display name. "
            "Uses the bbox centroid for the lookup."
        ),
    )


def _reverse_geocode(bbox: list[float]) -> dict:
    """Call Nominatim reverse API on the bbox centroid."""
    if len(bbox) != 4:
        return {
            "message": (
                f"Expected a bbox of 4 numbers [west, south, east, north], "
                f"got {len(bbox)}: {bbox}."
            )
        }
    west, south, east, north = bbox
    lat = (south + north) / 2
    lon = (west + east) / 2

    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 5,  # state-level detail
        "addressdetails": 1,
    }
    try:
        resp = nominatim_get(NOMINATIM_REVERSE_URL, params)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return {"message": f"Reverse geocoding service unavailable: {e}"}

    if "error" in data:
        return {"message": f"No results for centroid ({lat}, {lon}): {data['error']}"}

    address = data.get("address", {})
    state_name = address.get("state", "")
    state_code = _NAME_TO_CODE.get(state_name.lower())
    county = address.get("county", "")
    country = address.get("country", "")

    return {
        "state": state_code,
        "state_name": state_name or None,
        "county": county or None,
        "country": country or None,
        "display_name": data.get("display_name"),
        "centroid_lat": round(lat, 4),
        "centroid_lon": round(lon, 4),
        "message": "ok",
    }


@mcp_tool
class ReverseGeoCodeTool(BaseTool[ReverseGeoCodeInput, ReverseGeoCodeOutput]):
    """Convert a bounding box to a US state, county, and location name.

    Uses the bbox centroid with the Nominatim reverse API.
    Nominatim rate limit: 1 req/sec enforced by sleep.
    """

    config_schema = ReverseGeoCodeConfig
    input_schema = ReverseGeoCodeInput
    output_schema = ReverseGeoCodeOutput

    async def _arun(self, params: ReverseGeoCodeInput, **kwargs) -> ReverseGeoCodeOutput:
        result = await asyncio.to_thread(_reverse_geocode, params.bbox)
        return ReverseGeoCodeOutput.model_validate(result)
