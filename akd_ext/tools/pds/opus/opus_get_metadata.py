"""OPUS Get Metadata Tool - Get detailed metadata for observations."""

import logging
from typing import Any

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.opus_client import OPUSClient, OPUSClientError

logger = logging.getLogger(__name__)


class OPUSGetMetadataInputSchema(InputSchema):
    """Input schema for OPUSGetMetadataTool."""

    opusid: str = Field(
        ...,
        description='OPUS observation ID (e.g., "co-iss-n1460960653")',
    )


class OPUSGetMetadataOutputSchema(OutputSchema):
    """Output schema for OPUSGetMetadataTool."""

    status: str = Field(..., description="Status of the metadata retrieval")
    opusid: str = Field(..., description="OPUS observation ID")
    general: dict[str, Any] | None = Field(
        None,
        description="General constraints (target, mission, instrument, time)",
    )
    pds: dict[str, Any] | None = Field(
        None,
        description="PDS constraints (bundle ID, dataset ID, product ID)",
    )
    image: dict[str, Any] | None = Field(
        None,
        description="Image constraints (dimensions, levels, image type)",
    )
    wavelength: dict[str, Any] | None = Field(
        None,
        description="Wavelength constraints (wavelength range, wavenumber range)",
    )
    ring_geometry: dict[str, Any] | None = Field(
        None,
        description="Ring geometry constraints (ring radius, opening angles)",
    )
    surface_geometry: dict[str, Any] | None = Field(
        None,
        description="Surface geometry constraints",
    )
    instrument_specific: dict[str, Any] | None = Field(
        None,
        description="Instrument-specific constraints",
    )


class OPUSGetMetadataToolConfig(BaseToolConfig):
    """Configuration for OPUSGetMetadataTool."""

    base_url: str = Field(
        default="https://opus.pds-rings.seti.org/opus/api/",
        description="OPUS API base URL",
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
class OPUSGetMetadataTool(BaseTool[OPUSGetMetadataInputSchema, OPUSGetMetadataOutputSchema]):
    """Get detailed metadata for a specific observation.

    Returns comprehensive metadata organized by category including:
    - General constraints (target, mission, instrument, time)
    - PDS constraints (bundle ID, dataset ID, product ID)
    - Image constraints (dimensions, levels, image type)
    - Wavelength constraints (wavelength range, wavenumber range)
    - Ring geometry constraints (ring radius, opening angles)
    - Surface geometry constraints
    - Instrument-specific constraints
    """

    input_schema = OPUSGetMetadataInputSchema
    output_schema = OPUSGetMetadataOutputSchema
    config_schema = OPUSGetMetadataToolConfig

    async def _arun(self, params: OPUSGetMetadataInputSchema) -> OPUSGetMetadataOutputSchema:
        """Execute the metadata retrieval."""
        try:
            async with OPUSClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.get_metadata(params.opusid)

            if response.status == "error":
                logger.error(f"OPUS metadata error: {response.error}")
                return OPUSGetMetadataOutputSchema(
                    status="error",
                    opusid=params.opusid,
                )

            if not response.metadata:
                logger.warning(f"Metadata not found for observation: {params.opusid}")
                return OPUSGetMetadataOutputSchema(
                    status="not_found",
                    opusid=params.opusid,
                )

            metadata = response.metadata
            return OPUSGetMetadataOutputSchema(
                status="success",
                opusid=metadata.opusid,
                general=metadata.general_constraints if metadata.general_constraints else None,
                pds=metadata.pds_constraints if metadata.pds_constraints else None,
                image=metadata.image_constraints if metadata.image_constraints else None,
                wavelength=metadata.wavelength_constraints if metadata.wavelength_constraints else None,
                ring_geometry=metadata.ring_geometry_constraints if metadata.ring_geometry_constraints else None,
                surface_geometry=metadata.surface_geometry_constraints if metadata.surface_geometry_constraints else None,
                instrument_specific=metadata.instrument_constraints if metadata.instrument_constraints else None,
            )

        except OPUSClientError as e:
            logger.error(f"OPUS client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OPUS get metadata: {e}")
            raise RuntimeError(f"Internal error: {e}") from e
