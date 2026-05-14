"""
Viz tool: build raster tile URLs for COG items using VEDA Raster API.

This tool converts COG (Cloud Optimized GeoTIFF) items into tile URLs
suitable for visualization in web mapping applications.
"""

from __future__ import annotations

import os
from urllib.parse import quote

import httpx
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field
from loguru import logger

from akd_ext.mcp import mcp_tool


class VizToolConfig(BaseToolConfig):
    """Configuration for the Viz Tool."""

    veda_stac_url: str = Field(
        default=os.getenv("VEDA_STAC_URL", ""),
        description="Base URL for the VEDA STAC API",
    )
    veda_raster_url: str = Field(
        default=os.getenv("VEDA_RASTER_URL", ""),
        description="Base URL for the VEDA Raster API",
    )
    timeout: float = Field(
        default=15.0,
        description="HTTP request timeout in seconds",
    )


class VizItem(InputSchema):
    """Schema for a single COG item to visualize."""

    url: str = Field(
        ...,
        description="URL to the COG (Cloud Optimized GeoTIFF) file",
    )
    id: str | None = Field(
        None,
        description="Optional identifier for the item",
    )
    datetime: str | None = Field(
        None,
        description="Optional datetime string for the item",
    )


class VizInputSchema(InputSchema):
    """Input schema for the Viz tool."""

    items: list[VizItem] = Field(
        ...,
        description="List of COG items to generate tile URLs for",
    )
    collection_id: str | None = Field(
        None,
        description="Optional collection ID to fetch render params from STAC API",
    )


class VizTileResult(OutputSchema):
    """Schema for a single tile URL result."""

    id: str | None = Field(
        None,
        description="Item identifier",
    )
    datetime: str | None = Field(
        None,
        description="Item datetime",
    )
    tile_url: str = Field(
        ...,
        description="Tile URL template with {z}/{x}/{y} placeholders",
    )


class VizOutputSchema(OutputSchema):
    """Output schema for the Viz tool."""

    items: list[dict] = Field(
        default_factory=list,
        description="List of tile URL results with id, datetime, and tile_url",
    )
    collection_id: str | None = Field(
        None,
        description="Collection ID used for render params",
    )
    title: str | None = Field(
        None,
        description="Collection title from STAC metadata",
    )
    description: str | None = Field(
        None,
        description="Collection description from STAC metadata",
    )
    colormap_name: str | None = Field(
        None,
        description="Colormap name used for rendering",
    )
    rescale: list[float] | None = Field(
        None,
        description="Rescale range as [min, max]",
    )
    units: str | None = Field(
        None,
        description="Data units from collection metadata",
    )
    time_density: str | None = Field(
        None,
        description="Time density from collection metadata",
    )
    error: str | None = Field(
        None,
        description="Error message if visualization failed",
    )


def _fetch_collection_metadata(stac_url: str, collection_id: str, timeout: float) -> dict | None:
    """Fetch collection metadata from STAC API.
    
    Returns the full collection metadata including renders.dashboard params.
    """
    url = f"{stac_url.rstrip('/')}/collections/{collection_id}"
    
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url, headers={"Accept": "application/json"})
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def _get_render_params(collection_metadata: dict | None) -> dict:
    """Extract render params from collection metadata.
    
    Looks for renders.dashboard to get colormap_name, bidx, rescale.
    Returns dict with keys: colormap_name, bidx, rescale (all optional).
    """
    if not collection_metadata:
        return {}
    
    renders = collection_metadata.get("renders", {})
    dashboard = renders.get("dashboard", {})
    
    params = {}
    
    if "colormap_name" in dashboard:
        params["colormap_name"] = dashboard["colormap_name"]
    
    if "bidx" in dashboard:
        # bidx is a list like [1]
        bidx = dashboard["bidx"]
        if isinstance(bidx, list) and bidx:
            params["bidx"] = bidx[0]
    
    if "rescale" in dashboard:
        # rescale is a list of [min, max] pairs like [[0, 1.5e16]]
        rescale = dashboard["rescale"]
        if isinstance(rescale, list) and rescale:
            if isinstance(rescale[0], list) and len(rescale[0]) == 2:
                params["rescale"] = f"{rescale[0][0]},{rescale[0][1]}"
            elif len(rescale) == 2:
                params["rescale"] = f"{rescale[0]},{rescale[1]}"
    
    return params


@mcp_tool
class VizTool(BaseTool[VizInputSchema, VizOutputSchema]):
    """
    Build raster tile URLs for COG items using VEDA Raster API.

    This tool converts Cloud Optimized GeoTIFF (COG) items into tile URL
    templates that can be used for visualization in web mapping applications.
    It fetches render parameters (colormap, rescale, etc.) from the STAC
    collection metadata when a collection_id is provided.

    Input parameters:
    - items: List of COG items with 'url' (required), 'id', and 'datetime' (optional)
    - collection_id: Optional collection ID to fetch render params from STAC API

    Configuration parameters:
    - veda_stac_url: Base URL for the VEDA STAC API (required for collection metadata)
    - veda_raster_url: Base URL for the VEDA Raster API (required)
    - timeout: HTTP request timeout in seconds (default: 15.0)

    Returns:
    - items: List of tile URL results with id, datetime, and tile_url
    - collection_id: Collection ID used
    - title, description: Collection metadata
    - colormap_name, rescale, units, time_density: Render parameters
    - error: Error message if visualization failed
    """

    input_schema = VizInputSchema
    output_schema = VizOutputSchema
    config_schema = VizToolConfig

    async def _arun(self, params: VizInputSchema) -> VizOutputSchema:
        """Build tile URLs for the provided COG items."""
        # Validate configuration
        if not self.config.veda_raster_url:
            return VizOutputSchema(
                items=[],
                collection_id=None,
                error="veda_raster_url not configured",
            )

        if not params.items:
            return VizOutputSchema(
                items=[],
                collection_id=params.collection_id,
            )

        # Fetch collection metadata for render params
        collection_metadata = None
        render_params = {}
        if params.collection_id and self.config.veda_stac_url:
            collection_metadata = _fetch_collection_metadata(
                self.config.veda_stac_url,
                params.collection_id,
                self.config.timeout,
            )
            render_params = _get_render_params(collection_metadata)

        try:
            results = []
            for item in params.items:
                url = item.url
                if not url:
                    continue

                # Build PNG tile URL with colormap params
                encoded_url = quote(url, safe="")

                # Start with base URL - note .png extension for PNG output
                raster_base = self.config.veda_raster_url.rstrip("/")
                tile_url = f"{raster_base}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png?url={encoded_url}"

                # Add render params if available
                if render_params.get("bidx"):
                    tile_url += f"&bidx={render_params['bidx']}"
                if render_params.get("colormap_name"):
                    tile_url += f"&colormap_name={render_params['colormap_name']}"
                if render_params.get("rescale"):
                    tile_url += f"&rescale={render_params['rescale']}"

                results.append({
                    "id": item.id,
                    "datetime": item.datetime,
                    "tile_url": tile_url,
                })

            # Extract collection-level fields for frontend
            output = VizOutputSchema(
                items=results,
                collection_id=params.collection_id,
                title=None,
                description=None,
                colormap_name=render_params.get("colormap_name"),
                rescale=None,
                units=None,
                time_density=None,
                error=None,
            )

            if collection_metadata:
                output.title = collection_metadata.get("title")
                output.description = collection_metadata.get("description")
                output.time_density = collection_metadata.get("dashboard:time_density")

                # Extract rescale as [min, max] list
                rescale = render_params.get("rescale")
                if rescale and "," in rescale:
                    parts = rescale.split(",")
                    try:
                        output.rescale = [float(parts[0]), float(parts[1])]
                    except (ValueError, IndexError):
                        pass

                # Try to find units in item_assets or summaries
                item_assets = collection_metadata.get("item_assets", {})
                for asset_info in item_assets.values():
                    if "unit" in asset_info:
                        output.units = asset_info["unit"]
                        break

            return output

        except Exception as e:
            msg = f"Viz tool failed: {e}"
            logger.error(msg)
            return VizOutputSchema(
                items=[],
                collection_id=params.collection_id,
                error=msg,
            )
