"""List targets (celestial bodies) available in the PDS catalog."""

import logging
from typing import Annotated

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.pds_catalog.types import PDS_NODE
from akd_ext.tools.pds.utils.pds_catalog_client import PDSCatalogClient, PDSCatalogClientError

logger = logging.getLogger(__name__)


class PDSCatalogTargetItem(BaseModel):
    """Target item in list results."""

    name: str = Field(description="Target name (proper casing)")
    count: int = Field(description="Number of datasets for this target")
    nodes: list[str] = Field(description="List of PDS nodes containing datasets for this target")


class PDSCatalogListTargetsInputSchema(InputSchema):
    """Input schema for PDSCatalogListTargetsTool."""

    node: PDS_NODE | None = Field(
        None,
        description="Filter by PDS node (optional)",
    )
    limit: Annotated[int, Field(ge=1, le=50)] = Field(
        50,
        description="Maximum targets to return (default 50)",
    )


class PDSCatalogListTargetsOutputSchema(OutputSchema):
    """Output schema for PDSCatalogListTargetsTool."""

    status: str = Field(..., description="Status of the request ('success')")
    count: int = Field(..., description="Number of targets returned")
    targets: list[PDSCatalogTargetItem] = Field(
        default_factory=list,
        description="List of targets with dataset counts",
    )


class PDSCatalogListTargetsToolConfig(BaseToolConfig):
    """Configuration for PDSCatalogListTargetsTool."""

    catalog_dir: str | None = Field(
        default=None,
        description="Directory containing catalog JSONL files (uses PDS_CATALOG_DIR env var or default if None)",
    )


@mcp_tool
class PDSCatalogListTargetsTool(BaseTool[PDSCatalogListTargetsInputSchema, PDSCatalogListTargetsOutputSchema]):
    """List targets (celestial bodies) available in the catalog.

    This tool returns all targets (planets, moons, asteroids, comets, etc.) present
    in the PDS catalog with dataset counts. Use this to discover what celestial bodies
    have data available before searching.

    Each target entry includes:
    - name: Target name with proper casing (e.g., "Mars", "Saturn", "Enceladus")
    - count: Number of datasets for this target
    - nodes: List of PDS nodes containing data for this target

    Optionally filter by PDS node to see targets available at specific nodes.

    Example Usage:
        # List all targets
        tool = PDSCatalogListTargetsTool()
        result = await tool.arun(PDSCatalogListTargetsInputSchema())

        # List targets at the Ring-Moon Systems node
        result = await tool.arun(PDSCatalogListTargetsInputSchema(
            node="rms"
        ))

        # Get top 30 targets
        result = await tool.arun(PDSCatalogListTargetsInputSchema(
            limit=30
        ))
    """

    input_schema = PDSCatalogListTargetsInputSchema
    output_schema = PDSCatalogListTargetsOutputSchema
    config_schema = PDSCatalogListTargetsToolConfig

    async def _arun(self, params: PDSCatalogListTargetsInputSchema) -> PDSCatalogListTargetsOutputSchema:
        """Execute the target listing.

        Args:
            params: Input parameters with optional node filter

        Returns:
            List of targets with counts and nodes

        Raises:
            PDSCatalogClientError: If the catalog cannot be accessed
        """
        try:
            # Create client
            client = PDSCatalogClient(catalog_dir=self.config.catalog_dir)

            # List targets
            targets = await client.list_targets(node=params.node, limit=params.limit)

            # Convert to output format
            target_items = [
                PDSCatalogTargetItem(
                    name=t["name"],
                    count=t["count"],
                    nodes=t["nodes"],
                )
                for t in targets
            ]

            return PDSCatalogListTargetsOutputSchema(
                status="success",
                count=len(target_items),
                targets=target_items,
            )

        except PDSCatalogClientError as e:
            logger.error(f"PDS Catalog client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in list_targets: {e}")
            raise RuntimeError(f"Internal error listing targets: {e}") from e
