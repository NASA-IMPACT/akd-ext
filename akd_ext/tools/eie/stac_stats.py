"""
Tool to calculate statistics for STAC items.

"""

from pydantic import BaseModel, Field
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from akd_ext.mcp import mcp_tool
from .utils import fetch_statistics_batch


class StacItemInfo(BaseModel):
    """Info about a STAC item including its COG asset URL."""

    id: str = Field(description="Item ID")
    collection: str | None = Field(default=None, description="Collection ID")
    datetime: str | None = Field(default=None, description="Item datetime")
    asset_url: str | None = Field(default=None, description="URL to the COG asset")


class PlaceResult(BaseModel):
    """Result from place resolution."""

    place: str | None = Field(description="Resolved place name")
    bbox: list[float] | None = Field(description="Bounding box [west, south, east, north]")
    geometry: dict | None = Field(default=None, description="GeoJSON geometry (Polygon/MultiPolygon) for the place")
    error: str | None = Field(default=None, description="Error message if resolution failed")


class StacSearchResult(BaseModel):
    """Result from STAC search."""

    item_ids: list[str] = Field(default_factory=list, description="Found item IDs")
    items: list[StacItemInfo] = Field(default_factory=list, description="Item details with COG asset URLs")
    count: int = Field(default=0, description="Total number of items found")
    error: str | None = Field(default=None, description="Error message if search failed")


class STACItemStatsInputSchema(InputSchema):
    """Input schema for the STACItemStatsTool."""

    stac_result: StacSearchResult | None = Field(
        default=None,
        description="Result from stac_search tool with items and asset URLs",
    )
    place_result: PlaceResult | None = Field(
        default=None,
        description="Result from get_place tool with bbox and geometry",
    )


class ItemStats(BaseModel):
    """Statistics for a single COG item."""

    id: str | None = Field(default=None, description="Item ID")
    datetime: str | None = Field(default=None, description="Item datetime")
    statistics: dict = Field(default_factory=dict, description="Per-band statistics")
    error: str | None = Field(default=None, description="Error if this item failed")


class STACItemStatsOutputSchema(OutputSchema):
    """Output schema for the STACItemStatsTool."""

    items: list[ItemStats] = Field(default_factory=list, description="Statistics for each item")
    error: str | None = Field(default=None, description="Error message if request failed")


class STACItemStatsToolConfig(BaseToolConfig):
    """Config for the STACItemStatsTool."""

    raster_api_url: str = Field(default="https://dev.openveda.cloud/api/raster", description="Raster API URL")


@mcp_tool
class STACItemStatsTool(BaseTool[STACItemStatsInputSchema, STACItemStatsOutputSchema]):
    """
    Compute statistics for STAC items over a bounding box.
    """

    input_schema = STACItemStatsInputSchema
    output_schema = STACItemStatsOutputSchema
    config_schema = STACItemStatsToolConfig

    async def _arun(self, params: STACItemStatsInputSchema) -> STACItemStatsOutputSchema:
        """Compute statistics for STAC items over a bounding box."""
        try:
            if not params.stac_result or not params.stac_result.items:
                return STACItemStatsOutputSchema(items=[], error="No items from stac_search. Run stac_search first.")
            if not params.place_result or not params.place_result.geometry:
                return STACItemStatsOutputSchema(items=[], error="No geometry from get_place. Run get_place first.")

            # Convert state items to batch format
            batch_items = [
                {"url": it.asset_url, "id": it.id, "datetime": it.datetime}
                for it in params.stac_result.items
                if it.asset_url
            ]

            if not batch_items:
                return STACItemStatsOutputSchema(items=[], error="No items with asset URLs found.")

            results = fetch_statistics_batch(
                items=batch_items,
                geometry=params.place_result.geometry,
                dst_crs="+proj=cea",
                raster_api_url=self.config.raster_api_url,
            )

            item_stats = [
                ItemStats(
                    id=r.get("id"),
                    datetime=r.get("datetime"),
                    statistics=r.get("statistics", {}),
                    error=r.get("error"),
                )
                for r in results
            ]

            return STACItemStatsOutputSchema(items=item_stats)

        except Exception as e:
            return STACItemStatsOutputSchema(items=[], error=str(e))
