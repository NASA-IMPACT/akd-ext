"""Search PDS Context products that are Targets (celestial bodies, phenomena)."""

import logging
from typing import Annotated

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.pds4.types import TARGET_TYPE
from akd_ext.tools.pds.utils.pds4_client import PDS4Client, PDS4ClientError

logger = logging.getLogger(__name__)


class TargetSummary(BaseModel):
    """Target item in search results."""

    id: str
    lid: str | None = None
    lidvid: str | None = None
    title: str | None = None
    target: dict | None = None
    alias: dict | None = None


class PDS4SearchTargetsInputSchema(InputSchema):
    """Input schema for PDS4SearchTargetsTool."""

    keywords: str | None = Field(
        None, description="Space-delimited search terms (e.g. 'jupiter moon', 'asteroid belt')"
    )
    target_type: TARGET_TYPE | None = Field(None, description="Filter by target type")
    limit: Annotated[int, Field(ge=0, le=100)] = Field(10, description="Max results (default 10)")


class PDS4SearchTargetsOutputSchema(OutputSchema):
    """Output schema for PDS4SearchTargetsTool."""

    total_hits: int = Field(..., description="Total number of matching targets")
    query_time_ms: int | None = Field(None, description="Query execution time in milliseconds")
    query: str | None = Field(None, description="The query string that was executed")
    limit: int = Field(..., description="Number of results requested")
    targets: list[TargetSummary] = Field(default_factory=list, description="List of matching targets")


class PDS4SearchTargetsToolConfig(BaseToolConfig):
    """Configuration for PDS4SearchTargetsTool."""

    base_url: str = Field(default="https://pds.mcp.nasa.gov/api/search/1/", description="PDS4 API base URL")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


@mcp_tool
class PDS4SearchTargetsTool(BaseTool[PDS4SearchTargetsInputSchema, PDS4SearchTargetsOutputSchema]):
    """Search PDS Context products that are Targets (celestial bodies, phenomena).

    Targets are objects of scientific study: planets, moons, asteroids, comets, etc.

    Example: Mars - urn:nasa:pds:context:target:planet.mars

    Use for queries about specific celestial bodies, finding targets by type, or targets
    studied by missions.
    """

    input_schema = PDS4SearchTargetsInputSchema
    output_schema = PDS4SearchTargetsOutputSchema
    config_schema = PDS4SearchTargetsToolConfig

    async def _arun(self, params: PDS4SearchTargetsInputSchema) -> PDS4SearchTargetsOutputSchema:
        """Execute the target search."""
        try:
            async with PDS4Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.search_context_targets(
                    keywords=params.keywords,
                    target_type=params.target_type,
                    limit=params.limit,
                )

            targets: list[TargetSummary] = []
            for target_item in response.data:
                target_summary = TargetSummary(
                    id=target_item.id,
                    lid=target_item.lid,
                    lidvid=target_item.lidvid,
                    title=target_item.title,
                    target=target_item.target.model_dump(exclude_none=True) if target_item.target else None,
                    alias=target_item.alias.model_dump(exclude_none=True) if target_item.alias else None,
                )
                targets.append(target_summary)

            return PDS4SearchTargetsOutputSchema(
                total_hits=response.summary.hits,
                query_time_ms=response.summary.took,
                query=response.summary.q,
                limit=params.limit,
                targets=targets,
            )

        except PDS4ClientError as e:
            logger.error(f"PDS4 client error in search_targets: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_targets: {e}")
            raise RuntimeError(f"Internal error during target search: {e}") from e
