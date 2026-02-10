"""List missions available in the PDS catalog."""

import logging
from typing import Annotated

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.pds_catalog.types import PDS_NODE
from akd_ext.tools.pds.utils.pds_catalog_client import PDSCatalogClient, PDSCatalogClientError

logger = logging.getLogger(__name__)


class PDSCatalogMissionItem(BaseModel):
    """Mission item in list results."""

    name: str = Field(description="Mission name (proper casing)")
    count: int = Field(description="Number of datasets for this mission")
    nodes: list[str] = Field(description="List of PDS nodes containing datasets for this mission")


class PDSCatalogListMissionsInputSchema(InputSchema):
    """Input schema for PDSCatalogListMissionsTool."""

    node: PDS_NODE | None = Field(
        None,
        description="Filter by PDS node (optional)",
    )
    limit: Annotated[int, Field(ge=1, le=50)] = Field(
        50,
        description="Maximum missions to return (default 50)",
    )


class PDSCatalogListMissionsOutputSchema(OutputSchema):
    """Output schema for PDSCatalogListMissionsTool."""

    status: str = Field(..., description="Status of the request ('success')")
    count: int = Field(..., description="Number of missions returned")
    missions: list[PDSCatalogMissionItem] = Field(
        default_factory=list,
        description="List of missions with dataset counts",
    )


class PDSCatalogListMissionsToolConfig(BaseToolConfig):
    """Configuration for PDSCatalogListMissionsTool."""

    catalog_dir: str | None = Field(
        default=None,
        description="Directory containing catalog JSONL files (uses PDS_CATALOG_DIR env var or default if None)",
    )


@mcp_tool
class PDSCatalogListMissionsTool(BaseTool[PDSCatalogListMissionsInputSchema, PDSCatalogListMissionsOutputSchema]):
    """List missions available in the catalog.

    This tool returns all missions present in the PDS catalog with dataset counts.
    Use this to discover what missions have data available before searching.

    Each mission entry includes:
    - name: Mission name with proper casing
    - count: Number of datasets for this mission
    - nodes: List of PDS nodes containing data for this mission

    Optionally filter by PDS node to see missions available at specific nodes.

    """

    input_schema = PDSCatalogListMissionsInputSchema
    output_schema = PDSCatalogListMissionsOutputSchema
    config_schema = PDSCatalogListMissionsToolConfig

    async def _arun(self, params: PDSCatalogListMissionsInputSchema) -> PDSCatalogListMissionsOutputSchema:
        """Execute the mission listing.

        Args:
            params: Input parameters with optional node filter

        Returns:
            List of missions with counts and nodes

        Raises:
            PDSCatalogClientError: If the catalog cannot be accessed
        """
        try:
            # Create client
            client = PDSCatalogClient(catalog_dir=self.config.catalog_dir)

            # List missions
            missions = await client.list_missions(node=params.node, limit=params.limit)

            # Convert to output format
            mission_items = [
                PDSCatalogMissionItem(
                    name=m["name"],
                    count=m["count"],
                    nodes=m["nodes"],
                )
                for m in missions
            ]

            return PDSCatalogListMissionsOutputSchema(
                status="success",
                count=len(mission_items),
                missions=mission_items,
            )

        except PDSCatalogClientError as e:
            logger.error(f"PDS Catalog client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in list_missions: {e}")
            raise RuntimeError(f"Internal error listing missions: {e}") from e
