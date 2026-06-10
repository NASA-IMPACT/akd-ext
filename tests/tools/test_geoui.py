"""Tests for the GeoUI Protocol tools."""

import pytest

from akd_ext.mcp.registry import MCPToolRegistry
from akd_ext.tools.geoui import (
    GeoIntent,
    GeoUIGetStateInputSchema,
    GeoUIGetStateTool,
    GeoUIRenderIntentInputSchema,
    GeoUIRenderIntentTool,
    LayerRef,
    TimeWindow,
    Viewport,
)
from akd_ext.tools.geoui.extensions import chart, compare, raster_styling


@pytest.fixture
def simple_intent() -> GeoIntent:
    return GeoIntent(
        viewport=Viewport(bbox=[-125, 32, -114, 42], crs="EPSG:4326"),
        time=TimeWindow(instant="2025-09-15"),
        layers=[LayerRef(id="MODIS_Aqua_Aerosol", opacity=0.8)],
    )


@pytest.fixture
def rich_intent() -> GeoIntent:
    intent = GeoIntent(
        geoui_extensions=[raster_styling.URI],
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
    intent = compare.inject(
        intent,
        compare.CompareFields(
            layers=[LayerRef(id="MODIS_Aqua_Aerosol")],
            time=TimeWindow(instant="2025-09-14"),
            mode="swipe",
            value=60,
        ),
    )
    return chart.inject(
        intent,
        chart.ChartFields(
            layer="MODIS_Aqua_Aerosol",
            area=[-125, 32, -114, 42],
            time=TimeWindow(start="2025-09-01", end="2025-09-30"),
            autoload=True,
        ),
    )


class TestGeoUIRenderIntentTool:
    @pytest.mark.asyncio
    async def test_simple_intent_renders_url(self, simple_intent):
        tool = GeoUIRenderIntentTool()
        result = await tool.arun(GeoUIRenderIntentInputSchema(intent=simple_intent))
        assert result.url.startswith("https://")
        assert "MODIS_Aqua_Aerosol" in result.url
        assert "t=2025-09-15" in result.url

    @pytest.mark.asyncio
    async def test_rich_intent_renders_extension_params(self, rich_intent):
        tool = GeoUIRenderIntentTool()
        result = await tool.arun(GeoUIRenderIntentInputSchema(intent=rich_intent))
        # compare → ca/l1/t1/cm/cv, chart → cha/chl, raster-styling → palettes
        for fragment in ("ca=", "l1=", "cm=swipe", "cv=60", "cha=true", "palettes"):
            assert fragment in result.url


class TestGeoUIGetStateTool:
    @pytest.mark.asyncio
    async def test_round_trip_simple(self, simple_intent):
        render = GeoUIRenderIntentTool()
        get_state = GeoUIGetStateTool()
        rendered = await render.arun(GeoUIRenderIntentInputSchema(intent=simple_intent))
        parsed = await get_state.arun(GeoUIGetStateInputSchema(url=rendered.url))

        assert parsed.intent.viewport.bbox == simple_intent.viewport.bbox
        assert str(parsed.intent.time.instant) == "2025-09-15"
        # build_url auto-injects base reflectance / reference overlay layers,
        # so assert on membership rather than the exact layer list.
        layers_by_id = {layer.id: layer for layer in parsed.intent.layers}
        assert "MODIS_Aqua_Aerosol" in layers_by_id
        assert layers_by_id["MODIS_Aqua_Aerosol"].opacity == 0.8

    @pytest.mark.asyncio
    async def test_round_trip_declares_extensions(self, rich_intent):
        render = GeoUIRenderIntentTool()
        get_state = GeoUIGetStateTool()
        rendered = await render.arun(GeoUIRenderIntentInputSchema(intent=rich_intent))
        parsed = await get_state.arun(GeoUIGetStateInputSchema(url=rendered.url))

        declared = set(parsed.intent.geoui_extensions)
        assert {compare.URI, chart.URI, raster_styling.URI} <= declared

        cmp = compare.extract(parsed.intent)
        assert cmp is not None
        assert cmp.mode == "swipe"
        assert cmp.value == 60

        ch = chart.extract(parsed.intent)
        assert ch is not None
        assert ch.layer == "MODIS_Aqua_Aerosol"
        assert ch.autoload is True


class TestMCPRegistration:
    def test_geoui_tools_are_registered(self):
        import akd_ext.tools  # noqa: F401 — triggers @mcp_tool registration

        registered = MCPToolRegistry().get_tools()
        assert GeoUIRenderIntentTool in registered
        assert GeoUIGetStateTool in registered
