"""OPUS Count Tool - Count observations matching criteria."""

import logging
from typing import Any

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.opus.types import OPUS_INSTRUMENTS, OPUS_MISSIONS, OPUS_PLANETS
from akd_ext.tools.pds.utils.opus_client import OPUSClient, OPUSClientError

logger = logging.getLogger(__name__)


class OPUSCountInputSchema(InputSchema):
    """Input schema for OPUSCountTool.

    Valid planets: Jupiter, Saturn, Uranus, Neptune, Pluto, Other
    Valid missions: Cassini, Voyager 1, Voyager 2, Galileo, New Horizons, Juno, Hubble
    Valid instruments by mission:
      - Cassini: ISS, VIMS, UVIS, CIRS, RSS
      - Voyager: ISS, IRIS
      - Galileo: SSI
      - New Horizons: LORRI, MVIC
      - Juno: JunoCam, JIRAM
      - Hubble: WFPC2, WFC3, ACS, STIS, NICMOS
    """

    target: str | None = Field(
        None,
        description='Target body filter (e.g., "Saturn", "Titan")',
    )
    mission: OPUS_MISSIONS | None = Field(
        None,
        description='Mission name filter (e.g., "Cassini")',
    )
    instrument: OPUS_INSTRUMENTS | None = Field(
        None,
        description='Instrument name filter (e.g., "Cassini ISS", "Cassini VIMS")',
    )
    planet: OPUS_PLANETS | None = Field(
        None,
        description='Planet system filter (e.g., "Saturn")',
    )
    time_min: str | None = Field(
        None,
        description="Start of time range (ISO 8601 format)",
    )
    time_max: str | None = Field(
        None,
        description="End of time range (ISO 8601 format)",
    )


class OPUSCountOutputSchema(OutputSchema):
    """Output schema for OPUSCountTool."""

    status: str = Field(..., description="Status of the count operation (success/error)")
    count: int = Field(..., description="Number of observations matching the criteria")
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Applied filters for reference",
    )


class OPUSCountToolConfig(BaseToolConfig):
    """Configuration for OPUSCountTool."""

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
class OPUSCountTool(BaseTool[OPUSCountInputSchema, OPUSCountOutputSchema]):
    """Count observations matching criteria without retrieving them.

    This is useful for understanding data availability before running full searches.
    It's much faster than a full search and doesn't consume as much bandwidth.
    """

    input_schema = OPUSCountInputSchema
    output_schema = OPUSCountOutputSchema
    config_schema = OPUSCountToolConfig

    async def _arun(self, params: OPUSCountInputSchema) -> OPUSCountOutputSchema:
        """Execute the count."""
        try:
            async with OPUSClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.count_observations(
                    target=params.target,
                    mission=params.mission,
                    instrument=params.instrument,
                    planet=params.planet,
                    time_min=params.time_min,
                    time_max=params.time_max,
                )

            if response.status == "error":
                logger.error(f"OPUS count error: {response.error}")
                return OPUSCountOutputSchema(
                    status="error",
                    count=0,
                    filters={},
                )

            return OPUSCountOutputSchema(
                status="success",
                count=response.count,
                filters={
                    "target": params.target,
                    "mission": params.mission,
                    "instrument": params.instrument,
                    "planet": params.planet,
                    "time_min": params.time_min,
                    "time_max": params.time_max,
                },
            )

        except OPUSClientError as e:
            logger.error(f"OPUS client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OPUS count: {e}")
            raise RuntimeError(f"Internal error: {e}") from e
