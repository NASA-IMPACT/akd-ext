"""
Geocoding tool for resolving place names to bounding boxes.

This tool uses the Geodini geocoding service to convert natural language
place names (e.g., "California", "Los Angeles") into geographic bounding boxes
that can be used for spatial queries.
"""

import os
import httpx
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field
from loguru import logger

from akd_ext.mcp import mcp_tool


class GetPlaceToolConfig(BaseToolConfig):
    """Configuration for the GetPlace Tool."""

    geodini_host: str = Field(
        default=os.getenv("GEODINI_HOST", ""),
        description="Base URL for the Geodini geocoding service",
    )
    timeout: float = Field(
        default=15.0,
        description="HTTP request timeout in seconds",
    )


class GetPlaceInputSchema(InputSchema):
    """Input schema for the GetPlace tool."""

    query: str = Field(
        ...,
        description="A place name or location to geocode (e.g., 'Los Angeles', 'California', 'Amazon rainforest')",
    )


class GetPlaceOutputSchema(OutputSchema):
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
class GetPlaceTool(BaseTool[GetPlaceInputSchema, GetPlaceOutputSchema]):
    """
    Resolve a place name to a geographic bounding box via geocoding.

    This tool uses the Geodini geocoding service to convert natural language
    place names into bounding boxes suitable for spatial queries against
    geospatial data catalogs (e.g., STAC).

    Input parameters:
    - query: Natural language place name (e.g., "I am interested in LA", "California", "Amazon basin")

    Configuration parameters:
    - geodini_host: Base URL for the Geodini service (required)
    - timeout: HTTP request timeout in seconds (default: 15.0)

    Returns:
    - place: Resolved place name
    - bbox: Bounding box as [west, south, east, north]
    - error: Error message if resolution failed
    """

    input_schema = GetPlaceInputSchema
    output_schema = GetPlaceOutputSchema
    config_schema = GetPlaceToolConfig

    async def _arun(self, params: GetPlaceInputSchema) -> GetPlaceOutputSchema:
        """Execute geocoding query and return bounding box."""
        # Validate configuration
        if not self.config.geodini_host:
            return GetPlaceOutputSchema(
                place=None,
                bbox=None,
                error="geodini_host not configured",
            )

        try:
            # Query the Geodini geocoding service
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    f"{self.config.geodini_host.rstrip('/')}/search",
                    params={"query": params.query},
                )
                response.raise_for_status()
                data = response.json()

            # Check if we got any results
            if not data.get("results"):
                return GetPlaceOutputSchema(
                    place=None,
                    bbox=None,
                    error=f"Could not resolve bbox for '{params.query}'",
                )

            # Extract the top result
            top = data["results"][0]
            name = top.get("name") or top.get("display_name")

            # Extract bounding box from geometry
            # Geodini returns GeoJSON geometry, we need to compute bounds
            geometry = top.get("geometry")
            if geometry:
                from shapely.geometry import shape
                bbox = list(shape(geometry).bounds)  # Returns (minx, miny, maxx, maxy)
            else:
                bbox = None

            if bbox:
                return GetPlaceOutputSchema(
                    place=name,
                    bbox=bbox,
                    geometry=geometry,
                    error=None,
                )
            else:
                return GetPlaceOutputSchema(
                    place=name,
                    bbox=None,
                    geometry=None,
                    error=f"No geometry found for '{params.query}'",
                )

        except httpx.TimeoutException as e:
            msg = f"Geodini request timed out after {self.config.timeout}s"
            logger.error(msg)
            return GetPlaceOutputSchema(place=None, bbox=None, geometry=None, error=msg)

        except httpx.HTTPStatusError as e:
            msg = f"Geodini returned error status {e.response.status_code}"
            logger.error(msg)
            return GetPlaceOutputSchema(place=None, bbox=None, geometry=None, error=msg)

        except Exception as e:
            msg = f"Geocoding failed: {e}"
            logger.error(msg)
            return GetPlaceOutputSchema(place=None, bbox=None, geometry=None, error=msg)
