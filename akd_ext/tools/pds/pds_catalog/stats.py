"""Get statistics about the PDS catalog."""

import logging

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.pds_catalog_client import PDSCatalogClient, PDSCatalogClientError

logger = logging.getLogger(__name__)


class PDSCatalogStatsInputSchema(InputSchema):
    """Input schema for PDSCatalogStatsTool.

    This tool requires no input parameters.
    """

    pass


class PDSCatalogStatsOutputSchema(OutputSchema):
    """Output schema for PDSCatalogStatsTool."""

    status: str = Field(..., description="Status of the request ('success')")
    total_datasets: int = Field(..., description="Total number of datasets in the catalog")
    by_node: dict[str, int] = Field(..., description="Dataset counts by PDS node")
    by_pds_version: dict[str, int] = Field(..., description="Dataset counts by PDS version (PDS3/PDS4)")
    by_type: dict[str, int] = Field(..., description="Dataset counts by type (volume/bundle/collection)")
    missions_count: int = Field(..., description="Total number of unique missions in the catalog")
    targets_count: int = Field(..., description="Total number of unique targets in the catalog")


class PDSCatalogStatsToolConfig(BaseToolConfig):
    """Configuration for PDSCatalogStatsTool."""

    catalog_dir: str | None = Field(
        default=None,
        description="Directory containing catalog JSONL files (uses PDS_CATALOG_DIR env var or default if None)",
    )


@mcp_tool
class PDSCatalogStatsTool(BaseTool[PDSCatalogStatsInputSchema, PDSCatalogStatsOutputSchema]):
    """Get catalog statistics.

    This tool returns comprehensive statistics about the PDS catalog including:
    - Total number of datasets
    - Breakdown by PDS node (atm, geo, img, naif, ppi, rms, sbn)
    - Breakdown by PDS version (PDS3 vs PDS4)
    - Breakdown by dataset type (volume, bundle, collection)
    - Number of unique missions
    - Number of unique targets

    Use this to understand the catalog's coverage before searching.
    """

    input_schema = PDSCatalogStatsInputSchema
    output_schema = PDSCatalogStatsOutputSchema
    config_schema = PDSCatalogStatsToolConfig

    async def _arun(self, params: PDSCatalogStatsInputSchema) -> PDSCatalogStatsOutputSchema:
        """Execute the stats retrieval.

        Args:
            params: Input parameters (none required)

        Returns:
            Catalog statistics

        Raises:
            PDSCatalogClientError: If the catalog cannot be accessed
        """
        try:
            # Create client
            client = PDSCatalogClient(catalog_dir=self.config.catalog_dir)

            # Get stats
            stats = await client.get_stats()

            return PDSCatalogStatsOutputSchema(
                status="success",
                total_datasets=stats["total_datasets"],
                by_node=stats["by_node"],
                by_pds_version=stats["by_pds_version"],
                by_type=stats["by_type"],
                missions_count=stats["missions_count"],
                targets_count=stats["targets_count"],
            )

        except PDSCatalogClientError as e:
            logger.error(f"PDS Catalog client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_stats: {e}")
            raise RuntimeError(f"Internal error retrieving stats: {e}") from e
