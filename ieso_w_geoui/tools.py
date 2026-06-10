"""Shim — the GeoUI tools moved to ``akd_ext.tools.geoui.tools``.

The canonical classes are ``@mcp_tool``-decorated there, so they are
also auto-registered on the akd-ext MCP server (``akd_ext.mcp.server``).
"""

from akd_ext.tools.geoui.tools import (
    GeoUIGetStateInputSchema,
    GeoUIGetStateOutputSchema,
    GeoUIGetStateTool,
    GeoUIRenderIntentInputSchema,
    GeoUIRenderIntentOutputSchema,
    GeoUIRenderIntentTool,
)

__all__ = [
    "GeoUIGetStateInputSchema",
    "GeoUIGetStateOutputSchema",
    "GeoUIGetStateTool",
    "GeoUIRenderIntentInputSchema",
    "GeoUIRenderIntentOutputSchema",
    "GeoUIRenderIntentTool",
]
