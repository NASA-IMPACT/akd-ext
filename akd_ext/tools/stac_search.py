"""
VEDA STAC catalog search tool.

This tool queries the VEDA STAC API for spatio-temporal asset catalog items,
returning matching items with their COG asset URLs and metadata.
"""

import os

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from loguru import logger
from pydantic import Field
from pystac_client import Client

from akd_ext.mcp import mcp_tool

DEFAULT_STAC_URL = "https://dev.openveda.cloud/api/stac"


class STACSearchToolConfig(BaseToolConfig):
    """Configuration for the STAC Search Tool."""

    stac_url: str = Field(
        default=os.getenv("VEDA_STAC_URL", DEFAULT_STAC_URL),
        description="Root URL for the STAC API catalog",
    )


class STACItem(OutputSchema):
    """A single item result from a STAC search."""

    id: str = Field(..., description="STAC item ID")
    collection: str | None = Field(None, description="Collection the item belongs to")
    datetime: str | None = Field(None, description="Temporal extent of the item")
    asset_url: str | None = Field(None, description="URL of the primary COG asset")
    properties: dict = Field(default_factory=dict, description="Full item properties")


class STACSearchToolInputSchema(InputSchema):
    """Input schema for STAC search queries."""

    collections: list[str] = Field(
        ..., description="Collection IDs to search within (uses the first entry)"
    )
    bbox: list[float] = Field(
        ..., description="Bounding box as [west, south, east, north] in decimal degrees"
    )
    datetime: str = Field(
        ...,
        description="Temporal filter as a single datetime or date range (e.g. '2020-01-01/2020-12-31')",
    )
    limit: int = Field(
        default=15, ge=1, le=100, description="Maximum number of items to return"
    )


class STACSearchToolOutputSchema(OutputSchema):
    """Output schema for STAC search results."""

    items: list[STACItem] = Field(
        ..., description="List of matching STAC items"
    )
    item_ids: list[str] = Field(
        ..., description="IDs of the returned items"
    )


def _extract_asset_url(item, collection_hint: str | None) -> str | None:
    """Pick the best COG asset URL from a STAC item."""
    if not item.assets:
        return None

    # Try common asset keys in order of preference
    for key in ("cog_default", "data", "visual", "default", collection_hint):
        if key and key in item.assets:
            return item.assets[key].href

    # Fallback: first asset with a tiff media type
    for asset in item.assets.values():
        if asset.href and (
            ".tif" in asset.href or "geotiff" in (asset.media_type or "")
        ):
            return asset.href

    # Last resort: first asset
    first_asset = next(iter(item.assets.values()), None)
    return first_asset.href if first_asset else None


@mcp_tool
class STACSearchTool(BaseTool[STACSearchToolInputSchema, STACSearchToolOutputSchema]):
    """
    Search the VEDA STAC catalog for spatio-temporal asset catalog items.

    The VEDA (Visualization, Exploration, and Data Analysis) STAC API provides
    access to Earth observation datasets hosted on NASA's open-data platform.
    Use this tool to discover and retrieve cloud-optimized GeoTIFF (COG) assets
    by specifying a collection, bounding box, and time range.

    Input parameters (query-time, LLM-controllable):
    - collections: List of STAC collection IDs to search (uses the first entry)
    - bbox: Bounding box as [west, south, east, north]
    - datetime: Temporal filter (ISO-8601 datetime or range, e.g. '2020-01-01/2020-12-31')
    - limit: Maximum items to return (1-100, default 15)

    Configuration parameters (instance-time, user-controlled):
    - stac_url: Root URL of the STAC API (default: VEDA dev catalog)

    Returns items with:
    - id: STAC item identifier
    - collection: Parent collection ID
    - datetime: Temporal extent
    - asset_url: URL to the primary COG asset
    - properties: Full item property dictionary
    """

    input_schema = STACSearchToolInputSchema
    output_schema = STACSearchToolOutputSchema
    config_schema = STACSearchToolConfig

    async def _arun(
        self, params: STACSearchToolInputSchema
    ) -> STACSearchToolOutputSchema:
        """Execute STAC search and return matching items."""
        root = self.config.stac_url.rstrip("/")
        client = Client.open(root, headers={"Accept": "application/json"})

        col = params.collections[0] if params.collections else None
        logger.debug(
            f"STAC search: collection={col}, bbox={params.bbox}, "
            f"datetime={params.datetime}, limit={params.limit}"
        )

        search = client.search(
            collections=[col] if col else None,
            bbox=params.bbox,
            datetime=params.datetime,
            max_items=params.limit,
        )

        items: list[STACItem] = []
        for it in search.items():
            dt = None
            if it.properties:
                dt = it.properties.get("datetime") or it.properties.get(
                    "start_datetime"
                )

            items.append(
                STACItem(
                    id=it.id,
                    collection=getattr(it, "collection_id", None),
                    datetime=dt,
                    asset_url=_extract_asset_url(it, col),
                    properties=dict(it.properties or {}),
                )
            )

        logger.debug(f"STAC search returned {len(items)} items")

        return STACSearchToolOutputSchema(
            items=items,
            item_ids=[item.id for item in items],
        )
