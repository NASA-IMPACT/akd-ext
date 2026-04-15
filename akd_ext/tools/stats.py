"""Stats tool: fetch raster statistics from VEDA raster API and titiler-cmr."""
from __future__ import annotations

import os

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from loguru import logger
from pydantic import Field

from akd_ext.mcp import mcp_tool
from akd_ext.tools.utils import fetch_cmr_statistics, fetch_collection_metadata, fetch_statistics_batch


class StatsToolConfig(BaseToolConfig):
    """Configuration for the Statistics Tool."""

    veda_api_root: str = Field(
        default=os.getenv("VEDA_API_ROOT", "https://dev.openveda.cloud/api"),
        description="VEDA API root (base URL for STAC and raster APIs)",
    )
    titiler_cmr_url: str = Field(
        default=os.getenv("TITILER_CMR_URL", "https://staging.openveda.cloud/api/titiler-cmr"),
        description="Base URL for the titiler-cmr service",
    )
    dst_crs: str = Field(
        default="+proj=cea",
        description="Destination CRS for area-weighted statistics",
    )

    @property
    def raster_api_url(self) -> str:
        """Raster API URL derived from veda_api_root."""
        return f"{self.veda_api_root.rstrip('/')}/raster"

    @property
    def stac_url(self) -> str:
        """STAC API URL derived from veda_api_root."""
        return f"{self.veda_api_root.rstrip('/')}/stac"


class StatsItem(OutputSchema):
    """A COG item with URL and optional metadata."""

    url: str = Field(..., description="URL to the COG file (S3 or HTTP)")
    id: str | None = Field(None, description="STAC item ID")
    datetime: str | None = Field(None, description="Item datetime")


class StatsResultItem(OutputSchema):
    """Statistics result for a single item."""

    url: str | None = Field(None, description="COG URL")
    id: str | None = Field(None, description="STAC item ID")
    datetime: str | None = Field(None, description="Item datetime")
    statistics: dict = Field(default_factory=dict, description="Per-band statistics")
    error: str | None = Field(None, description="Error message if the fetch failed")


class StatsToolInputSchema(InputSchema):
    """Input schema for the statistics tool.

    Provide either 'items' (for VEDA COG stats) or 'collection_metadata' +
    'datetime_range' (for CMR timeseries stats). The tool picks the right
    path automatically.
    """

    geometry: dict = Field(
        ..., description="GeoJSON geometry (Polygon or MultiPolygon) defining the area of interest"
    )

    # --- VEDA COG path ---
    items: list[StatsItem] | None = Field(
        None, description="List of COG items with 'url' and optionally 'id', 'datetime' (VEDA path)"
    )

    # --- CMR path ---
    collection_id: str | None = Field(
        None, description="Collection ID — full metadata is fetched automatically (CMR path)"
    )
    collection_metadata: dict | None = Field(
        None, description="Pre-fetched STAC collection JSON; if omitted, fetched from collection_id (CMR path)"
    )
    datetime_range: str | None = Field(
        None, description="ISO-8601 range 'start/end' for CMR timeseries (required with collection_metadata)"
    )
    selected_variable: str | None = Field(
        None, description="Variable name from the collection renders (CMR path, optional)"
    )


class StatsToolOutputSchema(OutputSchema):
    """Output schema for the statistics tool."""

    results: list[StatsResultItem] = Field(
        default_factory=list, description="Per-item statistics (VEDA COG path)"
    )
    statistics: dict = Field(
        default_factory=dict, description="Aggregated statistics (CMR path)"
    )
    error: str | None = Field(None, description="Error message if the request failed")


@mcp_tool
class StatsTool(BaseTool[StatsToolInputSchema, StatsToolOutputSchema]):
    """
    Fetch raster zonal statistics from the VEDA raster API or titiler-cmr.

    Supports two modes determined by the inputs provided:

    1. VEDA COG mode — provide 'items' (list of COG URLs) + 'geometry'.
       Fetches per-band statistics for each COG in parallel via the VEDA
       raster API /cog/statistics endpoint.

    2. CMR mode — provide 'collection_metadata' + 'datetime_range' + 'geometry'.
       Fetches timeseries zonal statistics for CMR-backed collections via
       the titiler-cmr /xarray/timeseries/statistics endpoint.

    Input parameters (query-time, LLM-controllable):
    - geometry: GeoJSON geometry (Polygon or MultiPolygon) for the AOI (required)
    - items: List of COG items (VEDA path)
    - collection_metadata: Full STAC collection JSON (CMR path)
    - datetime_range: ISO-8601 range 'start/end' (CMR path)
    - selected_variable: Variable name from renders (CMR path, optional)

    Configuration parameters (instance-time, user-controlled):
    - veda_api_root: VEDA API root (raster URL derived from it)
    - titiler_cmr_url: Base URL for the titiler-cmr service
    - dst_crs: Destination CRS for area-weighted stats (default: Equal Area)
    """

    input_schema = StatsToolInputSchema
    output_schema = StatsToolOutputSchema
    config_schema = StatsToolConfig

    async def _arun(self, params: StatsToolInputSchema) -> StatsToolOutputSchema:
        """Execute statistics fetch — picks VEDA or CMR path based on inputs."""

        # Auto-fetch collection metadata from collection_id if not provided
        collection_metadata = params.collection_metadata
        if collection_metadata is None and params.collection_id:
            collection_metadata = fetch_collection_metadata(params.collection_id, self.config.stac_url)
            if collection_metadata is None:
                return StatsToolOutputSchema(
                    error=f"Could not fetch metadata for collection '{params.collection_id}'"
                )

        # CMR path: collection_metadata provided (or auto-fetched)
        if collection_metadata is not None:
            if not params.datetime_range:
                return StatsToolOutputSchema(
                    error="datetime_range is required when using collection_metadata (CMR path)"
                )

            result = fetch_cmr_statistics(
                collection_metadata=collection_metadata,
                datetime_range=params.datetime_range,
                geometry=params.geometry,
                titiler_cmr_url=self.config.titiler_cmr_url,
                timeout=60,
                selected_variable=params.selected_variable,
            )

            return StatsToolOutputSchema(
                statistics=result.get("statistics", {}),
                error=result.get("error"),
            )

        # VEDA COG path: items provided
        if params.items:
            raw_items = [
                {"url": item.url, "id": item.id, "datetime": item.datetime}
                for item in params.items
            ]

            raw_results = fetch_statistics_batch(
                items=raw_items,
                geometry=params.geometry,
                dst_crs=self.config.dst_crs,
                raster_api_url=self.config.raster_api_url,
                timeout=60,
            )

            results = [StatsResultItem(**r) for r in raw_results]

            logger.debug(f"Raster stats returned {len(results)} results")

            return StatsToolOutputSchema(results=results)

        return StatsToolOutputSchema(
            error="Provide either 'items' (VEDA COG path) or 'collection_metadata' (CMR path)"
        )
