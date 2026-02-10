"""Search the PDS dataset catalog."""

import logging
from datetime import date
from typing import Annotated, Any

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.pds_catalog.types import DATASET_TYPE, FIELD_PROFILE, PDS_NODE, PDS_VERSION
from akd_ext.tools.pds.utils.pds_catalog_client import (
    FIELD_PROFILES,
    MAX_RESULTS_LIMIT,
    PDSCatalogClient,
    PDSCatalogClientError,
    filter_dataset,
)

logger = logging.getLogger(__name__)


class PDSCatalogSearchInputSchema(InputSchema):
    """Input schema for PDSCatalogSearchTool."""

    query: str | None = Field(
        None,
        description=(
            "Text search across title, description, missions, targets, instruments. "
            "Examples: 'mars images', 'cassini saturn', 'comet spectra'"
        ),
    )
    node: PDS_NODE | None = Field(
        None,
        description=(
            "Filter by PDS node. Valid values: "
            "atm (Atmospheres), geo (Geosciences), img (Imaging), "
            "naif (SPICE/Navigation), ppi (Plasma), rms (Ring-Moon), sbn (Small Bodies)"
        ),
    )
    mission: str | None = Field(
        None,
        description="Filter by mission name. Examples: 'Cassini', 'Mars 2020', 'Voyager'",
    )
    instrument: str | None = Field(
        None,
        description="Filter by instrument name. Examples: 'JEDI', 'CAPS', 'magnetometer'",
    )
    target: str | None = Field(
        None,
        description="Filter by target body. Examples: 'Mars', 'Saturn', 'Comet'",
    )
    pds_version: PDS_VERSION | None = Field(
        None,
        description="Filter by archive version: 'PDS3' or 'PDS4'",
    )
    dataset_type: DATASET_TYPE | None = Field(
        None,
        description="Filter by type: 'volume' (PDS3), 'bundle' (PDS4), or 'collection' (PDS4)",
    )
    start_date: str | None = Field(
        None,
        description="Filter datasets that have data on or after this date (YYYY-MM-DD)",
    )
    stop_date: str | None = Field(
        None,
        description="Filter datasets that have data on or before this date (YYYY-MM-DD)",
    )
    limit: Annotated[int, Field(ge=1, le=50)] = Field(
        20,
        description="Maximum results to return (default 20, max 50)",
    )
    offset: Annotated[int, Field(ge=0)] = Field(
        0,
        description="Skip first N results for pagination (default 0)",
    )
    fields: FIELD_PROFILE = Field(
        "summary",
        description="Response detail level - 'essential', 'summary' (default), or 'full'",
    )


class PDSCatalogSearchOutputSchema(OutputSchema):
    """Output schema for PDSCatalogSearchTool."""

    status: str = Field(..., description="Status of the search ('success' or 'error')")
    count: int = Field(..., description="Number of datasets returned in this response")
    total: int = Field(..., description="Total number of matching datasets")
    offset: int = Field(..., description="Offset used for pagination")
    limit: int = Field(..., description="Limit used for pagination")
    has_more: bool = Field(..., description="Whether more results are available")
    fields: str = Field(..., description="Field profile used ('essential', 'summary', or 'full')")
    datasets: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of matching datasets with fields based on the selected profile",
    )


class PDSCatalogSearchToolConfig(BaseToolConfig):
    """Configuration for PDSCatalogSearchTool."""

    catalog_dir: str | None = Field(
        default=None,
        description="Directory containing catalog JSONL files (uses PDS_CATALOG_DIR env var or default if None)",
    )


@mcp_tool
class PDSCatalogSearchTool(BaseTool[PDSCatalogSearchInputSchema, PDSCatalogSearchOutputSchema]):
    """Search the PDS dataset catalog.

    This tool searches across all PDS nodes for datasets matching your criteria.
    The catalog is a pre-scraped collection of PDS datasets stored locally in JSONL format.

    Supports:
    - Text search across titles, descriptions, and metadata
    - Filtering by node, mission, instrument, target
    - Temporal filtering by observation dates
    - Pagination for large result sets
    - Three detail levels: essential, summary, and full

    PDS Nodes:
    - atm: Atmospheres node
    - geo: Geosciences node
    - img: Imaging node
    - naif: Navigation and Ancillary Information (SPICE kernels)
    - ppi: Planetary Plasma Interactions node
    - rms: Ring-Moon Systems node
    - sbn: Small Bodies node

    Dataset Types:
    - volume: PDS3 data volumes
    - bundle: PDS4 top-level collections
    - collection: PDS4 data collections
    """

    input_schema = PDSCatalogSearchInputSchema
    output_schema = PDSCatalogSearchOutputSchema
    config_schema = PDSCatalogSearchToolConfig

    async def _arun(self, params: PDSCatalogSearchInputSchema) -> PDSCatalogSearchOutputSchema:
        """Execute the catalog search.

        Args:
            params: Input parameters for the search

        Returns:
            Search results with datasets and pagination metadata

        Raises:
            PDSCatalogClientError: If the catalog cannot be loaded or searched
        """
        try:
            # Create client
            client = PDSCatalogClient(catalog_dir=self.config.catalog_dir)

            # Parse date strings
            parsed_start = date.fromisoformat(params.start_date) if params.start_date else None
            parsed_stop = date.fromisoformat(params.stop_date) if params.stop_date else None

            # Enforce max limit
            effective_limit = min(params.limit, MAX_RESULTS_LIMIT)

            # Get field set for filtering
            field_set = FIELD_PROFILES.get(params.fields, FIELD_PROFILES["summary"])

            # Perform search
            datasets, total = await client.search(
                query=params.query,
                node=params.node,
                mission=params.mission,
                instrument=params.instrument,
                target=params.target,
                pds_version=params.pds_version,
                dataset_type=params.dataset_type,
                start_date=parsed_start,
                stop_date=parsed_stop,
                limit=effective_limit,
                offset=params.offset,
            )

            # Filter datasets to requested fields
            results = [filter_dataset(d, field_set) for d in datasets]
            has_more = params.offset + len(results) < total

            return PDSCatalogSearchOutputSchema(
                status="success",
                count=len(results),
                total=total,
                offset=params.offset,
                limit=effective_limit,
                has_more=has_more,
                fields=params.fields,
                datasets=results,
            )

        except PDSCatalogClientError as e:
            logger.error(f"PDS Catalog client error: {e}")
            raise
        except ValueError as e:
            # Date parsing errors
            logger.error(f"Invalid date format: {e}")
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD format: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in catalog search: {e}")
            raise RuntimeError(f"Internal error during catalog search: {e}") from e
