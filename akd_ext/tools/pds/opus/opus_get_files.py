"""OPUS Get Files Tool - Get downloadable file URLs for observations."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.opus_client import OPUSClient, OPUSClientError


class OPUSBrowseImages(BaseModel):
    """Browse image URLs for an observation."""

    thumbnail: str | None = None
    small: str | None = None
    medium: str | None = None
    full: str | None = None


class OPUSGetFilesInputSchema(InputSchema):
    """Input schema for OPUSGetFilesTool."""

    opusid: str = Field(
        ...,
        description='OPUS observation ID (e.g., "co-iss-n1460960653")',
    )


class OPUSGetFilesOutputSchema(OutputSchema):
    """Output schema for OPUSGetFilesTool."""

    status: str = Field(..., description="Status of the file retrieval")
    opusid: str = Field(..., description="OPUS observation ID")
    raw_files: list[str] | None = Field(
        None,
        description="URLs for raw data files",
    )
    calibrated_files: list[str] | None = Field(
        None,
        description="URLs for calibrated data files",
    )
    browse_images: OPUSBrowseImages | None = Field(
        None,
        description="Browse image URLs at various resolutions",
    )
    all_file_categories: dict[str, list[str]] | None = Field(
        None,
        description="All files organized by category",
    )


class OPUSGetFilesToolConfig(BaseToolConfig):
    """Configuration for OPUSGetFilesTool."""

    base_url: str = Field(
        default=os.getenv("OPUS_BASE_URL", "https://opus.pds-rings.seti.org/opus/api/"),
        description="OPUS API base URL (override with OPUS_BASE_URL env var)",
    )
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
    )


@mcp_tool
class OPUSGetFilesTool(BaseTool[OPUSGetFilesInputSchema, OPUSGetFilesOutputSchema]):
    """Get downloadable file URLs for an observation.

    Returns URLs for:
    - Raw data files (original instrument data)
    - Calibrated data files (processed/calibrated versions)
    - Browse images at various resolutions (thumbnail, small, medium, full)
    """

    input_schema = OPUSGetFilesInputSchema
    output_schema = OPUSGetFilesOutputSchema
    config_schema = OPUSGetFilesToolConfig

    async def _arun(self, params: OPUSGetFilesInputSchema) -> OPUSGetFilesOutputSchema:
        """Execute the file retrieval."""
        try:
            async with OPUSClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.get_files(params.opusid)

            if response.status == "error":
                logger.error(f"OPUS files error: {response.error}")
                return OPUSGetFilesOutputSchema(
                    status="error",
                    opusid=params.opusid,
                )

            if not response.files:
                logger.warning(f"Files not found for observation: {params.opusid}")
                return OPUSGetFilesOutputSchema(
                    status="not_found",
                    opusid=params.opusid,
                )

            files = response.files
            browse = None
            if any([files.browse_thumb, files.browse_small, files.browse_medium, files.browse_full]):
                browse = OPUSBrowseImages(
                    thumbnail=files.browse_thumb,
                    small=files.browse_small,
                    medium=files.browse_medium,
                    full=files.browse_full,
                )

            return OPUSGetFilesOutputSchema(
                status="success",
                opusid=files.opusid,
                raw_files=files.raw_files if files.raw_files else None,
                calibrated_files=files.calibrated_files if files.calibrated_files else None,
                browse_images=browse,
                all_file_categories=files.all_files if files.all_files else None,
            )

        except OPUSClientError as e:
            logger.error(f"OPUS client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OPUS get files: {e}")
            raise RuntimeError(f"Internal error: {e}") from e
