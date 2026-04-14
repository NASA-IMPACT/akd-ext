"""GetPlace tool: resolve place names to bounding boxes via Geodini."""
from __future__ import annotations

import os

import httpx
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from loguru import logger
from pydantic import Field
from shapely.geometry import shape

from akd_ext.mcp import mcp_tool


def _resolve_place(
    query: str,
    geodini_host: str,
    timeout: float = 30.0,
    verify_ssl: bool = True,
) -> dict:
    """Resolve a place query to bbox, place_name, and geometry via Geodini."""
    if not geodini_host:
        return {"bbox": None, "place": None, "geometry": None, "error": "geodini_host not configured"}

    try:
        with httpx.Client(timeout=timeout, verify=verify_ssl) as client:
            r = client.get(f"{geodini_host.rstrip('/')}/search", params={"query": query})
            r.raise_for_status()
            data = r.json()

        if not data.get("results"):
            return {"bbox": None, "place": None, "geometry": None, "error": f"Could not resolve place for '{query}'"}

        top = data["results"][0]
        name = top.get("name") or top.get("display_name")
        geometry = top.get("geometry")
        bbox = list(shape(geometry).bounds) if geometry else None

        return {"bbox": bbox, "place": name, "geometry": geometry, "error": None}

    except httpx.TimeoutException:
        return {"bbox": None, "place": None, "geometry": None, "error": f"Geodini request timed out after {timeout}s"}
    except httpx.HTTPStatusError as e:
        return {"bbox": None, "place": None, "geometry": None, "error": f"Geodini returned error status {e.response.status_code}"}
    except Exception as e:
        logger.exception("Geocoding error")
        return {"bbox": None, "place": None, "geometry": None, "error": f"Geocoding failed: {e}"}


class GetPlaceToolConfig(BaseToolConfig):
    """Configuration for the GetPlace Tool."""

    geodini_host: str = Field(
        default=os.getenv("GEODINI_HOST", ""),
        description="Base URL for the Geodini geocoding service",
    )
    timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates (set False for self-signed certs)",
    )


class GetPlaceToolInputSchema(InputSchema):
    """Input schema for the GetPlace tool."""

    query: str = Field(
        ...,
        description="A place name or location to geocode (e.g., 'Los Angeles', 'California', 'Amazon rainforest')",
    )


class GetPlaceToolOutputSchema(OutputSchema):
    """Output schema for the GetPlace tool."""

    place: str | None = Field(
        None,
        description="The resolved place name as returned by the geocoding service",
    )
    bbox: list[float] | None = Field(
        None,
        description="Bounding box as [west, south, east, north] (i.e., [min_lon, min_lat, max_lon, max_lat])",
    )
    geometry: dict | None = Field(
        None,
        description="GeoJSON geometry for the place",
    )
    error: str | None = Field(
        None,
        description="Error message if geocoding failed",
    )


@mcp_tool
class GetPlaceTool(BaseTool[GetPlaceToolInputSchema, GetPlaceToolOutputSchema]):
    """
    Resolve a place name to a geographic bounding box via geocoding.

    This tool uses the Geodini geocoding service to convert natural language
    place names into bounding boxes suitable for spatial queries against
    geospatial data catalogs (e.g., STAC).

    Input parameters (query-time, LLM-controllable):
    - query: Natural language place name (e.g., "California", "Amazon basin")

    Configuration parameters (instance-time, user-controlled):
    - geodini_host: Base URL for the Geodini service (required)
    - timeout: HTTP request timeout in seconds (default: 30.0)
    - verify_ssl: Verify SSL certificates (default: True)

    Returns:
    - place: Resolved place name
    - bbox: Bounding box as [west, south, east, north]
    - geometry: GeoJSON geometry for the place
    - error: Error message if resolution failed
    """

    input_schema = GetPlaceToolInputSchema
    output_schema = GetPlaceToolOutputSchema
    config_schema = GetPlaceToolConfig

    async def _arun(self, params: GetPlaceToolInputSchema) -> GetPlaceToolOutputSchema:
        """Execute geocoding query and return bounding box."""
        result = _resolve_place(
            query=params.query,
            geodini_host=self.config.geodini_host,
            timeout=self.config.timeout,
            verify_ssl=self.config.verify_ssl,
        )

        return GetPlaceToolOutputSchema(
            place=result.get("place"),
            bbox=result.get("bbox"),
            geometry=result.get("geometry"),
            error=result.get("error"),
        )
