"""AKD tools exposing the GeoUI Protocol over the Worldview adapter.

Two tools, both pure / no I/O:

- ``GeoUIRenderIntentTool`` — agent constructs a ``GeoIntent`` describing
  the desired application state; tool returns a Worldview permalink URL.
- ``GeoUIGetStateTool`` — agent passes a Worldview URL; tool returns the
  current state as a ``GeoIntent``.

Both are decorated with ``@mcp_tool`` so they are auto-registered on the
akd-ext MCP server (``akd_ext.mcp.server``). They can also be wired into
a ``PydanticAIBaseAgentConfig`` via the ``tools`` field — the base class
auto-converts AKD ``BaseTool`` instances to pydantic_ai tools.
"""

from __future__ import annotations

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool
from pydantic import Field

from akd_ext.mcp import mcp_tool
from akd_ext.tools.geoui.adapter import intent_to_url, url_to_intent
from akd_ext.tools.geoui.core import GeoIntent


# -----------------------------------------------------------------------------
# render_intent
# -----------------------------------------------------------------------------


class GeoUIRenderIntentInputSchema(InputSchema):
    """Input for ``GeoUIRenderIntentTool``."""

    intent: GeoIntent = Field(
        ...,
        description=(
            "GeoIntent describing the desired application state. "
            "Core fields: viewport (bbox + crs), time (instant), layers (id + visible + opacity). "
            "Use extensions by adding their URI to `geoui_extensions` and including the "
            "corresponding namespaced fields: "
            "geoui:compare/v1.0.0 → compare:layers, compare:time, compare:mode, "
            "compare:value, compare:active_side; "
            "geoui:chart/v1.0.0 → chart:layer, chart:area, chart:time, chart:autoload; "
            "geoui:raster-styling/v1.0.0 → on each LayerRef: raster-styling:palettes, "
            "raster-styling:min, raster-styling:max, raster-styling:squash, raster-styling:style."
        ),
    )


class GeoUIRenderIntentOutputSchema(OutputSchema):
    """Output for ``GeoUIRenderIntentTool``."""

    url: str = Field(
        ...,
        description="Worldview permalink URL that opens the map at the requested state.",
    )


@mcp_tool
class GeoUIRenderIntentTool(BaseTool[GeoUIRenderIntentInputSchema, GeoUIRenderIntentOutputSchema]):
    """Render a GeoIntent as a NASA Worldview permalink URL.

    Use this tool to materialise the agent's intended application state
    (expressed as a GeoIntent) into a URL the user can open. The agent
    reasons in GeoIntent terms, not Worldview-specific URL params.
    """

    input_schema = GeoUIRenderIntentInputSchema
    output_schema = GeoUIRenderIntentOutputSchema

    async def _arun(self, params: GeoUIRenderIntentInputSchema) -> GeoUIRenderIntentOutputSchema:
        return GeoUIRenderIntentOutputSchema(url=intent_to_url(params.intent))


# -----------------------------------------------------------------------------
# get_state
# -----------------------------------------------------------------------------


class GeoUIGetStateInputSchema(InputSchema):
    """Input for ``GeoUIGetStateTool``."""

    url: str = Field(..., description="Worldview permalink URL to parse.")


class GeoUIGetStateOutputSchema(OutputSchema):
    """Output for ``GeoUIGetStateTool``."""

    intent: GeoIntent = Field(
        ...,
        description="GeoIntent describing the application state encoded in the URL.",
    )


@mcp_tool
class GeoUIGetStateTool(BaseTool[GeoUIGetStateInputSchema, GeoUIGetStateOutputSchema]):
    """Read the current Worldview application state as a GeoIntent.

    Use this to observe the state implied by a Worldview URL — typically
    when continuing an iterative analysis: read current state, decide
    what to change, emit a new GeoIntent via ``geoui_render_intent``.

    Auto-injected base reflectance and reference overlay layers are
    preserved in the output for fidelity; ignore them when computing
    refinements.
    """

    input_schema = GeoUIGetStateInputSchema
    output_schema = GeoUIGetStateOutputSchema

    async def _arun(self, params: GeoUIGetStateInputSchema) -> GeoUIGetStateOutputSchema:
        return GeoUIGetStateOutputSchema(intent=url_to_intent(params.url))
