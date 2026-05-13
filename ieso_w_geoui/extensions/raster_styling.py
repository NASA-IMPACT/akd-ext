"""GeoUI Raster Styling Extension — v1.0.0.

Per-layer rendering hints for raster layers. Unlike the intent-level
extensions (compare, chart), this extension's fields live on each
LayerRef rather than on the GeoIntent root.

Declared by URI: ``https://geoui.org/ext/raster-styling/v1.0.0``
Namespace prefix: ``raster-styling:``

Optional fields per layer:
  - ``raster-styling:palettes`` — list of palette ids to apply, in order.
  - ``raster-styling:style``    — vector/raster style id.
  - ``raster-styling:min``      — lower bound of the palette/data range.
  - ``raster-styling:max``      — upper bound of the palette/data range.
  - ``raster-styling:squash``   — palette is squashed to min/max range.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ieso_w_geoui.core import GeoIntent, LayerRef

URI = "https://geoui.org/ext/raster-styling/v1.0.0"
PREFIX = "raster-styling"


class RasterStylingFields(BaseModel):
    """Typed view of the ``raster-styling:*`` fields on a LayerRef."""

    palettes: list[str] | None = None
    style: str | None = None
    min: float | None = None
    max: float | None = None
    squash: bool = False

    model_config = ConfigDict(populate_by_name=True)


def extract(layer: LayerRef) -> RasterStylingFields | None:
    """Pull ``raster-styling:*`` fields off a layer.

    Returns None if no styling fields are present.
    """
    raw = layer.extension_fields(PREFIX)
    if not raw:
        return None
    stripped = {k.removeprefix(f"{PREFIX}:"): v for k, v in raw.items()}
    return RasterStylingFields(**stripped)


def inject(layer: LayerRef, fields: RasterStylingFields) -> LayerRef:
    """Return a new LayerRef with ``raster-styling:*`` fields populated."""
    payload = fields.model_dump(exclude_none=True)
    extras = {f"{PREFIX}:{k}": v for k, v in payload.items()}

    base = layer.model_dump(by_alias=True)
    base.update(extras)
    return LayerRef.model_validate(base)


def declare(intent: GeoIntent) -> GeoIntent:
    """Add the raster-styling URI to a GeoIntent's declared extensions.

    Idempotent. Does not mutate.
    """
    if URI in intent.geoui_extensions:
        return intent
    extensions = [*intent.geoui_extensions, URI]
    base = intent.model_dump(by_alias=True)
    base["geoui_extensions"] = extensions
    return GeoIntent.model_validate(base)


def validate(intent: GeoIntent) -> None:
    """Validate raster-styling fields on each layer of the intent.

    No-op if the extension is not declared. Raises ValueError if a layer
    has ``raster-styling:*`` fields without the extension being declared.
    """
    declared = URI in intent.geoui_extensions
    for layer in intent.layers:
        if layer.extension_fields(PREFIX):
            if not declared:
                raise ValueError(
                    f"LayerRef(id={layer.id!r}) has `{PREFIX}:*` fields but the GeoIntent "
                    f"does not declare {URI} in geoui_extensions"
                )
            # Typed construction enforces field-type validity.
            extract(layer)
