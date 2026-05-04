from datetime import date, datetime, timedelta, timezone
from typing import Literal
from urllib.parse import urlencode

from dateutil import parser as date_parser
from pydantic import BaseModel, Field


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


def _fmt_num(n: float | int) -> str:
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return str(n)


def _format_layer(spec: LayerSpec) -> str:
    tokens: list[str] = []
    if spec.hidden:
        tokens.append("hidden")
    if spec.opacity is not None:
        tokens.append(f"opacity={_fmt_num(spec.opacity)}")
    if spec.palettes:
        tokens.append(f"palettes={','.join(spec.palettes)}")
    if spec.style is not None:
        tokens.append(f"style={spec.style}")
    if spec.min is not None:
        tokens.append(f"min={_fmt_num(spec.min)}")
    if spec.max is not None:
        tokens.append(f"max={_fmt_num(spec.max)}")
    if spec.squash:
        tokens.append("squash")
    if not tokens:
        return spec.id
    return f"{spec.id}({','.join(tokens)})"


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


def build_worldview_permalink(
    layers: list[LayerSpec],
    projection: Literal["geographic", "arctic", "antarctic"] = "geographic",
    base_url: str = "https://worldview.earthdata.nasa.gov/",
    time: str | date | datetime | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    rotation: float | None = None,
    *,
    compare_active: bool | None = None,
    compare_layers: list[LayerSpec] | None = None,
    compare_time: str | date | datetime | None = None,
    compare_mode: Literal["swipe", "spy", "opacity"] = "swipe",
    compare_value: int = 50,
    chart_active: bool = False,
    chart_layer: str | None = None,
    chart_area: tuple[float, float, float, float] | None = None,
    chart_time_start: str | date | datetime | None = None,
    chart_time_end: str | date | datetime | None = None,
    chart_autoload: bool = False,
) -> str:
    """Build a NASA Worldview permalink URL.

    Generates a deep link to NASA Worldview that opens the map at a specific
    layer configuration, time, viewport, and (optionally) compare or charting
    state. Pure URL string assembly — no I/O.

    Every URL is emitted in embed mode (`em=true`), which strips Worldview's
    side panels and header chrome for clean rendering in chat/iframe contexts.

    This function is the underlying implementation for a future
    WorldviewPermalinkTool; parameter descriptions here are written as
    agent-facing guidance and will map 1:1 to Pydantic Field descriptions on
    the tool's input schema.

    Args:
        layers: One or more LayerSpec instances, in render order (top of
            stack last). Each LayerSpec carries a GIBS layer ID plus
            optional per-layer modifiers (hidden, opacity, palettes, style,
            min/max, squash). REQUIRED — at least one layer must be supplied.
        projection: Map projection. Use 'geographic' for global Mercator (the
            default), 'arctic' for north polar stereographic, or 'antarctic'
            for south polar stereographic.
        base_url: Worldview base URL. Override only for testing or alternate
            deployments; default is the canonical production URL.
        time: Map time. Accepts a date (daily resolution), a datetime
            (subdaily, normalised to UTC), or a string in any reasonable
            date/datetime format — ISO 8601, 'Sep 15, 2025', '2025/09/15',
            TZ-aware forms, etc. (parsed via dateutil). If None, defaults
            to yesterday (UTC) — Worldview's own "today" default can show
            partially-rendered scenes because daily MODIS/VIIRS data is
            still being ingested into GIBS; yesterday guarantees a
            fully-rendered scene. Pass an explicit `date.today()` if the
            partial today behaviour is what you want. Note: ambiguous
            slash-separated strings like '01/02/2025' are interpreted as
            month/day/year by default; pass an unambiguous form
            ('2025-01-02') or a date object if the order matters.
        bbox: Map viewport extent as (west, south, east, north). Degrees
            for the geographic projection; projected meters for arctic/
            antarctic. If None, Worldview opens at its default global extent.
        rotation: Map rotation in degrees, range -180 to 180. Honored only
            by arctic/antarctic projections; ignored by geographic.

        compare_active: Activates Worldview's compare mode (side-by-side or
            overlay of two layer states). Tri-state:
              * None (default) — compare mode OFF; no compare params emitted
                and any other compare_* args are silently ignored.
              * True — compare mode ON with the A state shown as active.
              * False — compare mode ON with the B state shown as active.
            Maps to the URL `ca` param (None → omit; True → ca=true; False
            → ca=false).
        compare_layers: LayerSpec instances for the B state, same shape as
            `layers`. REQUIRED when compare_active is not None; raises
            ValueError if missing.
        compare_time: Time for the B state, same accepted forms as `time`.
            Optional even when compare is on; if omitted, the B state uses
            the same time as the A state.
        compare_mode: Comparison style. 'swipe' (vertical swiper between A
            and B), 'spy' (lens-style hover view of B over A), or 'opacity'
            (A overlaid on B with adjustable opacity). Only consulted when
            compare is active. Default 'swipe' matches Worldview's default.
        compare_value: Position of the swiper or value of the opacity
            overlay, integer 0–100. Only consulted when compare is active.
            Default 50.

        chart_active: Activates Worldview's charting mode (time-series of
            regional statistics over a drawn area). False (default) →
            charting OFF; no chart params emitted and any other chart_* args
            are silently ignored. True → charting ON; emits cha=true.
        chart_layer: GIBS layer ID to chart. Charting supports one layer
            at a time. REQUIRED when chart_active=True; raises ValueError
            if missing.
        chart_area: Area-of-interest for the chart, as
            (x1, y1, x2, y2) in the same coordinate system as `bbox`.
            Statistics are computed over this region.
        chart_time_start: Start of the chart's time range, same accepted
            forms as `time`. Maps to the URL `cht` param.
        chart_time_end: End of the chart's time range. Maps to the URL
            `cht2` param.
        chart_autoload: If True, the chart computes and renders the moment
            the link is opened. Default False (user must click "Generate
            Chart" in the Worldview UI).

    Returns:
        A complete Worldview permalink URL string.

    Raises:
        ValueError: If compare_active is not None but compare_layers is None.
        ValueError: If chart_active is True but chart_layer is None.

    Examples:
        Core layer + time + bbox::

            url = build_worldview_permalink(
                layers=[LayerSpec(id="MODIS_Terra_CorrectedReflectance_TrueColor")],
                time="2025-09-15",
                bbox=(-125, 32, -114, 42),
            )

        Custom opacity on one layer, compare mode A active, swipe at 60%::

            url = build_worldview_permalink(
                layers=[LayerSpec(id="MODIS_Terra_AOD", opacity=0.8)],
                compare_active=True,
                compare_layers=[LayerSpec(id="MODIS_Aqua_AOD")],
                compare_time="2025-09-14",
                compare_mode="swipe",
                compare_value=60,
            )

        Charting (time series over a region)::

            url = build_worldview_permalink(
                layers=[LayerSpec(id="VIIRS_SNPP_AOD")],
                chart_active=True,
                chart_layer="VIIRS_SNPP_AOD",
                chart_area=(-125, 32, -114, 42),
                chart_time_start="2025-09-01",
                chart_time_end="2025-09-30",
                chart_autoload=True,
            )
    """
    params: dict[str, str] = {}

    params["l"] = ",".join(_format_layer(s) for s in layers)

    if compare_active is not None:
        if compare_layers is None:
            raise ValueError(
                "compare_active is set, so compare_layers is required "
                "(cannot enable compare mode without a B-state layer list)"
            )
        params["l1"] = ",".join(_format_layer(s) for s in compare_layers)

    if time is None:
        time = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    if (formatted := _format_time(time)) is not None:
        params["t"] = formatted

    if compare_active is not None:
        if (formatted := _format_time(compare_time)) is not None:
            params["t1"] = formatted

    if bbox is not None:
        params["v"] = ",".join(_fmt_num(x) for x in bbox)

    params["p"] = projection

    if rotation is not None:
        params["r"] = _fmt_num(rotation)

    if compare_active is not None:
        params["ca"] = "true" if compare_active else "false"
        params["cm"] = compare_mode
        params["cv"] = str(compare_value)

    if chart_active:
        if chart_layer is None:
            raise ValueError(
                "chart_active is True, so chart_layer is required (cannot enable charting without a layer to chart)"
            )
        params["cha"] = "true"
        params["chl"] = chart_layer
        if chart_area is not None:
            params["chc"] = ",".join(_fmt_num(x) for x in chart_area)
        if (formatted := _format_time(chart_time_start)) is not None:
            params["cht"] = formatted
        if (formatted := _format_time(chart_time_end)) is not None:
            params["cht2"] = formatted
        params["chch"] = "true" if chart_autoload else "false"

    params["em"] = "true"

    return f"{base_url}?{urlencode(params, safe=',()=:')}"


if __name__ == "__main__":
    core = build_worldview_permalink(
        layers=[LayerSpec(id="MODIS_Terra_CorrectedReflectance_TrueColor")],
        time="2025-09-15",
        bbox=(-125, 32, -114, 42),
    )
    print("Core:", core)

    rich = build_worldview_permalink(
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
    print("Rich:", rich)
