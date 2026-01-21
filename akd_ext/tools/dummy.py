"""
Reference implementation for akd-ext tools.

This module demonstrates the standard pattern for creating tools in akd-ext.

Key concepts:
- Tools inherit from `BaseTool[InputSchema, OutputSchema]`
- Input/Output schemas extend `InputSchema`/`OutputSchema` from `akd._base`
- Schemas use Pydantic `Field` with descriptions
- Tools implement `async _arun(params) -> OutputSchema`

Auto-generated attributes:
- `.name`: Derived from class name (e.g., "DummyTool"), can be overridden via BaseToolConfig
- `.description`: Auto-generated from class docstring + input/output schema field names and descriptions

Example customization:
    from akd.tools import BaseToolConfig

    # Default name and description
    tool = DummyTool()

    # Custom name
    tool = DummyTool(config=BaseToolConfig(name="my_custom_name"))

    # Custom config class (inherit from BaseToolConfig to add/override options)
    class MyToolConfig(BaseToolConfig):
        custom_option: str = "default_value"

    tool = DummyTool(config=MyToolConfig(name="custom", custom_option="foo"))
"""

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool
from pydantic import Field
from akd_ext.mcp import mcp_tool


class DummyInputSchema(InputSchema):
    """Input schema for the DummyTool."""

    query: str = Field(..., description="The query text to pass through")


class DummyOutputSchema(OutputSchema):
    """Output schema for the DummyTool."""

    query: str = Field(..., description="The query text returned unchanged")


@mcp_tool
class DummyTool(BaseTool[DummyInputSchema, DummyOutputSchema]):
    """
    Identity tool that returns the input query unchanged.
    Serves as a reference implementation for akd-ext tools.
    """

    input_schema = DummyInputSchema
    output_schema = DummyOutputSchema

    async def _arun(self, params: DummyInputSchema) -> DummyOutputSchema:
        """Return the input query as-is."""
        return DummyOutputSchema(query=params.query)
