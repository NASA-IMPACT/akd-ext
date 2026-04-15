"""Viz tool: build raster tile URLs for COG items and CMR collections."""
from __future__ import annotations

import os

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp import mcp_tool
from akd_ext.tools.utils import build_cmr_tile_urls, build_tile_urls_batch, fetch_collection_metadata


class VizToolConfig(BaseToolConfig):
    """Configuration for the Viz Tool."""

    veda_api_root: str = Field(
        default=os.getenv("VEDA_API_ROOT", "https://dev.openveda.cloud/api"),
        description="VEDA API root (base URL for STAC and raster APIs)",
    )
    titiler_cmr_url: str = Field(
        default=os.getenv("TITILER_CMR_URL", "https://staging.openveda.cloud/api/titiler-cmr"),
        description="Base URL for the titiler-cmr service",
    )

    @property
    def raster_api_url(self) -> str:
        """Raster API URL derived from veda_api_root."""
        return f"{self.veda_api_root.rstrip('/')}/raster"

    @property
    def stac_url(self) -> str:
        """STAC API URL derived from veda_api_root."""
        return f"{self.veda_api_root.rstrip('/')}/stac"


class VizItem(OutputSchema):
    """A COG item for tile URL generation."""

    url: str = Field(..., description="URL to the COG file (S3 or HTTP)")
    id: str | None = Field(None, description="STAC item ID")
    datetime: str | None = Field(None, description="Item datetime")


class TileResultItem(OutputSchema):
    """A tile URL result for a single item."""

    id: str | None = Field(None, description="STAC item ID")
    datetime: str | None = Field(None, description="Item datetime")
    tile_url: str = Field(..., description="PNG tile URL template with {z}/{x}/{y}")


class VizToolInputSchema(InputSchema):
    """Input schema for the viz tool.

    Provide either 'items' (for VEDA COG tiles) or 'collection_metadata' +
    'datetime_range' (for CMR tiles). The tool picks the right path automatically.
    """

    # --- VEDA COG path ---
    items: list[VizItem] | None = Field(
        None, description="List of COG items with 'url' and optionally 'id', 'datetime' (VEDA path)"
    )
    collection_id: str | None = Field(
        None, description="Collection ID to fetch render params from (VEDA path)"
    )
    collection_metadata: dict | None = Field(
        None,
        description=(
            "Pre-fetched STAC collection JSON. For VEDA path, avoids a second STAC call. "
            "For CMR path, must include collection_concept_id and renders."
        ),
    )

    # --- CMR path ---
    datetime_range: str | None = Field(
        None, description="ISO-8601 range 'start/end' for CMR timeseries (required for CMR path)"
    )
    selected_variable: str | None = Field(
        None, description="Variable name from the collection renders (CMR path, optional)"
    )


class VizToolOutputSchema(OutputSchema):
    """Output schema for the viz tool."""

    items: list[TileResultItem] = Field(default_factory=list, description="Tile URL results")
    collection_id: str | None = Field(None, description="Collection ID")
    title: str | None = Field(None, description="Collection title")
    description: str | None = Field(None, description="Collection description")
    colormap_name: str | None = Field(None, description="Colormap used for rendering")
    rescale: list[float] | None = Field(None, description="Rescale range [min, max]")
    units: str | None = Field(None, description="Data units")
    time_density: str | None = Field(None, description="Temporal density")
    error: str | None = Field(None, description="Error message if the request failed")


@mcp_tool
class VizTool(BaseTool[VizToolInputSchema, VizToolOutputSchema]):
    """
    Build raster tile URLs for visualization of COG items or CMR collections.

    Supports two modes determined by the inputs provided:

    1. VEDA COG mode — provide 'items' (list of COG URLs) + optional 'collection_id'.
       Builds PNG tile URL templates with colormap params from the collection's
       renders.dashboard configuration.

    2. CMR mode — provide 'collection_metadata' + 'datetime_range'.
       Calls the titiler-cmr timeseries tilejson endpoint to get tile URLs
       for each timestep.

    Input parameters (query-time, LLM-controllable):
    - items: List of COG items (VEDA path)
    - collection_id: Collection ID for render params (VEDA path, optional)
    - collection_metadata: Full STAC collection JSON (CMR path, or VEDA pre-fetch)
    - datetime_range: ISO-8601 range 'start/end' (CMR path)
    - selected_variable: Variable name from renders (CMR path, optional)

    Configuration parameters (instance-time, user-controlled):
    - veda_api_root: VEDA API root (raster & stac URLs derived from it)
    - titiler_cmr_url: Base URL for the titiler-cmr service
    """

    input_schema = VizToolInputSchema
    output_schema = VizToolOutputSchema
    config_schema = VizToolConfig

    async def _arun(self, params: VizToolInputSchema) -> VizToolOutputSchema:
        """Execute tile URL generation — picks VEDA or CMR path based on inputs."""

        # Auto-fetch collection metadata from collection_id if not provided
        collection_metadata = params.collection_metadata
        if collection_metadata is None and params.collection_id:
            collection_metadata = fetch_collection_metadata(params.collection_id, self.config.stac_url)

        # CMR path: collection_metadata with concept_id + datetime_range
        if (
            collection_metadata is not None
            and collection_metadata.get("collection_concept_id")
            and params.datetime_range
        ):
            result = build_cmr_tile_urls(
                collection_metadata=collection_metadata,
                datetime_range=params.datetime_range,
                titiler_cmr_url=self.config.titiler_cmr_url,
                selected_variable=params.selected_variable,
            )

            tile_items = [TileResultItem(**item) for item in result.get("items", [])]
            rescale = result.get("rescale")

            return VizToolOutputSchema(
                items=tile_items,
                collection_id=result.get("collection_id"),
                title=result.get("title"),
                description=result.get("description"),
                colormap_name=result.get("colormap_name"),
                rescale=rescale if isinstance(rescale, list) else None,
                units=result.get("units"),
                time_density=result.get("time_density"),
                error=result.get("error"),
            )

        # VEDA COG path: items provided
        if params.items:
            raw_items = [
                {"url": item.url, "id": item.id, "datetime": item.datetime}
                for item in params.items
            ]

            result = build_tile_urls_batch(
                items=raw_items,
                collection_id=params.collection_id,
                raster_api_url=self.config.raster_api_url,
                stac_url=self.config.stac_url,
                collection_metadata=collection_metadata,
            )

            tile_items = [TileResultItem(**item) for item in result.get("items", [])]
            rescale = result.get("rescale")

            return VizToolOutputSchema(
                items=tile_items,
                collection_id=result.get("collection_id"),
                title=result.get("title"),
                description=result.get("description"),
                colormap_name=result.get("colormap_name"),
                rescale=rescale if isinstance(rescale, list) else None,
                units=result.get("units"),
                time_density=result.get("time_density"),
            )

        return VizToolOutputSchema(
            error="Provide either 'items' (VEDA COG path) or 'collection_metadata' + 'datetime_range' (CMR path)"
        )
