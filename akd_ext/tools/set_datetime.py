"""Set datetime tool: validate and normalize ISO-8601 datetime ranges."""
from __future__ import annotations

import re

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool
from pydantic import Field

from akd_ext.mcp import mcp_tool


def _validate_datetime(datetime_str: str | None) -> tuple[str | None, str | None]:
    """Validate and normalize ISO-8601 datetime range.

    Args:
        datetime_str: Expected format "YYYY-MM-DD/YYYY-MM-DD" or with time "YYYY-MM-DDTHH:MM:SSZ/..."

    Returns:
        (normalized_datetime, error) - error is None if valid
    """
    if not datetime_str:
        return None, None

    if "/" not in datetime_str:
        return None, f"Invalid datetime format: expected 'start/end' but got '{datetime_str}'"

    parts = datetime_str.split("/")
    if len(parts) != 2:
        return None, f"Invalid datetime format: expected exactly one '/' separator"

    start, end = parts[0].strip(), parts[1].strip()

    # Validate each part is parseable as ISO date
    iso_pattern = r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?)?$'
    for part, label in [(start, "start"), (end, "end")]:
        if not re.match(iso_pattern, part):
            return None, f"Invalid {label} date: expected ISO-8601 format (e.g., '2021-10-01' or '2021-10-01T00:00:00Z') but got '{part}'"

    return f"{start}/{end}", None


class SetDatetimeToolInputSchema(InputSchema):
    """Input schema for the set_datetime tool."""

    value: str = Field(
        ..., description="ISO-8601 datetime range (e.g. '2021-10-01/2021-12-31')"
    )


class SetDatetimeToolOutputSchema(OutputSchema):
    """Output schema for the set_datetime tool."""

    datetime: str | None = Field(None, description="Validated and normalized datetime range")
    error: str | None = Field(None, description="Error message if validation failed")


@mcp_tool
class SetDatetimeTool(BaseTool[SetDatetimeToolInputSchema, SetDatetimeToolOutputSchema]):
    """
    Validate and set a datetime range.

    Takes an ISO-8601 datetime range string (e.g. '2021-10-01/2021-12-31')
    and validates the format. Returns the normalized datetime if valid,
    or an error message if the format is incorrect.

    Input parameters (query-time, LLM-controllable):
    - value: ISO-8601 datetime range 'start/end'

    Returns:
    - datetime: Validated datetime range (None if invalid)
    - error: Error message (None if valid)
    """

    input_schema = SetDatetimeToolInputSchema
    output_schema = SetDatetimeToolOutputSchema

    async def _arun(self, params: SetDatetimeToolInputSchema) -> SetDatetimeToolOutputSchema:
        """Validate the datetime range."""
        validated_dt, dt_error = _validate_datetime(params.value)

        if dt_error:
            return SetDatetimeToolOutputSchema(error=f"Invalid datetime: {dt_error}")

        return SetDatetimeToolOutputSchema(datetime=validated_dt)
