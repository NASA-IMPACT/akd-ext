"""
Tool to search items from a STAC API endpoint.
"""

from pydantic import Field, BaseModel
from pystac_client import Client

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from akd_ext.mcp import mcp_tool

from .utils import validate_datetime


class StacItemInfo(BaseModel):
    """Info about a STAC item including its COG asset URL."""

    id: str = Field(description="Item ID")
    collection: str | None = Field(default=None, description="Collection ID")
    datetime: str | None = Field(default=None, description="Item datetime")
    asset_url: str | None = Field(default=None, description="URL to the COG asset")


class STACItemSearchInputSchema(InputSchema):
    """Input schema for the STACItemSearchTool."""

    collections: list[str] = Field(..., description="Collection IDs to search (e.g. ['no2-monthly'])")
    bbox: list[float] = Field(default=[], description="Bounding box [west, south, east, north]")
    datetime: str = Field(default="", description="ISO-8601 datetime range (e.g. '2021-10-01/2021-12-31')")
    limit: int = Field(default=10, description="Maximum number of items to return")


class STACItemSearchOutputSchema(OutputSchema):
    """Output schema for the STACItemSearchTool."""

    item_ids: list[str] = Field(default_factory=list, description="Found item IDs")
    items: list[StacItemInfo] = Field(default_factory=list, description="Item details with COG asset URLs")
    count: int = Field(default=0, description="Total number of items found")
    error: str | None = Field(default=None, description="Error message if search failed")


class STACItemSearchToolConfig(BaseToolConfig):
    """Config for the STACItemSearchTool."""

    root: str = Field(default="https://dev.openveda.cloud/api/stac", description="STAC root URL")


@mcp_tool
class STACItemSearchTool(BaseTool[STACItemSearchInputSchema, STACItemSearchOutputSchema]):
    """
    Tool to search items from a STAC API endpoint.
    Returns matching item IDs and count.
    """

    input_schema = STACItemSearchInputSchema
    output_schema = STACItemSearchOutputSchema
    config_schema = STACItemSearchToolConfig

    async def _arun(self, params: STACItemSearchInputSchema) -> STACItemSearchOutputSchema:
        """Return the input query as-is."""

        # Validate datetime format
        _, dt_error = validate_datetime(params.datetime)
        if dt_error:
            return STACItemSearchOutputSchema(item_ids=[], items=[], count=0, error=dt_error)

        try:
            config = self.config
            root = config.root.rstrip("/")
            client = Client.open(root, headers={"Accept": "application/json"})

            # Use first collection if multiple provided
            col = params.collections[0] if params.collections else None

            search = client.search(
                collections=[col] if col else None,
                bbox=params.bbox,
                datetime=params.datetime,
                max_items=params.limit,
            )

            items = []
            for it in search.items():
                # Extract COG asset URL - try common asset keys
                asset_url = None
                if it.assets:
                    # Try common asset keys in order of preference
                    for key in ["cog_default", "data", "visual", "default", col]:
                        if key and key in it.assets:
                            asset_url = it.assets[key].href
                            break
                    # Fallback: use first asset with a tiff type
                    if not asset_url:
                        for asset in it.assets.values():
                            if asset.href and (".tif" in asset.href or "geotiff" in (asset.media_type or "")):
                                asset_url = asset.href
                                break
                    # Last resort: use first asset
                    if not asset_url and it.assets:
                        first_asset = next(iter(it.assets.values()), None)
                        if first_asset:
                            asset_url = first_asset.href

                # Extract datetime from properties (try datetime, then start_datetime)
                dt = None
                if it.properties:
                    dt = it.properties.get("datetime") or it.properties.get("start_datetime")

                items.append(
                    {
                        "id": it.id,
                        "collection": getattr(it, "collection_id", None),
                        "datetime": dt,
                        "asset_url": asset_url,
                        "properties": dict(it.properties or {}),
                    }
                )

            item_ids = [it["id"] for it in items]
            items_data = [
                StacItemInfo(
                    id=it["id"],
                    collection=it.get("collection"),
                    datetime=it.get("datetime"),
                    asset_url=it.get("asset_url"),
                )
                for it in items
            ]
            return STACItemSearchOutputSchema(item_ids=item_ids, items=items_data, count=len(item_ids))
        except Exception as e:
            return STACItemSearchOutputSchema(item_ids=[], count=0, error=str(e))
