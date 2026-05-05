"""AKD Tool for the NASA Worldview permalink builder.

URL-assembly helpers and the public `build_url` live as static/classmethods on the tool class.
Field descriptions on the input schema are written as agent-facing guidance.
"""

import os
from datetime import date, datetime, timedelta, timezone
from typing import Literal, Self
from urllib.parse import urlencode

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from dateutil import parser as date_parser
from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from akd_ext.mcp import mcp_tool

# -----------------------------------------------------------------------------
# Module global variables
# -----------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://worldview.earthdata.nasa.gov/"

BASE_LAYERS: tuple[str, ...] = (
    "MODIS_Terra_CorrectedReflectance_TrueColor",
    "MODIS_Aqua_CorrectedReflectance_TrueColor",
    "VIIRS_SNPP_CorrectedReflectance_TrueColor",
    "VIIRS_NOAA20_CorrectedReflectance_TrueColor",
    "VIIRS_NOAA21_CorrectedReflectance_TrueColor",
)
BASE_LAYERS_SET: frozenset[str] = frozenset(BASE_LAYERS)
DEFAULT_BASE_LAYER: str = BASE_LAYERS[0]
DEFAULT_REFERENCE_OVERLAYS: tuple[str, ...] = ("Coastlines_15m", "Reference_Features_15m")

_FORBIDDEN_LAYER_CHARS: frozenset[str] = frozenset(",()")


# -----------------------------------------------------------------------------
# Input/Output Schema with Validators
# -----------------------------------------------------------------------------


def _reject_grammar_chars(value: str, field_name: str) -> str:
    """Reject ',', '(', ')' — reserved by Worldview's layer-list grammar.

    The URL format `l=LayerID(mod,mod),LayerID2` uses these characters as
    structural delimiters; embedding them inside an ID, style, or palette
    silently corrupts the URL when Worldview parses it back.
    """
    bad = _FORBIDDEN_LAYER_CHARS.intersection(value)
    if bad:
        raise ValueError(
            f"{field_name}={value!r} contains forbidden character(s) {sorted(bad)}; "
            f"',', '(', and ')' are reserved by Worldview's layer-list grammar"
        )
    return value


def _coerce_to_datetime(t: str | date | datetime) -> datetime:
    """Best-effort coerce a time value to a TZ-aware UTC datetime for comparison.

    Used in model validator during time comparision to check semantics.
    """
    if isinstance(t, str):
        try:
            t = date_parser.parse(t)
        except (ValueError, OverflowError) as e:
            raise ValueError(f"could not parse time {t!r}: {e}") from e
    # datetime is a subclass of date — check it first
    if isinstance(t, datetime):
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    if isinstance(t, date):
        return datetime.combine(t, datetime.min.time(), tzinfo=timezone.utc)
    raise TypeError(f"unsupported time type: {type(t).__name__}")


class LayerSpec(BaseModel):
    """A single Worldview layer, optionally with rendering modifiers.

    Field defaults match Worldview's own defaults; omitted fields are not
    emitted into the URL.
    """

    id: str = Field(
        ...,
        description=(
            "GIBS layer identifier (e.g. 'MODIS_Terra_CorrectedReflectance_TrueColor', "
            "'VIIRS_SNPP_AOD'). Stable strings published by NASA's GIBS service."
        ),
    )
    hidden: bool = Field(
        default=False,
        description=(
            "If True, the layer is included in the layer stack but rendered invisibly. "
            "Useful for pre-loading toggleable layers without rebuilding the link."
        ),
    )
    opacity: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Layer opacity, 0.0 (fully transparent) to 1.0 (fully opaque). None for full opacity.",
    )
    palettes: list[str] | None = Field(
        default=None,
        description=(
            "Custom palette IDs to apply, in order. Only meaningful for raster layers that support palette swapping."
        ),
    )
    style: str | None = Field(
        default=None,
        description="Vector style ID. Only meaningful for vector layers.",
    )
    min: float | None = Field(
        default=None,
        description="Lower bound of the palette/data range. Set together with `max` to clamp the visible range.",
    )
    max: float | None = Field(
        default=None,
        description="Upper bound of the palette/data range.",
    )
    squash: bool = Field(
        default=False,
        description=(
            "If True, the palette is squashed to the designated min/max values "
            "rather than spanning the layer's full data range."
        ),
    )

    @field_validator("id", "style")
    @classmethod
    def _check_string_field(cls, v: str | None, info: ValidationInfo) -> str | None:
        if v is not None:
            _reject_grammar_chars(v, info.field_name)
        return v

    @field_validator("palettes")
    @classmethod
    def _check_palettes(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for item in v:
                _reject_grammar_chars(item, "palettes")
        return v


class WorldviewPermalinkInputSchema(InputSchema):
    """Input schema for the Worldview Permalink Tool."""

    layers: list[LayerSpec] = Field(
        ...,
        description=(
            "One or more LayerSpec instances, in render order (top of stack last). "
            "Each LayerSpec carries a GIBS layer ID plus optional per-layer modifiers "
            "(hidden, opacity, palettes, style, min/max, squash). REQUIRED — at least "
            "one layer must be supplied."
        ),
    )
    projection: Literal["geographic", "arctic", "antarctic"] = Field(
        default="geographic",
        description=(
            "Map projection. 'geographic' for global Mercator (the default), 'arctic' "
            "for north polar stereographic, or 'antarctic' for south polar stereographic."
        ),
    )
    time: str | date | datetime | None = Field(
        default=None,
        description=(
            "Map time. Accepts a date (daily resolution), a datetime (subdaily, "
            "normalised to UTC), or a string in any reasonable date/datetime format — "
            "ISO 8601, 'Sep 15, 2025', '2025/09/15', TZ-aware forms, etc. (parsed via "
            "dateutil). If None, defaults to yesterday (UTC) — Worldview's own 'today' "
            "default can show partially-rendered scenes because daily MODIS/VIIRS data "
            "is still being ingested into GIBS; yesterday guarantees a fully-rendered "
            "scene. Note: ambiguous slash-separated strings like '01/02/2025' are "
            "interpreted as month/day/year by default; pass an unambiguous form "
            "('2025-01-02') if the order matters."
        ),
    )
    bbox: tuple[float, float, float, float] | None = Field(
        default=None,
        description=(
            "Map viewport extent as (west, south, east, north). Degrees for the "
            "geographic projection; projected meters for arctic/antarctic. "
            "If None, Worldview opens at its default global extent."
        ),
    )
    rotation: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description=(
            "Map rotation in degrees, range -180 to 180. Honored only by arctic/"
            "antarctic projections; ignored by geographic."
        ),
    )

    compare_active: bool | None = Field(
        default=None,
        description=(
            "Activates Worldview's compare mode. Tri-state: None (default) — compare "
            "OFF, no compare params emitted, all other compare_* args silently ignored. "
            "True — compare ON with the A state shown as active. False — compare ON "
            "with the B state shown as active. When set (True or False), compare_layers "
            "is REQUIRED."
        ),
    )
    compare_layers: list[LayerSpec] | None = Field(
        default=None,
        description=(
            "LayerSpec instances for the B state, same shape as `layers`. REQUIRED when compare_active is not None."
        ),
    )
    compare_time: str | date | datetime | None = Field(
        default=None,
        description=(
            "Time for the B state, same accepted forms as `time`. Optional even when "
            "compare is on; if omitted, the B state uses the same time as the A state."
        ),
    )
    compare_mode: Literal["swipe", "spy", "opacity"] = Field(
        default="swipe",
        description=(
            "Comparison style. 'swipe' (vertical swiper between A and B), 'spy' "
            "(lens-style hover view of B over A), or 'opacity' (A overlaid on B with "
            "adjustable opacity). Only consulted when compare is active."
        ),
    )
    compare_value: int = Field(
        default=50,
        ge=0,
        le=100,
        description=(
            "Position of the swiper or value of the opacity overlay, integer 0–100. "
            "Only consulted when compare is active."
        ),
    )

    chart_active: bool = Field(
        default=False,
        description=(
            "Activates Worldview's charting mode (time-series of regional statistics "
            "over a drawn area). False (default) — charting OFF, no chart params "
            "emitted, all other chart_* args silently ignored. True — charting ON. "
            "When True, chart_layer is REQUIRED."
        ),
    )
    chart_layer: str | None = Field(
        default=None,
        description=("GIBS layer ID to chart. Charting supports one layer at a time. REQUIRED when chart_active=True."),
    )
    chart_area: tuple[float, float, float, float] | None = Field(
        default=None,
        description=(
            "Area-of-interest for the chart, as (x1, y1, x2, y2) in the same coordinate "
            "system as `bbox`. Statistics are computed over this region."
        ),
    )
    chart_time_start: str | date | datetime | None = Field(
        default=None,
        description="Start of the chart's time range, same accepted forms as `time`.",
    )
    chart_time_end: str | date | datetime | None = Field(
        default=None,
        description="End of the chart's time range.",
    )
    chart_autoload: bool = Field(
        default=False,
        description=(
            "If True, the chart computes and renders the moment the link is opened. "
            "Default False (user must click 'Generate Chart' in the Worldview UI)."
        ),
    )

    @field_validator("chart_layer")
    @classmethod
    def _check_chart_layer(cls, v: str | None) -> str | None:
        if v is not None:
            _reject_grammar_chars(v, "chart_layer")
        return v

    @model_validator(mode="after")
    def _enforce_feature_gates(self) -> Self:
        if self.compare_active is not None and self.compare_layers is None:
            raise ValueError(
                "compare_active is set, so compare_layers is required "
                "(cannot enable compare mode without a B-state layer list)"
            )
        if self.chart_active and self.chart_layer is None:
            raise ValueError(
                "chart_active is True, so chart_layer is required (cannot enable charting without a layer to chart)"
            )
        return self

    @model_validator(mode="after")
    def _validate_semantics(self) -> Self:
        if self.bbox is not None:
            west, south, east, north = self.bbox
            if south >= north:
                raise ValueError(f"bbox south ({south}) must be < north ({north})")
            if west == east:
                raise ValueError(f"bbox west ({west}) must differ from east ({east}); zero-width bbox is invalid")
            # west > east is allowed (antimeridian crossing in geographic projection)
            if self.projection == "geographic":
                if not (-180 <= west <= 180 and -180 <= east <= 180):
                    raise ValueError(f"bbox lon out of [-180, 180] for geographic projection: {self.bbox}")
                if not (-90 <= south <= 90 and -90 <= north <= 90):
                    raise ValueError(f"bbox lat out of [-90, 90] for geographic projection: {self.bbox}")

        if self.chart_active and self.chart_area is not None:
            x1, y1, x2, y2 = self.chart_area
            if y1 >= y2:
                raise ValueError(f"chart_area y1 ({y1}) must be < y2 ({y2})")
            if x1 == x2:
                raise ValueError(f"chart_area x1 ({x1}) must differ from x2 ({x2}); zero-width area is invalid")
            if self.projection == "geographic":
                if not (-180 <= x1 <= 180 and -180 <= x2 <= 180):
                    raise ValueError(f"chart_area lon out of [-180, 180] for geographic projection: {self.chart_area}")
                if not (-90 <= y1 <= 90 and -90 <= y2 <= 90):
                    raise ValueError(f"chart_area lat out of [-90, 90] for geographic projection: {self.chart_area}")

        if self.chart_time_start is not None and self.chart_time_end is not None:
            start = _coerce_to_datetime(self.chart_time_start)
            end = _coerce_to_datetime(self.chart_time_end)
            if start > end:
                raise ValueError(
                    f"chart_time_start ({self.chart_time_start}) must be <= chart_time_end ({self.chart_time_end})"
                )

        return self


class WorldviewPermalinkOutputSchema(OutputSchema):
    """Output schema for the Worldview Permalink Tool."""

    url: str = Field(
        ...,
        description="A complete NASA Worldview permalink URL that opens the map at the requested state.",
    )


# -----------------------------------------------------------------------------
# Tool Configuration
# -----------------------------------------------------------------------------


class WorldviewPermalinkToolConfig(BaseToolConfig):
    """Configuration for the WorldviewPermalinkTool Tool."""

    base_url: str = Field(
        default=os.getenv("WORLDVIEW_BASE_URL", DEFAULT_BASE_URL),
        description="Base URL for the NASA WORLDVIEW",
    )


# -----------------------------------------------------------------------------
# Permalink generation (mcp) Tool
# -----------------------------------------------------------------------------


@mcp_tool
class WorldviewPermalinkTool(BaseTool[WorldviewPermalinkInputSchema, WorldviewPermalinkOutputSchema]):
    """
    Build a NASA Worldview permalink URL.

    Generates a deep link to NASA Worldview (https://worldview.earthdata.nasa.gov)
    that opens the interactive map at a specific layer configuration, time,
    viewport, and (optionally) comparison or charting state. No I/O — pure URL
    string assembly.

    Use this tool after a dataset has been confirmed with the user, to produce
    the visualization link the user will open.
    p.s. The IESO Worldview agent calls this in its "Visualization Construction" and
    "Analysis Support" steps.

    Required:
    - layers: at least one LayerSpec (GIBS layer ID + optional rendering modifiers)

    Optional viewport / time:
    - projection, time, bbox, rotation — omit any to inherit Worldview's defaults

    Optional feature blocks (each gated by an _active flag; the rest of the
    block is silently ignored when the gate is off):
    - Comparison: set compare_active=True (A side) or False (B side) and
      provide compare_layers; optionally compare_time / compare_mode /
      compare_value.
    - Charting: set chart_active=True and provide chart_layer; optionally
      chart_area / chart_time_start / chart_time_end / chart_autoload.
    """

    input_schema = WorldviewPermalinkInputSchema
    output_schema = WorldviewPermalinkOutputSchema
    config_schema = WorldviewPermalinkToolConfig

    async def _arun(self, params: WorldviewPermalinkInputSchema) -> WorldviewPermalinkOutputSchema:
        return WorldviewPermalinkOutputSchema(url=self.build_url(params, self.config.base_url))

    @classmethod
    def build_url(cls, params: WorldviewPermalinkInputSchema, base_url: str = DEFAULT_BASE_URL) -> str:
        """Pure URL-string assembly from a validated input schema. No I/O.

        The schema's `_enforce_feature_gates` validator guarantees the
        compare/chart not-None invariants before this method runs, so the body
        does not re-check them.
        """
        out: dict[str, str] = {}

        layers = cls._apply_layer_preprocessing(params.layers)
        out["l"] = ",".join(cls._format_layer(s) for s in layers)

        if params.compare_active is not None:
            assert params.compare_layers is not None
            compare_layers = cls._apply_layer_preprocessing(params.compare_layers)
            out["l1"] = ",".join(cls._format_layer(s) for s in compare_layers)

        time_value = params.time if params.time is not None else (datetime.now(timezone.utc) - timedelta(days=1)).date()
        if (formatted := cls._format_time(time_value)) is not None:
            out["t"] = formatted

        if params.compare_active is not None and (formatted := cls._format_time(params.compare_time)) is not None:
            out["t1"] = formatted

        if params.bbox is not None:
            out["v"] = ",".join(cls._fmt_num(x) for x in params.bbox)

        out["p"] = params.projection

        if params.rotation is not None:
            out["r"] = cls._fmt_num(params.rotation)

        if params.compare_active is not None:
            out["ca"] = "true" if params.compare_active else "false"
            out["cm"] = params.compare_mode
            out["cv"] = str(params.compare_value)

        if params.chart_active:
            assert params.chart_layer is not None
            out["cha"] = "true"
            out["chl"] = params.chart_layer
            if params.chart_area is not None:
                out["chc"] = ",".join(cls._fmt_num(x) for x in params.chart_area)
            if (formatted := cls._format_time(params.chart_time_start)) is not None:
                out["cht"] = formatted
            if (formatted := cls._format_time(params.chart_time_end)) is not None:
                out["cht2"] = formatted
            out["chch"] = "true" if params.chart_autoload else "false"

        out["em"] = "true"
        return f"{base_url}?{urlencode(out, safe=',()=:')}"

    # -----------------------------------------------------------------------------
    # Utility static methods
    # -----------------------------------------------------------------------------

    @staticmethod
    def _fmt_num(n: float | int) -> str:
        if isinstance(n, float) and n.is_integer():
            return str(int(n))
        return str(n)

    @classmethod
    def _format_layer(cls, spec: LayerSpec) -> str:
        tokens: list[str] = []
        if spec.hidden:
            tokens.append("hidden")
        if spec.opacity is not None:
            tokens.append(f"opacity={cls._fmt_num(spec.opacity)}")
        if spec.palettes:
            tokens.append(f"palettes={','.join(spec.palettes)}")
        if spec.style is not None:
            tokens.append(f"style={spec.style}")
        if spec.min is not None:
            tokens.append(f"min={cls._fmt_num(spec.min)}")
        if spec.max is not None:
            tokens.append(f"max={cls._fmt_num(spec.max)}")
        if spec.squash:
            tokens.append("squash")
        if not tokens:
            return spec.id
        return f"{spec.id}({','.join(tokens)})"

    @staticmethod
    def _apply_layer_preprocessing(layers: list[LayerSpec]) -> list[LayerSpec]:
        """Pre-process a layer list before URL emission. Applied unconditionally.

        Three steps:
          1. Prepend the default base layer if none of the supplied layers' ids are in
             BASE_LAYERS_SET. Load-bearing — Worldview shows a black background when
             l= contains only overlays.
          2. Append default reference overlays (Coastlines_15m, Reference_Features_15m)
             that aren't already present. Provides land/water clarity + political borders.
          3. Canonical reorder: baselayers first, overlays after; user-supplied order
             preserved within each partition.

        Returns a new list; the input is not mutated.
        """
        result = list(layers)

        if not any(layer.id in BASE_LAYERS_SET for layer in result):
            result = [LayerSpec(id=DEFAULT_BASE_LAYER), *result]

        existing_ids = {layer.id for layer in result}
        for ref_id in DEFAULT_REFERENCE_OVERLAYS:
            if ref_id not in existing_ids:
                result.append(LayerSpec(id=ref_id))

        baselayers = [layer for layer in result if layer.id in BASE_LAYERS_SET]
        overlays = [layer for layer in result if layer.id not in BASE_LAYERS_SET]
        return [*baselayers, *overlays]

    @staticmethod
    def _format_time(t: str | date | datetime | None) -> str | None:
        if t is None:
            return None
        if isinstance(t, str):
            try:
                t = date_parser.parse(t)
            except (ValueError, OverflowError) as e:
                raise ValueError(f"Could not parse time {t!r}: {e}") from e
        if isinstance(t, datetime):
            if t.tzinfo is not None:
                t = t.astimezone(timezone.utc)
            if t.time() == datetime.min.time():
                return t.date().isoformat()
            return t.strftime("%Y-%m-%dT%H:%M:%SZ")
        if isinstance(t, date):
            return t.isoformat()
        raise TypeError(f"Unsupported time type: {type(t).__name__}")


if __name__ == "__main__":
    core = WorldviewPermalinkTool.build_url(
        WorldviewPermalinkInputSchema(
            layers=[LayerSpec(id="MODIS_Terra_CorrectedReflectance_TrueColor")],
            time="2025-09-15",
            bbox=(-125, 32, -114, 42),
        )
    )
    print("Core:", core)

    rich = WorldviewPermalinkTool.build_url(
        WorldviewPermalinkInputSchema(
            layers=[LayerSpec(id="MODIS_Terra_AOD", opacity=0.8)],
            time="September 15, 2025",
            bbox=(-125, 32, -114, 42),
            compare_active=True,
            compare_layers=[LayerSpec(id="MODIS_Aqua_AOD")],
            compare_time="2025-09-14",
            compare_mode="swipe",
            compare_value=60,
            chart_active=True,
            chart_layer="MODIS_Terra_AOD",
            chart_area=(-125, 32, -114, 42),
            chart_time_start="2025-09-01",
            chart_time_end="2025-09-30",
            chart_autoload=True,
        )
    )
    print("Rich:", rich)
