"""Shim — the GeoUI Protocol core moved to ``akd_ext.tools.geoui.core``."""

from akd_ext.tools.geoui.core import (
    GEOUI_PROTOCOL_VERSION,
    GeoIntent,
    LayerRef,
    TimeWindow,
    Viewport,
)

__all__ = [
    "GEOUI_PROTOCOL_VERSION",
    "GeoIntent",
    "LayerRef",
    "TimeWindow",
    "Viewport",
]
