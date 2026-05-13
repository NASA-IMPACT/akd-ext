"""GeoUI Protocol extensions — v1.0.0.

Each extension defines:
  - `URI` — canonical, versioned URI identifying the extension.
  - `PREFIX` — the namespaced field prefix (`<prefix>:<field>`).
  - A typed Pydantic model for the extension's fields.
  - `extract(intent)` / `inject(intent, fields)` helpers that move data
    between the typed model and the GeoIntent's namespaced extra keys.
  - `validate(intent)` for layered validation; no-op when the extension
    is not declared.
"""

from ieso_w_geoui.extensions import chart, compare, raster_styling

__all__ = ["chart", "compare", "raster_styling"]
