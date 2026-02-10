"""Search for observations at fixed sky coordinates."""

import logging
from typing import Annotated, Any, Literal

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.sbn.types import (
    DEFAULT_OBSERVATIONS_LIMIT,
    FIELD_PROFILES,
    MAX_OBSERVATIONS_LIMIT,
    SUMMARY_FIELDS,
    VALID_SOURCES_DESCRIPTION,
    filter_observation,
)
from akd_ext.tools.pds.utils.sbn_client import SBNCatchClient, SBNCatchClientError

logger = logging.getLogger(__name__)


class SBNSearchCoordinatesInputSchema(InputSchema):
    """Input schema for SBNSearchCoordinatesTool."""

    ra: str = Field(
        ...,
        description="Right ascension. Formats: Sexagesimal '12:34:56.7' (hours) or decimal degrees '123.45'",
    )
    dec: str = Field(
        ...,
        description="Declination. Formats: Sexagesimal '+12:34:56.7' or '-12:34:56.7', or decimal degrees '-30.5'",
    )
    radius: Annotated[float, Field(gt=0, le=120)] = Field(
        10.0, description="Search radius in arcminutes (0-120, default 10)"
    )
    sources: list[str] | None = Field(None, description=VALID_SOURCES_DESCRIPTION)
    start_date: str | None = Field(None, description="Start date filter (format: 'YYYY-MM-DD')")
    stop_date: str | None = Field(None, description="Stop date filter (format: 'YYYY-MM-DD')")
    limit: Annotated[int, Field(ge=1, le=10)] = Field(
        DEFAULT_OBSERVATIONS_LIMIT, description="Maximum observations to return (default 10, max 10)"
    )
    offset: Annotated[int, Field(ge=0)] = Field(0, description="Skip first N observations for pagination (default 0)")
    fields: Literal["essential", "summary", "full"] = Field(
        "summary", description="Field profile: 'essential' (minimal), 'summary' (default), or 'full' (all fields)"
    )


class SBNSearchCoordinatesOutputSchema(OutputSchema):
    """Output schema for SBNSearchCoordinatesTool."""

    ra: str = Field(..., description="Right ascension that was searched")
    dec: str = Field(..., description="Declination that was searched")
    radius: float = Field(..., description="Search radius in arcminutes")
    count: int = Field(..., description="Number of observations returned in this response")
    total_available: int = Field(..., description="Total number of observations available")
    offset: int = Field(..., description="Offset used for pagination")
    limit: int = Field(..., description="Limit applied to this response")
    has_more: bool = Field(..., description="Whether more results are available beyond this response")
    fields: str = Field(..., description="Field profile used for filtering")
    observations: list[dict[str, Any]] = Field(
        default_factory=list, description="List of observations with filtered fields"
    )


class SBNSearchCoordinatesToolConfig(BaseToolConfig):
    """Configuration for SBNSearchCoordinatesTool."""

    base_url: str = Field(
        default="https://catch-api.astro.umd.edu/",
        description="CATCH API base URL (can be overridden with SBN_BASE_URL env var)",
    )
    timeout: float = Field(default=60.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class SBNSearchCoordinatesTool(BaseTool[SBNSearchCoordinatesInputSchema, SBNSearchCoordinatesOutputSchema]):
    """Search for observations at fixed sky coordinates.

    This tool searches survey data for observations covering a specific position
    in the sky. This is useful for finding serendipitous observations of objects
    at known coordinates, or for checking if a particular sky region has been
    observed by any surveys.

    Coordinate Formats:
    - Right Ascension (RA):
      - Sexagesimal: "12:34:56.7" (hours:minutes:seconds)
      - Decimal degrees: "123.45"
    - Declination (Dec):
      - Sexagesimal: "+12:34:56.7" or "-12:34:56.7" (degrees:arcmin:arcsec)
      - Decimal degrees: "-30.5" or "45.2"

    Search Radius:
    - Specified in arcminutes (0-120)
    - Default: 10 arcminutes
    - Larger radii may return more results but take longer

    Field Profiles:
    - essential: product_id, source, date, archive_url (minimal metadata)
    - summary: essential + ra, dec, vmag, filter, exposure (most useful fields)
    - full: all available fields including ephemeris, photometry, observing conditions

    Unlike moving target searches, fixed coordinate searches return results
    immediately without requiring job polling.

    """

    input_schema = SBNSearchCoordinatesInputSchema
    output_schema = SBNSearchCoordinatesOutputSchema
    config_schema = SBNSearchCoordinatesToolConfig

    async def _arun(self, params: SBNSearchCoordinatesInputSchema) -> SBNSearchCoordinatesOutputSchema:
        """Execute the tool to search for observations at fixed coordinates."""
        try:
            async with SBNCatchClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.search_fixed_target(
                    ra=params.ra,
                    dec=params.dec,
                    radius=params.radius,
                    sources=params.sources,
                    start_date=params.start_date,
                    stop_date=params.stop_date,
                )

            if response.error:
                logger.error(f"CATCH API returned error: {response.error}")
                raise SBNCatchClientError(response.error)

            # Get field set for filtering
            field_set = FIELD_PROFILES.get(params.fields, SUMMARY_FIELDS)

            # Enforce maximum limit
            effective_limit = min(params.limit, MAX_OBSERVATIONS_LIMIT)

            # Get total count before limiting
            total_available = len(response.observations)

            # Apply offset and limit
            limited_observations = response.observations[params.offset : params.offset + effective_limit]
            has_more = params.offset + len(limited_observations) < total_available

            # Filter fields for each observation
            observations = [
                filter_observation(obs.model_dump(exclude_none=True), field_set) for obs in limited_observations
            ]

            return SBNSearchCoordinatesOutputSchema(
                ra=params.ra,
                dec=params.dec,
                radius=params.radius,
                count=len(observations),
                total_available=total_available,
                offset=params.offset,
                limit=effective_limit,
                has_more=has_more,
                fields=params.fields,
                observations=observations,
            )

        except SBNCatchClientError as e:
            logger.error(f"SBN client error in search_coordinates: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_coordinates: {e}")
            raise RuntimeError(f"Internal error: {e}") from e
