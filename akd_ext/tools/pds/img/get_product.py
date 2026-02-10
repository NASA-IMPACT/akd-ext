"""IMG Atlas get product tool for retrieving detailed product metadata."""

import logging

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.img_client import IMGAtlasClient, IMGAtlasClientError

logger = logging.getLogger(__name__)


class IMGProductDetailURLs(BaseModel):
    """URL container for IMG product detail."""

    data: str | None = Field(None, description="URL to download the image data file")
    label: str | None = Field(None, description="URL to download the PDS label file")
    browse: str | None = Field(None, description="URL to browse version of the image")
    thumbnail: str | None = Field(None, description="URL to thumbnail version of the image")


class IMGGetProductInputSchema(InputSchema):
    """Input schema for IMGGetProductTool."""

    product_id: str = Field(..., description="Product identifier (uuid or PRODUCT_ID)")


class IMGGetProductOutputSchema(OutputSchema):
    """Output schema for IMGGetProductTool."""

    status: str = Field(..., description="Status of the request: 'success', 'not_found', or 'error'")
    uuid: str | None = Field(None, description="Unique identifier for the product")
    product_id: str | None = Field(None, description="PDS product ID")
    pds_standard: str | None = Field(None, description="PDS standard version (PDS3 or PDS4)")
    target: str | None = Field(None, description="Target body (e.g., Mars, Saturn, Moon)")
    product_type: str | None = Field(None, description="Product type (EDR, RDR)")
    mission: str | None = Field(None, description="Mission name")
    spacecraft: str | None = Field(None, description="Spacecraft name")
    instrument: str | None = Field(None, description="Instrument name")
    start_time: str | None = Field(None, description="Image start time (ISO 8601)")
    stop_time: str | None = Field(None, description="Image stop time (ISO 8601)")
    product_creation_time: str | None = Field(None, description="Product creation time (ISO 8601)")
    sol: int | None = Field(None, description="Mars sol number (Mars missions only)")
    local_solar_time: str | None = Field(None, description="Local true solar time")
    solar_azimuth: float | None = Field(None, description="Solar azimuth angle in degrees")
    solar_elevation: float | None = Field(None, description="Solar elevation angle in degrees")
    lines: int | None = Field(None, description="Number of lines (height) in pixels")
    line_samples: int | None = Field(None, description="Number of samples per line (width) in pixels")
    exposure_duration_ms: float | None = Field(None, description="Exposure duration in milliseconds")
    compression_ratio: float | None = Field(None, description="Compression ratio")
    frame_type: str | None = Field(None, description="Frame type (FULL, SUBFRAME)")
    center_latitude: float | None = Field(None, description="Center latitude in degrees")
    center_longitude: float | None = Field(None, description="Center longitude in degrees")
    urls: IMGProductDetailURLs | None = Field(None, description="URLs for data, label, browse, and thumbnail")
    error: str | None = Field(None, description="Error message if status is 'error'")
    message: str | None = Field(None, description="Additional message (e.g., not found reason)")


class IMGGetProductToolConfig(BaseToolConfig):
    """Configuration for IMGGetProductTool."""

    base_url: str = Field(
        default="https://pds-imaging.jpl.nasa.gov/solr/pds_archives/",
        description="Base URL for the IMG Atlas API",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")
    retry_delay: float = Field(default=1.0, description="Base delay between retries in seconds")


@mcp_tool
class IMGGetProductTool(BaseTool[IMGGetProductInputSchema, IMGGetProductOutputSchema]):
    """Get detailed metadata for a specific imagery product.

    This tool retrieves comprehensive metadata for a single product identified by its
    uuid or PRODUCT_ID. Use this when you need full details about a specific image
    that you found through a search.

    Examples:
        Get product by uuid:
            product_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

        Get product by PRODUCT_ID:
            product_id="2N123456789EFFAM00P1234L0M1"
    """

    input_schema = IMGGetProductInputSchema
    output_schema = IMGGetProductOutputSchema
    config_schema = IMGGetProductToolConfig

    async def _arun(self, params: IMGGetProductInputSchema) -> IMGGetProductOutputSchema:
        """Execute the IMG get product tool."""
        try:
            async with IMGAtlasClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                retry_delay=self.config.retry_delay,
            ) as client:
                response = await client.get_product(params.product_id)

            if response.status == "error":
                return IMGGetProductOutputSchema(
                    status="error",
                    error=response.error,
                )

            if not response.products:
                return IMGGetProductOutputSchema(
                    status="not_found",
                    message=f"Product '{params.product_id}' not found",
                )

            product = response.products[0]

            urls = IMGProductDetailURLs(
                data=product.data_url,
                label=product.label_url,
                browse=product.browse_url,
                thumbnail=product.thumbnail_url,
            )

            return IMGGetProductOutputSchema(
                status="success",
                uuid=product.uuid,
                product_id=product.product_id,
                pds_standard=product.pds_standard,
                target=product.target,
                product_type=product.product_type,
                mission=product.mission_name,
                spacecraft=product.spacecraft_name,
                instrument=product.instrument_name,
                start_time=product.start_time,
                stop_time=product.stop_time,
                product_creation_time=product.product_creation_time,
                sol=product.planet_day_number,
                local_solar_time=product.local_true_solar_time,
                solar_azimuth=product.solar_azimuth,
                solar_elevation=product.solar_elevation,
                lines=product.lines,
                line_samples=product.line_samples,
                exposure_duration_ms=product.exposure_duration,
                compression_ratio=product.compression_ratio,
                frame_type=product.frame_type,
                center_latitude=product.center_latitude,
                center_longitude=product.center_longitude,
                urls=urls,
            )

        except IMGAtlasClientError as e:
            logger.error(f"IMG Atlas client error in IMGGetProductTool: {e}")
            return IMGGetProductOutputSchema(
                status="error",
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error in IMGGetProductTool: {e}")
            return IMGGetProductOutputSchema(
                status="error",
                error=f"Internal error: {e}",
            )
