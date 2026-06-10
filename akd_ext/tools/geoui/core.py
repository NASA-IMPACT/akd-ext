"""GeoUI Protocol core — v1.0.0.

Application-agnostic intent schema for geospatial-visualization UIs.
Inspired by STAC: tiny required core + opt-in URI-identified extensions
+ namespaced field prefixes + composable validation.

Extension fields live as extra keys on `GeoIntent` and `LayerRef`, using
the convention `"<prefix>:<field>"` (e.g. `"compare:layers"`,
`"raster-styling:palettes"`). The URIs declared in `geoui_extensions`
identify which extension schemas should validate the document.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

GEOUI_PROTOCOL_VERSION = "1.0.0"


class LayerRef(BaseModel):
    """A reference to a renderable layer.

    `id` is application-defined — the conforming app must be able to
    resolve it to a layer in its own catalogue. Per-layer rendering hints
    beyond the universal set (`visible`, `opacity`) belong in extensions
    and are expressed as namespaced extra keys
    (e.g. `"raster-styling:palettes": [...]`).
    """

    id: str
    visible: bool = True
    opacity: float | None = Field(default=None, ge=0.0, le=1.0)

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def extension_fields(self, prefix: str) -> dict[str, object]:
        """Return all extra fields whose key starts with `"<prefix>:"`."""
        marker = f"{prefix}:"
        extras = self.__pydantic_extra__ or {}
        return {k: v for k, v in extras.items() if k.startswith(marker)}


class Viewport(BaseModel):
    """Spatial viewport.

    `bbox` is interpreted in `crs`. For the geographic default
    (`EPSG:4326`), `bbox` is `[west, south, east, north]` in degrees.
    For projected CRSs, the values are projected coordinates.
    `bbox=None` means "app default extent."
    """

    bbox: list[float] | None = Field(default=None, min_length=4, max_length=4)
    crs: str = "EPSG:4326"


class TimeWindow(BaseModel):
    """Time selection.

    Either a single `instant` OR a closed range `{start, end}` — the two
    are mutually exclusive. All fields `None` is allowed and means
    "app default time."
    """

    instant: str | date | datetime | None = None
    start: str | date | datetime | None = None
    end: str | date | datetime | None = None

    @model_validator(mode="after")
    def _exclusive(self) -> Self:
        if self.instant is not None and (self.start is not None or self.end is not None):
            raise ValueError("`instant` and `start`/`end` are mutually exclusive")
        if (self.start is None) ^ (self.end is None):
            raise ValueError("`start` and `end` must both be set or both omitted")
        return self


class GeoIntent(BaseModel):
    """The GeoUI Protocol root.

    Carries the minimal cross-application contract: viewport, time,
    layers. Extension fields are namespaced (e.g. `"compare:layers"`)
    and live as extra keys; their semantics are defined by the schemas
    pointed to by `geoui_extensions`.
    """

    geoui_version: str = GEOUI_PROTOCOL_VERSION
    geoui_extensions: list[str] = Field(default_factory=list)

    viewport: Viewport = Field(default_factory=Viewport)
    time: TimeWindow | None = None
    layers: list[LayerRef] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def extension_fields(self, prefix: str) -> dict[str, object]:
        """Return all extra fields whose key starts with `"<prefix>:"`.

        Adapter / extension validators use this to pluck out their slice
        of the intent without scanning the whole document.
        """
        marker = f"{prefix}:"
        extras = self.__pydantic_extra__ or {}
        return {k: v for k, v in extras.items() if k.startswith(marker)}
