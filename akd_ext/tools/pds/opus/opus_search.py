"""OPUS Search Tool - Search outer planets observations."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.opus.types import OPUS_INSTRUMENTS, OPUS_MISSIONS, OPUS_PLANETS
from akd_ext.tools.pds.utils.opus_client import OPUSClient, OPUSClientError


class OPUSObservationSummary(BaseModel):
    """Observation item in search results."""

    opusid: str
    instrument: str | None = None
    target: str | None = None
    mission: str | None = None
    planet: str | None = None
    time_start: str | None = None
    time_end: str | None = None
    duration_seconds: float | None = None


class OPUSSearchInputSchema(InputSchema):
    """Input schema for OPUSSearchTool.

    Valid planets: Jupiter, Saturn, Uranus, Neptune, Pluto, Other
    Valid missions: Cassini, Voyager 1, Voyager 2, Galileo, New Horizons, Juno, Hubble
    Valid instruments (use full name with mission prefix):
      - Cassini ISS, Cassini VIMS, Cassini UVIS, Cassini CIRS, Cassini RSS
      - Voyager ISS, Voyager IRIS
      - Galileo SSI
      - New Horizons LORRI, New Horizons MVIC
      - Juno JunoCam, Juno JIRAM
      - Hubble WFPC2, Hubble WFC3, Hubble ACS, Hubble STIS, Hubble NICMOS
    """

    target: str | None = Field(
        None,
        description='Target body (e.g., "Saturn", "Titan", "Saturn Rings", "Io")',
    )
    mission: OPUS_MISSIONS | None = Field(
        None,
        description="Mission name filter",
    )
    instrument: OPUS_INSTRUMENTS | None = Field(
        None,
        description='Instrument name filter (e.g., "Cassini ISS", "Cassini VIMS")',
    )
    planet: OPUS_PLANETS | None = Field(
        None,
        description="Planet system filter",
    )
    time_min: str | None = Field(
        None,
        description='Start of time range (ISO 8601 format, e.g., "2004-01-01")',
    )
    time_max: str | None = Field(
        None,
        description="End of time range (ISO 8601 format)",
    )
    limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum observations to return",
    )
    startobs: int = Field(
        1,
        ge=1,
        description="Starting observation index for pagination",
    )


class OPUSSearchOutputSchema(OutputSchema):
    """Output schema for OPUSSearchTool."""

    status: str = Field(..., description="Status of the search (success/error)")
    available: int = Field(..., description="Total observations available matching criteria")
    start_obs: int = Field(..., description="Starting observation index")
    limit: int = Field(..., description="Maximum observations returned")
    count: int = Field(..., description="Number of observations in this response")
    observations: list[OPUSObservationSummary] = Field(
        default_factory=list,
        description="List of observations with basic metadata",
    )


class OPUSSearchToolConfig(BaseToolConfig):
    """Configuration for OPUSSearchTool."""

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
class OPUSSearchTool(BaseTool[OPUSSearchInputSchema, OPUSSearchOutputSchema]):
    """Search for outer planets observations in the OPUS database.

    OPUS contains 400,000+ observations from Cassini, Voyager, Galileo,
    New Horizons, Juno, and Hubble Space Telescope missions covering outer
    planets (Jupiter, Saturn, Uranus, Neptune, Pluto).
    """

    input_schema = OPUSSearchInputSchema
    output_schema = OPUSSearchOutputSchema
    config_schema = OPUSSearchToolConfig

    async def _arun(self, params: OPUSSearchInputSchema) -> OPUSSearchOutputSchema:
        """Execute the search."""
        try:
            async with OPUSClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.search_observations(
                    target=params.target,
                    mission=params.mission,
                    instrument=params.instrument,
                    planet=params.planet,
                    time_min=params.time_min,
                    time_max=params.time_max,
                    limit=params.limit,
                    startobs=params.startobs,
                )

            if response.status == "error":
                logger.error(f"OPUS search error: {response.error}")
                return OPUSSearchOutputSchema(
                    status="error",
                    available=0,
                    start_obs=params.startobs,
                    limit=params.limit,
                    count=0,
                    observations=[],
                )

            observations = [
                OPUSObservationSummary(
                    opusid=obs.opusid,
                    instrument=obs.instrument,
                    target=obs.target,
                    mission=obs.mission,
                    planet=obs.planet,
                    time_start=obs.time1,
                    time_end=obs.time2,
                    duration_seconds=obs.observation_duration,
                )
                for obs in response.observations
            ]

            return OPUSSearchOutputSchema(
                status="success",
                available=response.available,
                start_obs=response.start_obs,
                limit=response.limit,
                count=response.count,
                observations=observations,
            )

        except OPUSClientError as e:
            logger.error(f"OPUS client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OPUS search: {e}")
            raise RuntimeError(f"Internal error: {e}") from e
