"""GeoUI Protocol tools for akd_ext.

Application-agnostic geospatial-UI intent protocol (GeoIntent) plus the
Worldview adapter and the two AKD tools that expose it (also served over
MCP via ``akd_ext.mcp.server``).
"""

from akd_ext.tools.geoui import extensions
from akd_ext.tools.geoui.adapter import (
    CRS_TO_WORLDVIEW_PROJECTION,
    WORLDVIEW_PROJECTION_TO_CRS,
    intent_to_permalink_input,
    intent_to_url,
    permalink_input_to_intent,
    url_to_intent,
)
from akd_ext.tools.geoui.core import (
    GEOUI_PROTOCOL_VERSION,
    GeoIntent,
    LayerRef,
    TimeWindow,
    Viewport,
)
from akd_ext.tools.geoui.tools import (
    GeoUIGetStateInputSchema,
    GeoUIGetStateOutputSchema,
    GeoUIGetStateTool,
    GeoUIRenderIntentInputSchema,
    GeoUIRenderIntentOutputSchema,
    GeoUIRenderIntentTool,
)
from akd_ext.tools.geoui.url_parser import parse_url

__all__ = [
    "CRS_TO_WORLDVIEW_PROJECTION",
    "GEOUI_PROTOCOL_VERSION",
    "GeoIntent",
    "GeoUIGetStateInputSchema",
    "GeoUIGetStateOutputSchema",
    "GeoUIGetStateTool",
    "GeoUIRenderIntentInputSchema",
    "GeoUIRenderIntentOutputSchema",
    "GeoUIRenderIntentTool",
    "LayerRef",
    "TimeWindow",
    "Viewport",
    "WORLDVIEW_PROJECTION_TO_CRS",
    "extensions",
    "intent_to_permalink_input",
    "intent_to_url",
    "parse_url",
    "permalink_input_to_intent",
    "url_to_intent",
]
