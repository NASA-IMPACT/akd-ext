"""IMG Atlas count tool for counting imagery products."""

import os

from loguru import logger
from typing import Any

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.img.types import IMGInstrument, IMGMission, IMGProductType, IMGTarget
from akd_ext.tools.pds.utils.img_client import IMGAtlasClient, IMGAtlasClientError


class IMGCountInputSchema(InputSchema):
    """Input schema for IMGCountTool."""

    target: IMGTarget | None = Field(
        None,
        description="Target body to filter imagery",
    )
    mission: IMGMission | None = Field(
        None,
        description="Mission name to filter imagery",
    )
    instrument: IMGInstrument | None = Field(
        None,
        description=(
            "Instrument name to filter imagery. Common by mission: "
            "MER (HAZCAM, NAVCAM, PANCAM, MI), "
            "MSL (HAZCAM, NAVCAM, MASTCAM, MAHLI, MARDI, CHEMCAM), "
            "Mars2020 (HAZCAM, NAVCAM, MASTCAM-Z, SHERLOC, PIXL), "
            "Cassini (ISS, VIMS), "
            "Voyager (ISS), "
            "LRO (LROC), "
            "MESSENGER (MDIS)"
        ),
    )
    spacecraft: str | None = Field(
        None,
        description="Spacecraft name filter (e.g., 'CURIOSITY', 'SPIRIT')",
    )
    start_time: str | None = Field(
        None, description="Start of time range in ISO 8601 format (e.g., '2020-01-01T00:00:00Z')"
    )
    stop_time: str | None = Field(
        None, description="End of time range in ISO 8601 format (e.g., '2020-12-31T23:59:59Z')"
    )
    sol_min: int | None = Field(None, ge=0, description="Minimum sol number (Mars missions only)")
    sol_max: int | None = Field(None, ge=0, description="Maximum sol number (Mars missions only)")
    product_type: IMGProductType | None = Field(
        None, description="Product type: 'EDR' for raw data, 'RDR' for processed data"
    )
    filter_name: str | None = Field(None, description="Camera filter name (e.g., 'L0', 'R0', 'RED', 'GREEN', 'BLUE')")
    frame_type: str | None = Field(None, description="Frame type filter (e.g., 'FULL', 'SUBFRAME')")
    exposure_min: float | None = Field(None, ge=0, description="Minimum exposure duration in milliseconds")
    exposure_max: float | None = Field(None, ge=0, description="Maximum exposure duration in milliseconds")
    local_solar_time: str | None = Field(
        None, description="Local true solar time filter (e.g., '12:00' for noon images)"
    )


class IMGCountOutputSchema(OutputSchema):
    """Output schema for IMGCountTool."""

    status: str = Field(..., description="Status of the request: 'success' or 'error'")
    count: int = Field(..., description="Total number of products matching the criteria")
    query_time_ms: int = Field(..., description="Query execution time in milliseconds")
    filters: dict[str, Any] = Field(default_factory=dict, description="Applied filters echoed back for reference")
    error: str | None = Field(None, description="Error message if status is 'error'")


class IMGCountToolConfig(BaseToolConfig):
    """Configuration for IMGCountTool."""

    base_url: str = Field(
        default=os.getenv("IMG_BASE_URL", "https://pds-imaging.jpl.nasa.gov/solr/pds_archives/"),
        description="IMG Atlas API base URL (override with IMG_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")
    retry_delay: float = Field(default=1.0, description="Base delay between retries in seconds")


@mcp_tool
class IMGCountTool(BaseTool[IMGCountInputSchema, IMGCountOutputSchema]):
    """Count imagery products matching criteria without retrieving them.

    This tool is useful for understanding data availability before running full searches.
    It efficiently returns just the count of matching products without fetching metadata,
    which is faster than a full search when you only need to know how many results exist.

    Examples:
        Count all Mars images from Curiosity:
            target="Mars", mission="MARS SCIENCE LABORATORY"

        Count images from a specific sol range:
            target="Mars", sol_min=100, sol_max=200

        Count images from a specific time range:
            start_time="2020-01-01T00:00:00Z", stop_time="2020-12-31T23:59:59Z"

        Count only raw (EDR) images:
            target="Mars", product_type="EDR"
    """

    input_schema = IMGCountInputSchema
    output_schema = IMGCountOutputSchema
    config_schema = IMGCountToolConfig

    async def _arun(self, params: IMGCountInputSchema) -> IMGCountOutputSchema:
        """Execute the IMG count tool."""
        try:
            async with IMGAtlasClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                retry_delay=self.config.retry_delay,
            ) as client:
                response = await client.count_products(
                    target=params.target,
                    mission=params.mission,
                    instrument=params.instrument,
                    spacecraft=params.spacecraft,
                    start_time=params.start_time,
                    stop_time=params.stop_time,
                    sol_min=params.sol_min,
                    sol_max=params.sol_max,
                    product_type=params.product_type,
                    filter_name=params.filter_name,
                    frame_type=params.frame_type,
                    exposure_min=params.exposure_min,
                    exposure_max=params.exposure_max,
                    local_solar_time=params.local_solar_time,
                )

            if response.status == "error":
                return IMGCountOutputSchema(
                    status="error",
                    count=0,
                    query_time_ms=0,
                    error=response.error,
                )

            # Build filters dictionary for reference
            filters = {
                "target": params.target,
                "mission": params.mission,
                "instrument": params.instrument,
                "spacecraft": params.spacecraft,
                "start_time": params.start_time,
                "stop_time": params.stop_time,
                "sol_min": params.sol_min,
                "sol_max": params.sol_max,
                "product_type": params.product_type,
                "filter_name": params.filter_name,
                "frame_type": params.frame_type,
                "exposure_min": params.exposure_min,
                "exposure_max": params.exposure_max,
                "local_solar_time": params.local_solar_time,
            }

            return IMGCountOutputSchema(
                status="success",
                count=response.count,
                query_time_ms=response.query_time_ms,
                filters=filters,
            )

        except IMGAtlasClientError as e:
            logger.error(f"IMG Atlas client error in IMGCountTool: {e}")
            return IMGCountOutputSchema(
                status="error",
                count=0,
                query_time_ms=0,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error in IMGCountTool: {e}")
            return IMGCountOutputSchema(
                status="error",
                count=0,
                query_time_ms=0,
                error=f"Internal error: {e}",
            )
