"""GeoIntent ⇄ WorldviewPermalinkInputSchema adapter.

Pure-function translation in both directions. The existing
``WorldviewPermalinkTool`` is used unchanged; this module is the only
place that knows how GeoUI core/extension fields map to Worldview's
permalink-input fields.

Public API:
  - ``intent_to_permalink_input(intent)`` — outbound (agent → app).
  - ``permalink_input_to_intent(params)`` — inbound  (app → agent).
  - ``intent_to_url(intent, base_url=None)`` — convenience: full render.
  - ``url_to_intent(url)``                    — convenience: full read.
"""

from __future__ import annotations

from akd_ext.tools.worldview.permalink import (
    DEFAULT_BASE_URL,
    LayerSpec,
    WorldviewPermalinkInputSchema,
    WorldviewPermalinkTool,
)

from ieso_w_geoui.core import GeoIntent, LayerRef, TimeWindow, Viewport
from ieso_w_geoui.extensions import chart, compare, raster_styling
from ieso_w_geoui.url_parser import parse_url

# CRS ↔ Worldview projection name. The geographic / arctic / antarctic
# projection literals are Worldview's own three-state.
CRS_TO_WORLDVIEW_PROJECTION: dict[str, str] = {
    "EPSG:4326": "geographic",
    "EPSG:3413": "arctic",
    "EPSG:3031": "antarctic",
}
WORLDVIEW_PROJECTION_TO_CRS: dict[str, str] = {v: k for k, v in CRS_TO_WORLDVIEW_PROJECTION.items()}


def _layer_ref_to_layer_spec(layer: LayerRef) -> LayerSpec:
    """LayerRef (+ optional raster-styling extras) → LayerSpec."""
    styling = raster_styling.extract(layer)
    return LayerSpec(
        id=layer.id,
        hidden=not layer.visible,
        opacity=layer.opacity,
        palettes=styling.palettes if styling else None,
        style=styling.style if styling else None,
        min=styling.min if styling else None,
        max=styling.max if styling else None,
        squash=bool(styling.squash) if styling else False,
    )


def _layer_spec_to_layer_ref(spec: LayerSpec, *, declare_styling: bool) -> LayerRef:
    """LayerSpec → LayerRef.

    Adds ``raster-styling:*`` extras only if ``declare_styling`` is True
    (i.e. the GeoIntent will also declare the raster-styling URI).
    """
    base: dict = {
        "id": spec.id,
        "visible": not spec.hidden,
        "opacity": spec.opacity,
    }
    if declare_styling:
        if spec.palettes is not None:
            base["raster-styling:palettes"] = spec.palettes
        if spec.style is not None:
            base["raster-styling:style"] = spec.style
        if spec.min is not None:
            base["raster-styling:min"] = spec.min
        if spec.max is not None:
            base["raster-styling:max"] = spec.max
        if spec.squash:
            base["raster-styling:squash"] = True
    return LayerRef.model_validate(base)


def _time_to_instant(t: TimeWindow | None):
    """Coerce a TimeWindow to the single instant Worldview's main map accepts.

    Raises if the window is a range — Worldview's ``t`` parameter is an
    instant; ranges belong on the chart extension.
    """
    if t is None:
        return None
    if t.instant is not None:
        return t.instant
    if t.start is not None or t.end is not None:
        raise ValueError("Worldview main-map time accepts an instant, not a range")
    return None


def intent_to_permalink_input(intent: GeoIntent) -> WorldviewPermalinkInputSchema:
    """GeoIntent → WorldviewPermalinkInputSchema.

    Mapping:
      - viewport.bbox → bbox
      - viewport.crs  → projection (via CRS_TO_WORLDVIEW_PROJECTION)
      - time.instant  → time
      - layers        → layers (with raster-styling per-layer extras)
      - compare:*     → compare_*
      - chart:*       → chart_*
    """
    if intent.viewport.crs not in CRS_TO_WORLDVIEW_PROJECTION:
        raise ValueError(
            f"Worldview adapter does not support CRS {intent.viewport.crs!r}. "
            f"Supported: {sorted(CRS_TO_WORLDVIEW_PROJECTION)}"
        )
    projection = CRS_TO_WORLDVIEW_PROJECTION[intent.viewport.crs]

    fields: dict = {
        "layers": [_layer_ref_to_layer_spec(layer) for layer in intent.layers],
        "projection": projection,
        "time": _time_to_instant(intent.time),
        "bbox": intent.viewport.bbox,
    }

    cmp = compare.extract(intent)
    if cmp is not None:
        fields["compare_active"] = cmp.active_side == "A"
        fields["compare_layers"] = [_layer_ref_to_layer_spec(layer) for layer in cmp.layers]
        fields["compare_time"] = _time_to_instant(cmp.time)
        fields["compare_mode"] = cmp.mode
        fields["compare_value"] = cmp.value

    ch = chart.extract(intent)
    if ch is not None:
        fields["chart_active"] = True
        fields["chart_layer"] = ch.layer
        if ch.area is not None:
            fields["chart_area"] = ch.area
        if ch.time is not None:
            fields["chart_time_start"] = ch.time.start
            fields["chart_time_end"] = ch.time.end
        fields["chart_autoload"] = ch.autoload

    return WorldviewPermalinkInputSchema(**fields)


def permalink_input_to_intent(params: WorldviewPermalinkInputSchema) -> GeoIntent:
    """WorldviewPermalinkInputSchema → GeoIntent.

    Declares ``raster-styling``, ``compare``, ``chart`` extension URIs
    when their corresponding fields are populated.
    """
    all_layers: list[LayerSpec] = list(params.layers) + list(params.compare_layers or [])
    needs_styling = any(
        layer.palettes is not None
        or layer.style is not None
        or layer.min is not None
        or layer.max is not None
        or layer.squash
        for layer in all_layers
    )

    extensions: list[str] = []
    if needs_styling:
        extensions.append(raster_styling.URI)

    crs = WORLDVIEW_PROJECTION_TO_CRS.get(params.projection, "EPSG:4326")
    viewport = Viewport(bbox=params.bbox, crs=crs)
    time = TimeWindow(instant=params.time) if params.time is not None else None
    layers = [_layer_spec_to_layer_ref(layer, declare_styling=needs_styling) for layer in params.layers]

    intent = GeoIntent(
        geoui_extensions=extensions,
        viewport=viewport,
        time=time,
        layers=layers,
    )

    if params.compare_active is not None:
        cmp_layers = [
            _layer_spec_to_layer_ref(layer, declare_styling=needs_styling) for layer in (params.compare_layers or [])
        ]
        cmp_fields = compare.CompareFields(
            layers=cmp_layers,
            active_side="A" if params.compare_active else "B",
            time=TimeWindow(instant=params.compare_time) if params.compare_time is not None else None,
            mode=params.compare_mode,
            value=params.compare_value,
        )
        intent = compare.inject(intent, cmp_fields)

    if params.chart_active:
        assert params.chart_layer is not None, "chart_active=True implies chart_layer per schema validators"
        ch_time = None
        if params.chart_time_start is not None or params.chart_time_end is not None:
            ch_time = TimeWindow(start=params.chart_time_start, end=params.chart_time_end)
        ch_fields = chart.ChartFields(
            layer=params.chart_layer,
            area=params.chart_area,
            time=ch_time,
            autoload=params.chart_autoload,
        )
        intent = chart.inject(intent, ch_fields)

    return intent


def intent_to_url(intent: GeoIntent, base_url: str = DEFAULT_BASE_URL) -> str:
    """GeoIntent → Worldview permalink URL (convenience wrapper)."""
    params = intent_to_permalink_input(intent)
    return WorldviewPermalinkTool.build_url(params, base_url)


def url_to_intent(url: str) -> GeoIntent:
    """Worldview permalink URL → GeoIntent (convenience wrapper)."""
    return permalink_input_to_intent(parse_url(url))


if __name__ == "__main__":
    # Round-trip smoke test.
    sample = GeoIntent(
        viewport=Viewport(bbox=[-125, 32, -114, 42], crs="EPSG:4326"),
        time=TimeWindow(instant="2025-09-15"),
        layers=[
            LayerRef(id="MODIS_Terra_CorrectedReflectance_TrueColor"),
            LayerRef(id="MODIS_Aqua_Aerosol", opacity=0.8),
        ],
    )

    url = intent_to_url(sample)
    print("Outbound URL:")
    print(" ", url)

    print("\nInbound (parsed back):")
    parsed = url_to_intent(url)
    print(" ", parsed.model_dump_json(by_alias=True, exclude_none=True, indent=2))

    # Rich case: compare + chart + raster-styling.
    rich = GeoIntent(
        geoui_extensions=[compare.URI, chart.URI, raster_styling.URI],
        viewport=Viewport(bbox=[-125, 32, -114, 42], crs="EPSG:4326"),
        time=TimeWindow(instant="2025-09-15"),
        layers=[
            LayerRef.model_validate(
                {
                    "id": "MODIS_Aqua_Aerosol",
                    "opacity": 0.8,
                    "raster-styling:palettes": ["red_1"],
                    "raster-styling:min": 0,
                    "raster-styling:max": 2,
                    "raster-styling:squash": True,
                }
            )
        ],
    )
    rich = compare.inject(
        rich,
        compare.CompareFields(
            layers=[LayerRef(id="MODIS_Aqua_Aerosol")],
            time=TimeWindow(instant="2025-09-14"),
            mode="swipe",
            value=60,
        ),
    )
    rich = chart.inject(
        rich,
        chart.ChartFields(
            layer="MODIS_Aqua_Aerosol",
            area=[-125, 32, -114, 42],
            time=TimeWindow(start="2025-09-01", end="2025-09-30"),
            autoload=True,
        ),
    )

    rich_url = intent_to_url(rich)
    print("\nRich outbound URL:")
    print(" ", rich_url)
