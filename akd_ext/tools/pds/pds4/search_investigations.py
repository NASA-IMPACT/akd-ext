"""Search PDS Context products that are Investigations (missions/projects)."""

import logging
from typing import Annotated

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.pds4_client import PDS4Client, PDS4ClientError

logger = logging.getLogger(__name__)


class InvestigationSummary(BaseModel):
    """Investigation item in search results."""

    id: str
    lid: str | None = None
    lidvid: str | None = None
    title: str | None = None
    investigation: dict | None = None
    label_file_info: dict | None = None


class PDS4SearchInvestigationsInputSchema(InputSchema):
    """Input schema for PDS4SearchInvestigationsTool."""

    keywords: str | None = Field(
        None, description="Space-delimited search terms (e.g. 'mars rover', 'jupiter cassini')"
    )
    limit: Annotated[int, Field(ge=0, le=100)] = Field(10, description="Max results (default 10)")


class PDS4SearchInvestigationsOutputSchema(OutputSchema):
    """Output schema for PDS4SearchInvestigationsTool."""

    total_hits: int = Field(..., description="Total number of matching investigations")
    query_time_ms: int | None = Field(None, description="Query execution time in milliseconds")
    query: str | None = Field(None, description="The query string that was executed")
    limit: int = Field(..., description="Number of results requested")
    investigations: list[InvestigationSummary] = Field(
        default_factory=list, description="List of matching investigations"
    )


class PDS4SearchInvestigationsToolConfig(BaseToolConfig):
    """Configuration for PDS4SearchInvestigationsTool."""

    base_url: str = Field(default="https://pds.mcp.nasa.gov/api/search/1/", description="PDS4 API base URL")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


@mcp_tool
class PDS4SearchInvestigationsTool(BaseTool[PDS4SearchInvestigationsInputSchema, PDS4SearchInvestigationsOutputSchema]):
    """Search PDS Context products that are Investigations (missions/projects).

    Investigations are organized missions or projects that collect scientific data.

    Example: Cassini-Huygens - urn:nasa:pds:context:investigation:mission.cassini-huygens

    Use for queries about space missions, mission timelines, or finding missions that studied
    specific targets.
    """

    input_schema = PDS4SearchInvestigationsInputSchema
    output_schema = PDS4SearchInvestigationsOutputSchema
    config_schema = PDS4SearchInvestigationsToolConfig

    async def _arun(self, params: PDS4SearchInvestigationsInputSchema) -> PDS4SearchInvestigationsOutputSchema:
        """Execute the investigation search."""
        try:
            async with PDS4Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.search_context_investigations(
                    keywords=params.keywords,
                    limit=params.limit,
                )

            investigations: list[InvestigationSummary] = []
            for investigation in response.data:
                inv_summary = InvestigationSummary(
                    id=investigation.id,
                    lid=investigation.lid,
                    lidvid=investigation.lidvid,
                    title=investigation.title,
                    investigation=(
                        investigation.investigation.model_dump(exclude_none=True)
                        if investigation.investigation
                        else None
                    ),
                    label_file_info=(
                        investigation.label_file_info.model_dump(exclude_none=True)
                        if investigation.label_file_info
                        else None
                    ),
                )
                investigations.append(inv_summary)

            return PDS4SearchInvestigationsOutputSchema(
                total_hits=response.summary.hits,
                query_time_ms=response.summary.took,
                query=response.summary.q,
                limit=params.limit,
                investigations=investigations,
            )

        except PDS4ClientError as e:
            logger.error(f"PDS4 client error in search_investigations: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_investigations: {e}")
            raise RuntimeError(f"Internal error during investigation search: {e}") from e
