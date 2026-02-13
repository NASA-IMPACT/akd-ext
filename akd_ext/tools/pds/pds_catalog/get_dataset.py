"""Get detailed information about a specific PDS dataset."""

from loguru import logger
from typing import Any

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.pds_catalog_client import (
    FIELD_PROFILES,
    PDSCatalogClient,
    PDSCatalogClientError,
    filter_dataset,
)


class PDSCatalogGetDatasetInputSchema(InputSchema):
    """Input schema for PDSCatalogGetDatasetTool."""

    dataset_id: str = Field(
        ...,
        description="The dataset ID (LIDVID for PDS4, VOLUME_ID for PDS3)",
    )


class PDSCatalogGetDatasetOutputSchema(OutputSchema):
    """Output schema for PDSCatalogGetDatasetTool."""

    status: str = Field(..., description="Status of the request ('success' or 'not_found')")
    dataset: dict[str, Any] | None = Field(
        None,
        description="Full dataset information if found",
    )
    error: str | None = Field(
        None,
        description="Error message if dataset not found",
    )


class PDSCatalogGetDatasetToolConfig(BaseToolConfig):
    """Configuration for PDSCatalogGetDatasetTool."""

    catalog_dir: str | None = Field(
        default=None,
        description="Directory containing catalog JSONL files (uses PDS_CATALOG_DIR env var or default if None)",
    )


@mcp_tool
class PDSCatalogGetDatasetTool(BaseTool[PDSCatalogGetDatasetInputSchema, PDSCatalogGetDatasetOutputSchema]):
    """Get detailed information about a specific dataset.

    This tool retrieves full metadata for a specific PDS dataset by its ID.
    Use this when you have a dataset ID from search results and need complete details.

    Dataset IDs:
    - PDS4: LIDVID format (e.g., "urn:nasa:pds:cassini_iss::1.0")
    - PDS3: VOLUME_ID format (e.g., "GO_0017")

    Returns all available metadata including:
    - Basic info: ID, title, description
    - Classification: node, PDS version, type
    - Discovery metadata: missions, targets, instruments
    - Temporal coverage: start and stop dates
    - Access URLs: browse, download, label
    - Additional metadata: keywords, processing level

    """

    input_schema = PDSCatalogGetDatasetInputSchema
    output_schema = PDSCatalogGetDatasetOutputSchema
    config_schema = PDSCatalogGetDatasetToolConfig

    async def _arun(self, params: PDSCatalogGetDatasetInputSchema) -> PDSCatalogGetDatasetOutputSchema:
        """Execute the dataset retrieval.

        Args:
            params: Input parameters with dataset ID

        Returns:
            Dataset information if found, error message otherwise

        Raises:
            PDSCatalogClientError: If the catalog cannot be accessed
        """
        try:
            # Create client
            client = PDSCatalogClient(catalog_dir=self.config.catalog_dir)

            # Get dataset
            dataset = await client.get_dataset(params.dataset_id)

            if dataset is None:
                return PDSCatalogGetDatasetOutputSchema(
                    status="not_found",
                    error=f"Dataset not found: {params.dataset_id}",
                )

            # Return full fields
            field_set = FIELD_PROFILES["full"]
            filtered_dataset = filter_dataset(dataset, field_set)

            return PDSCatalogGetDatasetOutputSchema(
                status="success",
                dataset=filtered_dataset,
            )

        except PDSCatalogClientError as e:
            logger.error(f"PDS Catalog client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_dataset: {e}")
            raise RuntimeError(f"Internal error retrieving dataset: {e}") from e
