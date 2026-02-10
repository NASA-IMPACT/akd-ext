"""Search for observations of a comet or asteroid."""

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
    SBNSourceStatusSummary,
    filter_observation,
)
from akd_ext.tools.pds.utils.sbn_client import SBNCatchClient, SBNCatchClientError

logger = logging.getLogger(__name__)


class SBNSearchObjectInputSchema(InputSchema):
    """Input schema for SBNSearchObjectTool."""

    target: str = Field(..., description="JPL Horizons-resolvable designation (e.g., '65803', '1P/Halley', 'Didymos')")
    sources: list[str] | None = Field(None, description=VALID_SOURCES_DESCRIPTION)
    start_date: str | None = Field(
        None, description="Start date filter (format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM')"
    )
    stop_date: str | None = Field(None, description="Stop date filter (format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM')")
    cached: bool = Field(True, description="Use cached results if available (default True, faster)")
    timeout: Annotated[float, Field(gt=0, le=600)] = Field(
        120.0, description="Maximum time to wait for results in seconds (default 120)"
    )
    limit: Annotated[int, Field(ge=1, le=10)] = Field(
        DEFAULT_OBSERVATIONS_LIMIT, description="Maximum observations to return (default 10, max 10)"
    )
    offset: Annotated[int, Field(ge=0)] = Field(0, description="Skip first N observations for pagination (default 0)")
    fields: Literal["essential", "summary", "full"] = Field(
        "summary", description="Field profile: 'essential' (minimal), 'summary' (default), or 'full' (all fields)"
    )


class SBNSearchObjectOutputSchema(OutputSchema):
    """Output schema for SBNSearchObjectTool."""

    target: str = Field(..., description="The target that was searched")
    count: int = Field(..., description="Number of observations returned in this response")
    total_available: int = Field(..., description="Total number of observations available")
    offset: int = Field(..., description="Offset used for pagination")
    limit: int = Field(..., description="Limit applied to this response")
    has_more: bool = Field(..., description="Whether more results are available beyond this response")
    fields: str = Field(..., description="Field profile used for filtering")
    observations: list[dict[str, Any]] = Field(
        default_factory=list, description="List of observations with filtered fields"
    )
    source_status: list[SBNSourceStatusSummary] = Field(
        default_factory=list, description="Status of each data source queried"
    )


class SBNSearchObjectToolConfig(BaseToolConfig):
    """Configuration for SBNSearchObjectTool."""

    base_url: str = Field(
        default="https://catch-api.astro.umd.edu/",
        description="CATCH API base URL (can be overridden with SBN_BASE_URL env var)",
    )
    timeout: float = Field(default=60.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class SBNSearchObjectTool(BaseTool[SBNSearchObjectInputSchema, SBNSearchObjectOutputSchema]):
    """Search for observations of a comet or asteroid.

    This tool searches astronomical survey data for observations of a specified
    small body (comet or asteroid) using its JPL Horizons designation. The CATCH
    API queries multiple survey archives to find all available observations.

    Target Designation Formats:
    - Asteroid number: "65803" (Didymos)
    - Asteroid name: "Ceres", "Vesta", "Didymos"
    - Provisional designation: "2019 DQ123"
    - Periodic comet: "1P/Halley", "65P"
    - Comet fragment: "73P-B"
    - Provisional comet: "P/2001 YX127"
    - Interstellar object: "1I" (Oumuamua)

    Field Profiles:
    - essential: product_id, source, date, archive_url (minimal metadata)
    - summary: essential + ra, dec, vmag, filter, exposure (most useful fields)
    - full: all available fields including ephemeris, photometry, observing conditions

    The tool automatically waits for long-running searches to complete using the
    specified timeout parameter. Results are paginated client-side since the CATCH
    API returns all results at once.
    """

    input_schema = SBNSearchObjectInputSchema
    output_schema = SBNSearchObjectOutputSchema
    config_schema = SBNSearchObjectToolConfig

    async def _arun(self, params: SBNSearchObjectInputSchema) -> SBNSearchObjectOutputSchema:
        """Execute the tool to search for observations of a moving target."""
        try:
            async with SBNCatchClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.search_and_wait(
                    target=params.target,
                    sources=params.sources,
                    start_date=params.start_date,
                    stop_date=params.stop_date,
                    cached=params.cached,
                    timeout=params.timeout,
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

            # Apply offset and limit (client-side since CATCH API has no pagination)
            limited_observations = response.observations[params.offset : params.offset + effective_limit]
            has_more = params.offset + len(limited_observations) < total_available

            # Filter fields for each observation
            observations = [
                filter_observation(obs.model_dump(exclude_none=True), field_set) for obs in limited_observations
            ]

            return SBNSearchObjectOutputSchema(
                target=params.target,
                count=len(observations),
                total_available=total_available,
                offset=params.offset,
                limit=effective_limit,
                has_more=has_more,
                fields=params.fields,
                observations=observations,
                source_status=[
                    SBNSourceStatusSummary(source=s.source, status=s.status, count=s.count)
                    for s in response.source_status
                ],
            )

        except SBNCatchClientError as e:
            logger.error(f"SBN client error in search_object: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_object: {e}")
            raise RuntimeError(f"Internal error: {e}") from e
