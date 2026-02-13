"""Search PDS data collections filtered by instrument, target, instrument host, and investigation."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.pds4.types import PROCESSING_LEVEL
from akd_ext.tools.pds.utils.pds4_client import PDS4Client, PDS4ClientError


class CollectionSummary(BaseModel):
    """Collection item in search results."""

    id: str
    lid: str | None = None
    lidvid: str | None = None
    title: str | None = None
    ref_lid_instrument: str | None = None
    ref_lid_target: str | None = None
    ref_lid_instrument_host: str | None = None
    ref_lid_investigation: str | None = None
    label_file_info: dict | None = None


class PDS4SearchCollectionsInputSchema(InputSchema):
    """Input schema for PDS4SearchCollectionsTool."""

    ref_lid_instrument: str | None = Field(
        None, description="URN identifier for instrument (e.g. urn:nasa:pds:context:instrument:mars2020.mastcamz)"
    )
    ref_lid_target: str | None = Field(
        None, description="URN identifier for target (e.g. urn:nasa:pds:context:target:planet.mars)"
    )
    ref_lid_instrument_host: str | None = Field(
        None,
        description="URN identifier for instrument host (e.g. urn:nasa:pds:context:instrument_host:spacecraft.mars2020)",
    )
    ref_lid_investigation: str | None = Field(
        None, description="URN identifier for investigation (e.g. urn:nasa:pds:context:investigation:mission.mars2020)"
    )
    start_time: str | None = Field(
        None, description="Start of time range in ISO 8601 format (e.g., '2020-01-01T00:00:00Z')"
    )
    end_time: str | None = Field(
        None, description="End of time range in ISO 8601 format (e.g., '2021-01-01T00:00:00Z')"
    )
    processing_level: PROCESSING_LEVEL | None = Field(None, description="Filter by calibration level")
    limit: int = Field(10, ge=0, le=100, description="Max results (default 10)")


class PDS4SearchCollectionsOutputSchema(OutputSchema):
    """Output schema for PDS4SearchCollectionsTool."""

    total_hits: int = Field(..., description="Total number of matching collections")
    query_time_ms: int | None = Field(None, description="Query execution time in milliseconds")
    query: str | None = Field(None, description="The query string that was executed")
    limit: int = Field(..., description="Number of results requested")
    collections: list[CollectionSummary] = Field(default_factory=list, description="List of matching collections")


class PDS4SearchCollectionsToolConfig(BaseToolConfig):
    """Configuration for PDS4SearchCollectionsTool."""

    base_url: str = Field(
        default=os.getenv("PDS4_BASE_URL", "https://pds.mcp.nasa.gov/api/search/1/"),
        description="PDS4 API base URL (override with PDS4_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


@mcp_tool
class PDS4SearchCollectionsTool(BaseTool[PDS4SearchCollectionsInputSchema, PDS4SearchCollectionsOutputSchema]):
    """Search PDS data collections filtered by instrument, target, instrument host, investigation, time range, or processing level.

    Example: Mars Reconnaissance Orbiter HiRISE data collections targeting Mars.

    Collections organize data products from specific instruments and missions.
    Use context URNs from search_investigations, search_targets, search_instruments, or search_instrument_hosts
    to filter collections by their associated context products.

    Processing Levels:
    - Raw: Unprocessed instrument data
    - Calibrated: Instrument effects removed
    - Derived: Higher-level data products
    """

    input_schema = PDS4SearchCollectionsInputSchema
    output_schema = PDS4SearchCollectionsOutputSchema
    config_schema = PDS4SearchCollectionsToolConfig

    async def _arun(self, params: PDS4SearchCollectionsInputSchema) -> PDS4SearchCollectionsOutputSchema:
        """Execute the collection search."""
        try:
            async with PDS4Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.search_context_collections(
                    ref_lid_instrument=params.ref_lid_instrument,
                    ref_lid_target=params.ref_lid_target,
                    ref_lid_instrument_host=params.ref_lid_instrument_host,
                    ref_lid_investigation=params.ref_lid_investigation,
                    start_time=params.start_time,
                    end_time=params.end_time,
                    processing_level=params.processing_level,
                    limit=params.limit,
                )

            collections: list[CollectionSummary] = []
            for collection in response.data:
                coll_summary = CollectionSummary(
                    id=collection.id,
                    lid=collection.lid,
                    lidvid=collection.lidvid,
                    title=collection.title,
                    ref_lid_instrument=collection.ref_lid_instrument,
                    ref_lid_target=collection.ref_lid_target,
                    ref_lid_instrument_host=collection.ref_lid_instrument_host,
                    ref_lid_investigation=collection.ref_lid_investigation,
                    label_file_info=(
                        collection.label_file_info.model_dump(exclude_none=True) if collection.label_file_info else None
                    ),
                )
                collections.append(coll_summary)

            return PDS4SearchCollectionsOutputSchema(
                total_hits=response.summary.hits,
                query_time_ms=response.summary.took,
                query=response.summary.q,
                limit=params.limit,
                collections=collections,
            )

        except PDS4ClientError as e:
            logger.error(f"PDS4 client error in search_collections: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_collections: {e}")
            raise RuntimeError(f"Internal error during collection search: {e}") from e
