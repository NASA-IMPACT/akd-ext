"""
Tool to search items from the STAC API.

"""

from pystac_client import Client

from email.policy import default
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field
from .utils import validate_datetime
from akd_ext.mcp import mcp_tool


class STACItemSearchInputSchema(InputSchema):
    """Input schema for the STACItemSearchTool."""

    collections: list[str] = Field(..., description="Collection IDs to search (e.g. ['no2-monthly']")
    bbox: list[float] = Field(default=[], description="Bounding box [west, south, east, north]")
    datetime: str = Field(
        default="", description="ISO-8601 datetime range (e.g. '2021-10-01/2021-12-31'"
    )
    limit: int = Field(default=10, description="Maximum number of items to return")

class STACItemSearchOutputSchema(OutputSchema):
    """Output schema for the STACItemSearchTool."""

    item_ids: list[str] = Field(default_factory=list, description="Found item IDs")
    count: int = Field(default=0, description="Total number of items found")
    error: str | None = Field(default=None, description="Error message if search failed")

class STACItemSearchToolConfig(BaseToolConfig):
    """Config for the STACItemSearchTool."""

    root: str = Field(default="https://dev.openveda.cloud/api/stac", description="STAC root URL")


@mcp_tool
class STACItemSearchTool(BaseTool[STACItemSearchInputSchema, STACItemSearchOutputSchema]):
    """
    Identity tool that returns the input query unchanged.
    Serves as a reference implementation for akd-ext tools.
    """

    input_schema = STACItemSearchInputSchema
    output_schema = STACItemSearchOutputSchema
    config_schema = STACItemSearchToolConfig

    async def _arun(self, params: STACItemSearchInputSchema ) -> STACItemSearchOutputSchema:
        """Return the input query as-is."""

        # Validate datetime format
        _, dt_error = validate_datetime(params.datetime)
        if dt_error:
            return STACItemSearchOutputSchema(item_ids=[], count=0, error=dt_error)
        
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
                items.append({
                    "id": it.id,
                    "collection": getattr(it, "collection_id", None),
                    "properties": dict(it.properties or {}),
                })
            item_ids =  [it["id"] for it in items]
            return STACItemSearchOutputSchema(item_ids=item_ids, count=len(item_ids))
        except Exception as e:
            return STACItemSearchOutputSchema(item_ids=[], count=0, error=str(e))

