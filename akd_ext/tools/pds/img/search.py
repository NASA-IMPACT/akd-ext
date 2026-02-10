"""IMG Atlas search tool for planetary imagery products."""

import logging
from typing import Annotated

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.img._types import (
    IMGInstrument,
    IMGMission,
    IMGProductType,
    IMGSortField,
    IMGSortOrder,
    IMGTarget,
)
from akd_ext.tools.pds.utils.img_client import IMGAtlasClient, IMGAtlasClientError

logger = logging.getLogger(__name__)


class IMGImageSize(BaseModel):
    """Image dimensions in pixels."""

    lines: int = Field(..., description="Number of lines (height) in pixels")
    samples: int = Field(..., description="Number of samples per line (width) in pixels")


class IMGProductSummary(BaseModel):
    """Product summary in IMG search results."""

    uuid: str | None = Field(None, description="Unique identifier for the product")
    target: str | None = Field(None, description="Target body (e.g., Mars, Saturn, Moon)")
    mission: str | None = Field(None, description="Mission name (e.g., MARS SCIENCE LABORATORY)")
    spacecraft: str | None = Field(None, description="Spacecraft name (e.g., CURIOSITY)")
    instrument: str | None = Field(None, description="Instrument name (e.g., MASTCAM, ISS)")
    product_type: str | None = Field(None, description="Product type (EDR for raw, RDR for processed)")
    start_time: str | None = Field(None, description="Image start time (ISO 8601 format)")
    stop_time: str | None = Field(None, description="Image stop time (ISO 8601 format)")
    sol: int | None = Field(None, description="Mars sol number (Mars missions only)")
    image_size: IMGImageSize | None = Field(None, description="Image dimensions in pixels")
    data_url: str | None = Field(None, description="URL to download the image data file")
    label_url: str | None = Field(None, description="URL to download the PDS label file")
    browse_url: str | None = Field(None, description="URL to browse version of the image")
    thumbnail_url: str | None = Field(None, description="URL to thumbnail version of the image")


class IMGSearchInputSchema(InputSchema):
    """Input schema for IMGSearchTool."""

    target: IMGTarget | None = Field(
        None,
        description=(
            "Target body to filter imagery. "
            "Use img_get_facets with facet_field='TARGET' to discover additional targets."
        ),
    )
    mission: IMGMission | None = Field(
        None,
        description=(
            "Mission name to filter imagery. "
            "Use img_get_facets with facet_field='ATLAS_MISSION_NAME' to discover additional missions."
        ),
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
            "MESSENGER (MDIS). "
            "Use img_get_facets with facet_field='ATLAS_INSTRUMENT_NAME' to discover additional instruments."
        ),
    )
    spacecraft: str | None = Field(
        None,
        description="Spacecraft name filter (e.g., 'CURIOSITY', 'SPIRIT', 'CASSINI ORBITER')",
    )
    start_time: str | None = Field(
        None, description="Start of time range in ISO 8601 format (e.g., '2020-01-01T00:00:00Z')"
    )
    stop_time: str | None = Field(
        None, description="End of time range in ISO 8601 format (e.g., '2020-12-31T23:59:59Z')"
    )
    sol_min: Annotated[int, Field(ge=0)] | None = Field(None, description="Minimum sol number (Mars missions only)")
    sol_max: Annotated[int, Field(ge=0)] | None = Field(None, description="Maximum sol number (Mars missions only)")
    product_type: IMGProductType | None = Field(
        None, description="Product type: 'EDR' for raw data, 'RDR' for processed data"
    )
    filter_name: str | None = Field(
        None, description="Camera filter name (e.g., 'L0', 'R0', 'RED', 'GREEN', 'BLUE')"
    )
    frame_type: str | None = Field(None, description="Frame type filter (e.g., 'FULL', 'SUBFRAME')")
    exposure_min: Annotated[float, Field(ge=0)] | None = Field(
        None, description="Minimum exposure duration in milliseconds"
    )
    exposure_max: Annotated[float, Field(ge=0)] | None = Field(
        None, description="Maximum exposure duration in milliseconds"
    )
    local_solar_time: str | None = Field(
        None, description="Local true solar time filter (e.g., '12:00' for noon images)"
    )
    sort_by: IMGSortField | None = Field(
        None, description="Field to sort results by"
    )
    sort_order: IMGSortOrder = Field("desc", description="Sort direction: 'asc' or 'desc'")
    rows: Annotated[int, Field(ge=1, le=1000)] = Field(100, description="Maximum number of products to return")
    start: Annotated[int, Field(ge=0)] = Field(0, description="Pagination offset (for retrieving additional pages)")


class IMGSearchOutputSchema(OutputSchema):
    """Output schema for IMGSearchTool."""

    status: str = Field(..., description="Status of the request: 'success' or 'error'")
    num_found: int = Field(..., description="Total number of products matching the query")
    start: int = Field(..., description="Pagination offset used in the query")
    query_time_ms: int = Field(..., description="Query execution time in milliseconds")
    products: list[IMGProductSummary] = Field(
        default_factory=list, description="List of imagery products matching the search criteria"
    )
    error: str | None = Field(None, description="Error message if status is 'error'")


class IMGSearchToolConfig(BaseToolConfig):
    """Configuration for IMGSearchTool."""

    base_url: str = Field(
        default="https://pds-imaging.jpl.nasa.gov/solr/pds_archives/",
        description="Base URL for the IMG Atlas API",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")
    retry_delay: float = Field(default=1.0, description="Base delay between retries in seconds")


@mcp_tool
class IMGSearchTool(BaseTool[IMGSearchInputSchema, IMGSearchOutputSchema]):
    """Search for planetary imagery in the PDS Imaging Node Atlas archive.

    The Atlas archive contains 30+ million images from Mars rovers (Spirit, Opportunity,
    Curiosity, Perseverance), Cassini, Voyager, LRO, and MESSENGER missions.

    This tool provides comprehensive search capabilities across multiple missions with filtering
    by target, mission, instrument, time range, sol number, and various image properties.
    """

    input_schema = IMGSearchInputSchema
    output_schema = IMGSearchOutputSchema
    config_schema = IMGSearchToolConfig

    async def _arun(self, params: IMGSearchInputSchema) -> IMGSearchOutputSchema:
        """Execute the IMG search tool."""
        try:
            # Build sort parameter
            sort_param = None
            if params.sort_by:
                order = params.sort_order if params.sort_order in ("asc", "desc") else "desc"
                sort_param = f"{params.sort_by} {order}"

            async with IMGAtlasClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                retry_delay=self.config.retry_delay,
            ) as client:
                response = await client.search_products(
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
                    rows=params.rows,
                    start=params.start,
                    sort=sort_param,
                )

            if response.status == "error":
                return IMGSearchOutputSchema(
                    status="error",
                    num_found=0,
                    start=0,
                    query_time_ms=0,
                    error=response.error,
                )

            # Convert products to summary format
            products = []
            for product in response.products:
                product_summary = IMGProductSummary(
                    uuid=product.uuid,
                    target=product.target,
                    mission=product.mission_name,
                    spacecraft=product.spacecraft_name,
                    instrument=product.instrument_name,
                    product_type=product.product_type,
                    start_time=product.start_time,
                    stop_time=product.stop_time,
                    sol=product.planet_day_number,
                    image_size=(
                        IMGImageSize(lines=product.lines, samples=product.line_samples)
                        if product.lines is not None and product.line_samples is not None
                        else None
                    ),
                    data_url=product.data_url,
                    label_url=product.label_url,
                    browse_url=product.browse_url,
                    thumbnail_url=product.thumbnail_url,
                )
                products.append(product_summary)

            return IMGSearchOutputSchema(
                status="success",
                num_found=response.num_found,
                start=response.start,
                query_time_ms=response.query_time_ms,
                products=products,
            )

        except IMGAtlasClientError as e:
            logger.error(f"IMG Atlas client error in IMGSearchTool: {e}")
            return IMGSearchOutputSchema(
                status="error",
                num_found=0,
                start=0,
                query_time_ms=0,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error in IMGSearchTool: {e}")
            return IMGSearchOutputSchema(
                status="error",
                num_found=0,
                start=0,
                query_time_ms=0,
                error=f"Internal error: {e}",
            )
