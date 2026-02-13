"""Get valid instrument and product type combinations for a planetary target."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.ode.types import TargetType
from akd_ext.tools.pds.utils.ode_client import ODEClient, ODEClientError


MAX_INSTRUMENTS_LIMIT = 25  # Max instruments returned


class ODEInstrumentSummary(BaseModel):
    """Instrument item in list_instruments results."""

    ihid: str
    instrument_host_name: str
    iid: str
    instrument_name: str
    pt: str
    product_type_name: str
    number_products: int


class ODEListInstrumentsInputSchema(InputSchema):
    """Input schema for ODEListInstrumentsTool."""

    target: TargetType = Field(..., description="Planetary body to query")
    ihid: str | None = Field(None, description="Filter by Instrument Host ID (e.g., 'MRO', 'LRO', 'MESS'). Optional.")
    iid: str | None = Field(None, description="Filter by Instrument ID (e.g., 'HIRISE', 'CTX', 'LROC'). Optional.")
    limit: int = Field(25, ge=1, le=25, description="Maximum combinations to return (default 25, max 25)")


class ODEListInstrumentsOutputSchema(OutputSchema):
    """Output schema for ODEListInstrumentsTool."""

    status: str = Field(..., description="Response status ('success' or 'error')")
    target: str = Field(..., description="Planetary body that was queried")
    count: int = Field(..., description="Number of instrument combinations returned")
    total_available: int = Field(..., description="Total number of combinations available")
    has_more: bool = Field(..., description="Whether more combinations are available")
    instruments: list[ODEInstrumentSummary] = Field(
        default_factory=list, description="List of instrument combinations with product counts"
    )
    error: str | None = Field(None, description="Error message if status is 'error'")


class ODEListInstrumentsToolConfig(BaseToolConfig):
    """Configuration for ODEListInstrumentsTool."""

    base_url: str = Field(
        default=os.getenv("ODE_BASE_URL", "https://oderest.rsl.wustl.edu/live2/"),
        description="ODE API base URL (override with ODE_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class ODEListInstrumentsTool(BaseTool[ODEListInstrumentsInputSchema, ODEListInstrumentsOutputSchema]):
    """Get valid instrument and product type combinations for a planetary target.

    This tool returns available instrument host/instrument/product type combinations
    with product counts. Use this to discover what data is available before searching.

    Each combination represents a specific type of data product available in ODE:
    - Instrument Host (ihid): The spacecraft or mission (e.g., "MRO", "LRO")
    - Instrument (iid): The specific instrument (e.g., "HIRISE", "CTX")
    - Product Type (pt): The data product type (e.g., "RDRV11", "EDR")

    This information is essential for constructing valid search queries, as the
    ODESearchProductsTool requires these identifiers.
    """

    input_schema = ODEListInstrumentsInputSchema
    output_schema = ODEListInstrumentsOutputSchema
    config_schema = ODEListInstrumentsToolConfig

    async def _arun(self, params: ODEListInstrumentsInputSchema) -> ODEListInstrumentsOutputSchema:
        """Execute the instruments list query.

        Args:
            params: Input parameters for the query

        Returns:
            List of available instrument combinations with product counts

        Raises:
            ODEClientError: If the API request fails
        """
        try:
            async with ODEClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.list_instruments(params.target)

            if response.status == "ERROR":
                return ODEListInstrumentsOutputSchema(
                    status="error",
                    target=params.target,
                    count=0,
                    total_available=0,
                    has_more=False,
                    error=response.error,
                )

            # Filter by instrument host and/or instrument if specified
            filtered_instruments = response.instruments
            if params.ihid:
                filtered_instruments = [inst for inst in filtered_instruments if inst.ihid == params.ihid]
            if params.iid:
                filtered_instruments = [inst for inst in filtered_instruments if inst.iid == params.iid]

            total_available = len(filtered_instruments)

            # Enforce maximum limit
            limit = min(params.limit, MAX_INSTRUMENTS_LIMIT)
            instruments = [
                ODEInstrumentSummary(
                    ihid=inst.ihid,
                    instrument_host_name=inst.instrument_host_name,
                    iid=inst.iid,
                    instrument_name=inst.instrument_name,
                    pt=inst.pt,
                    product_type_name=inst.pt_name,
                    number_products=inst.number_products,
                )
                for inst in filtered_instruments[:limit]
            ]

            return ODEListInstrumentsOutputSchema(
                status="success",
                target=params.target,
                count=len(instruments),
                total_available=total_available,
                has_more=len(instruments) < total_available,
                instruments=instruments,
            )

        except ODEClientError as e:
            logger.error(f"ODE client error in list_instruments: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in list_instruments: {e}")
            raise RuntimeError(f"Internal error during instruments query: {e}") from e
