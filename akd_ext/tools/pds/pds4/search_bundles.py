"""Search for bundles in PDS4 with comprehensive results."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.pds4.types import PROCESSING_LEVEL
from akd_ext.tools.pds.utils.pds4_client import PDS4Client, PDS4ClientError


class BundleSummary(BaseModel):
    """Bundle item in search results."""

    id: str
    lid: str | None = None
    lidvid: str | None = None
    title: str | None = None
    investigation_area: dict | None = None
    identification_area: dict | None = None
    target_identification: dict | None = None
    time_coordinates: dict | None = None
    harvest_info: dict | None = None


class PDS4SearchBundlesInputSchema(InputSchema):
    """Input schema for PDS4SearchBundlesTool."""

    title_query: str | None = Field(None, description="Search query for bundle titles (e.g., 'Lunar', 'Mars')")
    start_time: str | None = Field(
        None, description="Start of time range (ISO 8601 format, e.g., '2020-01-01T00:00:00Z')"
    )
    end_time: str | None = Field(None, description="End of time range (ISO 8601 format)")
    processing_level: PROCESSING_LEVEL | None = Field(None, description="Filter by processing level")
    limit: int = Field(0, ge=0, le=100, description="Number of actual products to return (set to 0 for facets only)")
    facet_fields: str | None = Field(
        None,
        description="Comma-separated list of fields to facet on (e.g., 'pds:Identification_Area.pds:title,lidvid')",
    )
    facet_limit: int = Field(25, ge=1, le=100, description="Maximum number of facet values to return (default: 25)")


class PDS4SearchBundlesOutputSchema(OutputSchema):
    """Output schema for PDS4SearchBundlesTool."""

    total_hits: int = Field(..., description="Total number of matching bundles")
    query_time_ms: int | None = Field(None, description="Query execution time in milliseconds")
    query: str | None = Field(None, description="The query string that was executed")
    limit: int = Field(..., description="Number of results returned")
    bundles: list[BundleSummary] = Field(default_factory=list, description="List of matching bundles")
    facets: dict[str, dict[str, int]] = Field(default_factory=dict, description="Facet counts organized by field name")


class PDS4SearchBundlesToolConfig(BaseToolConfig):
    """Configuration for PDS4SearchBundlesTool."""

    base_url: str = Field(
        default=os.getenv("PDS4_BASE_URL", "https://pds.mcp.nasa.gov/api/search/1/"),
        description="PDS4 API base URL (override with PDS4_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class PDS4SearchBundlesTool(BaseTool[PDS4SearchBundlesInputSchema, PDS4SearchBundlesOutputSchema]):
    """Search for bundles in PDS4 with comprehensive results.

    This tool searches for data bundles in the NASA Planetary Data System (PDS4) registry.
    Bundles are high-level organizational units that group related collections.

    Every PDS4 file is associated with a unique URN identifier. For example:
    - urn:nasa:pds:context:investigation:mission.juno is the URN for the Juno Mission
    - urn:nasa:pds:cassini_iss is a bundle URN for Cassini ISS data

    Use faceting (set limit=0 and provide facet_fields) to discover available values
    before narrowing down your search with specific filters.

    Processing Levels:
    - Raw: Unprocessed instrument data as received from spacecraft
    - Calibrated: Instrument effects removed, science-ready data
    - Derived: Higher-level data products (maps, mosaics, etc.)
    """

    input_schema = PDS4SearchBundlesInputSchema
    output_schema = PDS4SearchBundlesOutputSchema
    config_schema = PDS4SearchBundlesToolConfig

    async def _arun(self, params: PDS4SearchBundlesInputSchema) -> PDS4SearchBundlesOutputSchema:
        """Execute the bundle search.

        Args:
            params: Input parameters for the search

        Returns:
            Search results with bundles and facets

        Raises:
            PDS4ClientError: If the API request fails
        """
        try:
            # Parse facet fields if provided
            facet_field_list = None
            if params.facet_fields:
                facet_field_list = [field.strip() for field in params.facet_fields.split(",")]

            # Create client and perform search
            async with PDS4Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.search_bundles(
                    title_query=params.title_query,
                    start_time=params.start_time,
                    end_time=params.end_time,
                    processing_level=params.processing_level,
                    limit=params.limit,
                    facet_fields=facet_field_list,
                    facet_limit=params.facet_limit,
                )

            # Format response with requested properties
            bundles: list[BundleSummary] = []
            for bundle in response.data:
                bundle_data = BundleSummary(
                    id=bundle.id,
                    lid=bundle.lid,
                    lidvid=bundle.lidvid,
                    title=bundle.title,
                    investigation_area=(
                        bundle.investigation_area.model_dump(exclude_none=True) if bundle.investigation_area else None
                    ),
                    identification_area=(
                        bundle.identification_area.model_dump(exclude_none=True) if bundle.identification_area else None
                    ),
                    target_identification=(
                        bundle.target_identification.model_dump(exclude_none=True)
                        if bundle.target_identification
                        else None
                    ),
                    time_coordinates=(
                        bundle.time_coordinates.model_dump(exclude_none=True) if bundle.time_coordinates else None
                    ),
                    harvest_info=bundle.harvest_info.model_dump(exclude_none=True) if bundle.harvest_info else None,
                )
                bundles.append(bundle_data)

            # Format facets
            facets: dict[str, dict[str, int]] = {}
            for facet in response.facets:
                facets[facet.property] = facet.counts

            return PDS4SearchBundlesOutputSchema(
                total_hits=response.summary.hits,
                query_time_ms=response.summary.took,
                query=response.summary.q,
                limit=params.limit,
                bundles=bundles,
                facets=facets,
            )

        except PDS4ClientError as e:
            logger.error(f"PDS4 client error in search_bundles: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_bundles: {e}")
            raise RuntimeError(f"Internal error during bundle search: {e}") from e
