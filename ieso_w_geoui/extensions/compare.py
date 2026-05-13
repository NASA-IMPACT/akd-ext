"""GeoUI Compare Extension — v1.0.0.

Adds A/B comparison (side-by-side or overlay) to a GeoIntent.

Declared by URI: ``https://geoui.org/ext/compare/v1.0.0``
Namespace prefix: ``compare:``

Required fields when declared:
  - ``compare:layers`` — B-side layer stack.

Optional fields:
  - ``compare:active_side`` — "A" or "B" (default "A").
  - ``compare:time`` — TimeWindow for the B side (defaults to root time).
  - ``compare:mode`` — "swipe", "spy", or "opacity" (default "swipe").
  - ``compare:value`` — 0..100 swiper position / opacity (default 50).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ieso_w_geoui.core import GeoIntent, LayerRef, TimeWindow

URI = "https://geoui.org/ext/compare/v1.0.0"
PREFIX = "compare"

ActiveSide = Literal["A", "B"]
CompareMode = Literal["swipe", "spy", "opacity"]


class CompareFields(BaseModel):
    """Typed view of the ``compare:*`` fields on a GeoIntent."""

    layers: list[LayerRef] = Field(..., min_length=1)
    active_side: ActiveSide = "A"
    time: TimeWindow | None = None
    mode: CompareMode = "swipe"
    value: int = Field(default=50, ge=0, le=100)

    model_config = ConfigDict(populate_by_name=True)


def extract(intent: GeoIntent) -> CompareFields | None:
    """Pull ``compare:*`` fields off an intent.

    Returns None if the extension is not declared and no ``compare:*``
    fields are present. Raises ValueError if the document is malformed
    (extension declared without required fields, or fields present
    without declaration).
    """
    declared = URI in intent.geoui_extensions
    raw = intent.extension_fields(PREFIX)

    if not declared:
        if raw:
            raise ValueError(f"GeoIntent has `{PREFIX}:*` fields but does not declare {URI} in geoui_extensions")
        return None

    stripped = {k.removeprefix(f"{PREFIX}:"): v for k, v in raw.items()}
    return CompareFields(**stripped)


def inject(intent: GeoIntent, fields: CompareFields) -> GeoIntent:
    """Return a new GeoIntent with ``compare:*`` fields populated.

    Declares the extension URI if not already declared. Does not mutate.
    """
    extensions = list(intent.geoui_extensions)
    if URI not in extensions:
        extensions.append(URI)

    payload = fields.model_dump(exclude_none=True)
    extras = {f"{PREFIX}:{k}": v for k, v in payload.items()}

    base = intent.model_dump(by_alias=True)
    base["geoui_extensions"] = extensions
    base.update(extras)
    return GeoIntent.model_validate(base)


def validate(intent: GeoIntent) -> None:
    """Run compare-extension validation.

    No-op if the extension is not declared. Raises ValueError if
    declared and the document is malformed.
    """
    extract(intent)
