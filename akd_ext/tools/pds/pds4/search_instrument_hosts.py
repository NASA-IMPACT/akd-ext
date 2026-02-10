"""Search PDS Context products that are Instrument Hosts (spacecraft, rovers, telescopes)."""

import logging
from typing import Annotated

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.pds4.types import INSTRUMENT_HOST_TYPE
from akd_ext.tools.pds.utils.pds4_client import PDS4Client, PDS4ClientError

logger = logging.getLogger(__name__)


class InstrumentHostSummary(BaseModel):
    """Instrument host item in search results."""

    id: str
    lid: str | None = None
    lidvid: str | None = None
    title: str | None = None
    instrument_host: dict | None = None


class PDS4SearchInstrumentHostsInputSchema(InputSchema):
    """Input schema for PDS4SearchInstrumentHostsTool."""

    keywords: str | None = Field(
        None, description="Space-delimited search terms (e.g. 'mars rover', 'voyager spacecraft')"
    )
    instrument_host_type: INSTRUMENT_HOST_TYPE | None = Field(
        None, description="Filter by instrument host type"
    )
    limit: Annotated[int, Field(ge=0, le=100)] = Field(10, description="Max results (default 10)")


class PDS4SearchInstrumentHostsOutputSchema(OutputSchema):
    """Output schema for PDS4SearchInstrumentHostsTool."""

    total_hits: int = Field(..., description="Total number of matching instrument hosts")
    query_time_ms: int | None = Field(None, description="Query execution time in milliseconds")
    query: str | None = Field(None, description="The query string that was executed")
    limit: int = Field(..., description="Number of results requested")
    instrument_hosts: list[InstrumentHostSummary] = Field(
        default_factory=list, description="List of matching instrument hosts"
    )


class PDS4SearchInstrumentHostsToolConfig(BaseToolConfig):
    """Configuration for PDS4SearchInstrumentHostsTool."""

    base_url: str = Field(default="https://pds.mcp.nasa.gov/api/search/1/", description="PDS4 API base URL")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


@mcp_tool
class PDS4SearchInstrumentHostsTool(BaseTool[PDS4SearchInstrumentHostsInputSchema, PDS4SearchInstrumentHostsOutputSchema]):
    """Search PDS Context products that are Instrument Hosts (spacecraft, rovers, telescopes).

    Instrument Hosts are platforms that carry scientific instruments: spacecraft, rovers, landers, telescopes.

    Example: Cassini Orbiter - urn:nasa:pds:context:instrument_host:spacecraft.cassini

    Use for queries about specific spacecraft, rovers, or platforms that carry instruments.
    """

    input_schema = PDS4SearchInstrumentHostsInputSchema
    output_schema = PDS4SearchInstrumentHostsOutputSchema
    config_schema = PDS4SearchInstrumentHostsToolConfig

    async def _arun(self, params: PDS4SearchInstrumentHostsInputSchema) -> PDS4SearchInstrumentHostsOutputSchema:
        """Execute the instrument host search."""
        try:
            async with PDS4Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.search_context_instrument_hosts(
                    keywords=params.keywords,
                    instrument_host_type=params.instrument_host_type,
                    limit=params.limit,
                )

            instrument_hosts: list[InstrumentHostSummary] = []
            for host in response.data:
                host_summary = InstrumentHostSummary(
                    id=host.id,
                    lid=host.lid,
                    lidvid=host.lidvid,
                    title=host.title,
                    instrument_host=(
                        host.instrument_host.model_dump(exclude_none=True) if host.instrument_host else None
                    ),
                )
                instrument_hosts.append(host_summary)

            return PDS4SearchInstrumentHostsOutputSchema(
                total_hits=response.summary.hits,
                query_time_ms=response.summary.took,
                query=response.summary.q,
                limit=params.limit,
                instrument_hosts=instrument_hosts,
            )

        except PDS4ClientError as e:
            logger.error(f"PDS4 client error in search_instrument_hosts: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_instrument_hosts: {e}")
            raise RuntimeError(f"Internal error during instrument host search: {e}") from e
