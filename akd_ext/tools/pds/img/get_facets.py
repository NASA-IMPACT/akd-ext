"""IMG Atlas get facets tool for discovering available field values."""

import logging
from typing import Annotated

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.img._types import IMGFacetField, IMGInstrument, IMGMission, IMGTarget
from akd_ext.tools.pds.utils.img_client import IMGAtlasClient, IMGAtlasClientError

logger = logging.getLogger(__name__)


class IMGFacetValueItem(BaseModel):
    """A single facet value with its count."""

    value: str = Field(..., description="The facet value (e.g., 'Mars', 'MASTCAM')")
    count: int = Field(..., description="Number of products with this value")


class IMGGetFacetsInputSchema(InputSchema):
    """Input schema for IMGGetFacetsTool."""

    facet_field: IMGFacetField = Field(
        ...,
        description=(
            "Field to get values for. Valid fields:\n"
            "- 'TARGET': Planetary targets (Mars, Saturn, Moon, Titan, etc.)\n"
            "- 'ATLAS_MISSION_NAME': Mission names (MSL, Cassini, Voyager, etc.)\n"
            "- 'ATLAS_INSTRUMENT_NAME': Instruments (MASTCAM, ISS, LROC, etc.)\n"
            "- 'ATLAS_SPACECRAFT_NAME': Spacecraft names\n"
            "- 'PRODUCT_TYPE': Product types (EDR, RDR, etc.)\n"
            "- 'FRAME_TYPE': Frame types (FULL, SUBFRAME, etc.)\n"
            "- 'FILTER_NAME': Camera filter names\n"
            "- 'pds_standard': PDS version (PDS3, PDS4)"
        ),
    )
    limit: Annotated[int, Field(ge=1, le=1000)] = Field(
        100, description="Maximum number of values to return"
    )
    target: IMGTarget | None = Field(
        None, description="Optional target filter to narrow results"
    )
    mission: IMGMission | None = Field(
        None, description="Optional mission filter to narrow results"
    )
    instrument: IMGInstrument | None = Field(
        None, description="Optional instrument filter to narrow results"
    )


class IMGGetFacetsOutputSchema(OutputSchema):
    """Output schema for IMGGetFacetsTool."""

    status: str = Field(..., description="Status of the request: 'success' or 'error'")
    facet_field: str = Field(..., description="The facet field that was queried")
    query_time_ms: int = Field(..., description="Query execution time in milliseconds")
    count: int = Field(..., description="Number of unique values returned")
    values: list[IMGFacetValueItem] = Field(
        default_factory=list, description="List of facet values with counts, sorted by count descending"
    )
    error: str | None = Field(None, description="Error message if status is 'error'")


class IMGGetFacetsToolConfig(BaseToolConfig):
    """Configuration for IMGGetFacetsTool."""

    base_url: str = Field(
        default="https://pds-imaging.jpl.nasa.gov/solr/pds_archives/",
        description="Base URL for the IMG Atlas API",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")
    retry_delay: float = Field(default=1.0, description="Base delay between retries in seconds")


@mcp_tool
class IMGGetFacetsTool(BaseTool[IMGGetFacetsInputSchema, IMGGetFacetsOutputSchema]):
    """Get available values and counts for a field in the IMG Atlas archive.

    Use this tool to dynamically discover available targets, missions, instruments,
    product types, and other field values. This is more accurate than static lists
    as it queries the actual archive and returns current data with counts.

    The results are sorted by count in descending order, showing the most common
    values first.

    Examples:
        Discover all available targets:
            facet_field="TARGET"

        Discover all missions:
            facet_field="ATLAS_MISSION_NAME"

        Discover all instruments:
            facet_field="ATLAS_INSTRUMENT_NAME"

        Discover instruments for Mars missions only:
            facet_field="ATLAS_INSTRUMENT_NAME", target="Mars"

        Discover product types available for Cassini:
            facet_field="PRODUCT_TYPE", mission="CASSINI-HUYGENS"

        Discover available filter names for MASTCAM:
            facet_field="FILTER_NAME", instrument="MASTCAM"
    """

    input_schema = IMGGetFacetsInputSchema
    output_schema = IMGGetFacetsOutputSchema
    config_schema = IMGGetFacetsToolConfig

    async def _arun(self, params: IMGGetFacetsInputSchema) -> IMGGetFacetsOutputSchema:
        """Execute the IMG get facets tool."""
        try:
            async with IMGAtlasClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                retry_delay=self.config.retry_delay,
            ) as client:
                response = await client.get_facets(
                    facet_field=params.facet_field,
                    limit=params.limit,
                    target=params.target,
                    mission=params.mission,
                    instrument=params.instrument,
                )

            if response.status == "error":
                return IMGGetFacetsOutputSchema(
                    status="error",
                    facet_field=params.facet_field,
                    query_time_ms=0,
                    count=0,
                    error=response.error,
                )

            # Convert to output schema format
            values = [
                IMGFacetValueItem(value=v.value, count=v.count)
                for v in response.values
            ]

            return IMGGetFacetsOutputSchema(
                status="success",
                facet_field=response.facet_field,
                query_time_ms=response.query_time_ms,
                count=len(values),
                values=values,
            )

        except IMGAtlasClientError as e:
            logger.error(f"IMG Atlas client error in IMGGetFacetsTool: {e}")
            return IMGGetFacetsOutputSchema(
                status="error",
                facet_field=params.facet_field,
                query_time_ms=0,
                count=0,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error in IMGGetFacetsTool: {e}")
            return IMGGetFacetsOutputSchema(
                status="error",
                facet_field=params.facet_field,
                query_time_ms=0,
                count=0,
                error=f"Internal error: {e}",
            )
