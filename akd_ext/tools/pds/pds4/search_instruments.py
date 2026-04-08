"""Search the latest-versioned instances of PDS Context products that are Instruments."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.pds4.types import INSTRUMENT_TYPE
from akd_ext.tools.pds.utils.pds4_client import PDS4Client, PDS4ClientError


class InstrumentSummary(BaseModel):
    """Instrument item in search results."""

    id: str
    lid: str | None = None
    lidvid: str | None = None
    title: str | None = None
    instrument: dict | None = None


class PDS4SearchInstrumentsInputSchema(InputSchema):
    """Input schema for PDS4SearchInstrumentsTool."""

    keywords: str | None = Field(
        None, description="Space-delimited search terms (e.g. 'camera mars', 'spectrometer cassini')"
    )
    instrument_type: INSTRUMENT_TYPE | None = Field(None, description="Filter by instrument type")
    limit: int = Field(10, ge=0, le=25, description="Max results (default 10, max 25)")


class PDS4SearchInstrumentsOutputSchema(OutputSchema):
    """Output schema for PDS4SearchInstrumentsTool."""

    total_hits: int = Field(..., description="Total number of matching instruments")
    query_time_ms: int | None = Field(None, description="Query execution time in milliseconds")
    query: str | None = Field(None, description="The query string that was executed")
    limit: int = Field(..., description="Number of results requested")
    instruments: list[InstrumentSummary] = Field(default_factory=list, description="List of matching instruments")


class PDS4SearchInstrumentsToolConfig(BaseToolConfig):
    """Configuration for PDS4SearchInstrumentsTool."""

    base_url: str = Field(
        default=os.getenv("PDS4_BASE_URL", "https://pds.mcp.nasa.gov/api/search/1/"),
        description="PDS4 API base URL (override with PDS4_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


@mcp_tool
class PDS4SearchInstrumentsTool(BaseTool[PDS4SearchInstrumentsInputSchema, PDS4SearchInstrumentsOutputSchema]):
    """Search the latest-versioned instances of PDS Context products that are Instruments.

    Instruments are scientific devices (cameras, spectrometers, etc.) used on spacecraft to collect data.

    Example: Cassini RADAR - urn:nasa:pds:context:instrument:radar.cassini

    Use for queries about specific instruments, instrument types, or instruments on missions/spacecraft.
    """

    input_schema = PDS4SearchInstrumentsInputSchema
    output_schema = PDS4SearchInstrumentsOutputSchema
    config_schema = PDS4SearchInstrumentsToolConfig

    async def _arun(self, params: PDS4SearchInstrumentsInputSchema) -> PDS4SearchInstrumentsOutputSchema:
        """Execute the instrument search."""
        try:
            async with PDS4Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.search_context_instruments(
                    keywords=params.keywords,
                    instrument_type=params.instrument_type,
                    limit=params.limit,
                )

            instruments: list[InstrumentSummary] = []
            for instrument_item in response.data:
                inst_summary = InstrumentSummary(
                    id=instrument_item.id,
                    lid=instrument_item.lid,
                    lidvid=instrument_item.lidvid,
                    title=instrument_item.title,
                    instrument=(
                        instrument_item.instrument.model_dump(exclude_none=True) if instrument_item.instrument else None
                    ),
                )
                instruments.append(inst_summary)

            return PDS4SearchInstrumentsOutputSchema(
                total_hits=response.summary.hits,
                query_time_ms=response.summary.took,
                query=response.summary.q,
                limit=params.limit,
                instruments=instruments,
            )

        except PDS4ClientError as e:
            logger.error(f"PDS4 client error in search_instruments: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_instruments: {e}")
            raise RuntimeError(f"Internal error during instrument search: {e}") from e
