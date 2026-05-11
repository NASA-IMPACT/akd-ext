"""Unit tests for the WorldviewPermalinkTool wrapper."""

import pytest
from pydantic import ValidationError

from akd_ext.tools.worldview import (
    LayerSpec,
    WorldviewPermalinkInputSchema,
    WorldviewPermalinkOutputSchema,
    WorldviewPermalinkTool,
)


class TestWorldviewPermalinkTool:
    """Tool-level behaviour: input schema validation and _arun delegation."""

    async def test_arun_returns_output_schema_with_url(self):
        tool = WorldviewPermalinkTool()
        result = await tool.arun(
            WorldviewPermalinkInputSchema(
                layers=[LayerSpec(id="MODIS_Terra_CorrectedReflectance_TrueColor")],
                time="2025-09-15",
                bbox=(-125, 32, -114, 42),
            )
        )
        assert isinstance(result, WorldviewPermalinkOutputSchema)
        assert result.url.startswith("https://worldview.earthdata.nasa.gov/?")
        assert "l=MODIS_Terra_CorrectedReflectance_TrueColor" in result.url
        assert "t=2025-09-15" in result.url
        assert "v=-125,32,-114,42" in result.url

    async def test_arun_compare_block(self):
        tool = WorldviewPermalinkTool()
        result = await tool.arun(
            WorldviewPermalinkInputSchema(
                layers=[LayerSpec(id="L_A")],
                compare_active=True,
                compare_layers=[LayerSpec(id="L_B")],
                compare_time="2025-09-14",
                compare_mode="spy",
                compare_value=70,
            )
        )
        assert "ca=true" in result.url
        assert "cm=spy" in result.url
        assert "cv=70" in result.url
        # B-state list is pre-processed: base prepended, refs appended.
        assert ",L_B," in result.url
        assert "t1=2025-09-14" in result.url

    async def test_arun_chart_block(self):
        tool = WorldviewPermalinkTool()
        result = await tool.arun(
            WorldviewPermalinkInputSchema(
                layers=[LayerSpec(id="L")],
                chart_active=True,
                chart_layer="L_CHART",
                chart_area=(-125, 32, -114, 42),
                chart_time_start="2025-09-01",
                chart_time_end="2025-09-30",
                chart_autoload=True,
            )
        )
        assert "cha=true" in result.url
        assert "chl=L_CHART" in result.url
        assert "chc=-125,32,-114,42" in result.url
        assert "cht=2025-09-01" in result.url
        assert "cht2=2025-09-30" in result.url
        assert "chch=true" in result.url


class TestSchemaValidation:
    """Cross-field gate constraints enforced by model_validator."""

    def test_compare_active_without_compare_layers_rejected(self):
        with pytest.raises(ValidationError, match="compare_layers is required"):
            WorldviewPermalinkInputSchema(
                layers=[LayerSpec(id="L")],
                compare_active=True,
                compare_layers=None,
            )

    def test_chart_active_without_chart_layer_rejected(self):
        with pytest.raises(ValidationError, match="chart_layer is required"):
            WorldviewPermalinkInputSchema(
                layers=[LayerSpec(id="L")],
                chart_active=True,
                chart_layer=None,
            )

    def test_compare_value_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            WorldviewPermalinkInputSchema(
                layers=[LayerSpec(id="L")],
                compare_active=True,
                compare_layers=[LayerSpec(id="LB")],
                compare_value=150,
            )

    def test_minimal_input_validates(self):
        # Just layers — no compare, no chart, no extras
        schema = WorldviewPermalinkInputSchema(layers=[LayerSpec(id="L")])
        assert schema.compare_active is None
        assert schema.chart_active is False
        assert schema.projection == "geographic"


class TestGrammarCharRejection:
    """Reject ',', '(', ')' anywhere they would corrupt the layer-list grammar."""

    @pytest.mark.parametrize("bad_id", ["MODIS,Aqua", "A(B)", "A(", "A)", "X,Y,Z"])
    def test_layer_id_with_grammar_char_rejected(self, bad_id):
        with pytest.raises(ValidationError, match="forbidden character"):
            LayerSpec(id=bad_id)

    @pytest.mark.parametrize("bad_style", ["dashed,thick", "fancy(thing)", "a)b"])
    def test_layer_style_with_grammar_char_rejected(self, bad_style):
        with pytest.raises(ValidationError, match="forbidden character"):
            LayerSpec(id="L", style=bad_style)

    @pytest.mark.parametrize("bad_palette", ["red,blue", "p(1)", "x)"])
    def test_palette_item_with_grammar_char_rejected(self, bad_palette):
        with pytest.raises(ValidationError, match="forbidden character"):
            LayerSpec(id="L", palettes=[bad_palette])

    def test_chart_layer_with_grammar_char_rejected(self):
        with pytest.raises(ValidationError, match="forbidden character"):
            WorldviewPermalinkInputSchema(
                layers=[LayerSpec(id="L")],
                chart_active=True,
                chart_layer="X(Y)",
            )

    def test_safe_strings_accepted(self):
        # Realistic GIBS-shaped IDs must not trip the validator.
        spec = LayerSpec(
            id="MODIS_Terra_CorrectedReflectance_TrueColor",
            style="dashed",
            palettes=["red_blue", "viridis"],
        )
        assert spec.id == "MODIS_Terra_CorrectedReflectance_TrueColor"
        assert spec.style == "dashed"
        assert spec.palettes == ["red_blue", "viridis"]


class TestFieldBounds:
    """Field-level numeric bounds added alongside the validators."""

    @pytest.mark.parametrize("bad_opacity", [-0.1, 1.1, 2.0])
    def test_opacity_out_of_range_rejected(self, bad_opacity):
        with pytest.raises(ValidationError):
            LayerSpec(id="L", opacity=bad_opacity)

    @pytest.mark.parametrize("good_opacity", [0.0, 0.5, 1.0])
    def test_opacity_in_range_accepted(self, good_opacity):
        spec = LayerSpec(id="L", opacity=good_opacity)
        assert spec.opacity == good_opacity

    @pytest.mark.parametrize("bad_rotation", [-200, 200, 360])
    def test_rotation_out_of_range_rejected(self, bad_rotation):
        with pytest.raises(ValidationError):
            WorldviewPermalinkInputSchema(layers=[LayerSpec(id="L")], rotation=bad_rotation)

    @pytest.mark.parametrize("good_rotation", [-180, 0, 180])
    def test_rotation_in_range_accepted(self, good_rotation):
        schema = WorldviewPermalinkInputSchema(layers=[LayerSpec(id="L")], rotation=good_rotation)
        assert schema.rotation == good_rotation


class TestBboxValidation:
    """bbox ordering, geographic-projection bounds, antimeridian carve-out, polar-projection skip."""

    def test_zero_width_bbox_rejected(self):
        with pytest.raises(ValidationError, match="zero-width bbox"):
            WorldviewPermalinkInputSchema(layers=[LayerSpec(id="L")], bbox=(10.0, 0.0, 10.0, 5.0))

    def test_inverted_latitude_rejected(self):
        with pytest.raises(ValidationError, match="south .* must be < north"):
            WorldviewPermalinkInputSchema(layers=[LayerSpec(id="L")], bbox=(-10.0, 20.0, 10.0, 0.0))

    def test_antimeridian_crossing_accepted(self):
        # Pacific-spanning bbox: west (170) > east (-170) is valid in geographic.
        schema = WorldviewPermalinkInputSchema(layers=[LayerSpec(id="L")], bbox=(170.0, -10.0, -170.0, 10.0))
        assert schema.bbox == [170.0, -10.0, -170.0, 10.0]

    def test_lon_out_of_range_rejected_for_geographic(self):
        with pytest.raises(ValidationError, match="bbox lon out of"):
            WorldviewPermalinkInputSchema(layers=[LayerSpec(id="L")], bbox=(-200.0, 0.0, 0.0, 10.0))

    def test_lat_out_of_range_rejected_for_geographic(self):
        with pytest.raises(ValidationError, match="bbox lat out of"):
            WorldviewPermalinkInputSchema(layers=[LayerSpec(id="L")], bbox=(-10.0, -100.0, 10.0, 0.0))

    @pytest.mark.parametrize("projection", ["arctic", "antarctic"])
    def test_polar_projection_skips_lonlat_bounds(self, projection):
        # Same out-of-lonlat-range bbox is accepted for polar projections (those use projected meters).
        schema = WorldviewPermalinkInputSchema(
            layers=[LayerSpec(id="L")],
            projection=projection,
            bbox=(-4_000_000.0, -4_000_000.0, 4_000_000.0, 4_000_000.0),
        )
        assert schema.projection == projection

    @pytest.mark.parametrize("projection", ["arctic", "antarctic"])
    def test_polar_projection_still_enforces_ordering(self, projection):
        with pytest.raises(ValidationError, match="south .* must be < north"):
            WorldviewPermalinkInputSchema(
                layers=[LayerSpec(id="L")],
                projection=projection,
                bbox=(-1000.0, 1000.0, 1000.0, -1000.0),
            )


class TestChartAreaValidation:
    """chart_area follows the same rules as bbox; only consulted when chart_active."""

    def _base(self, **overrides):
        params = dict(
            layers=[LayerSpec(id="L")],
            chart_active=True,
            chart_layer="L",
        )
        params.update(overrides)
        return params

    def test_zero_width_chart_area_rejected(self):
        with pytest.raises(ValidationError, match="zero-width area"):
            WorldviewPermalinkInputSchema(**self._base(chart_area=(10.0, 0.0, 10.0, 5.0)))

    def test_inverted_y_rejected(self):
        with pytest.raises(ValidationError, match="y1 .* must be < y2"):
            WorldviewPermalinkInputSchema(**self._base(chart_area=(-10.0, 20.0, 10.0, 0.0)))

    def test_lon_out_of_range_rejected_for_geographic(self):
        with pytest.raises(ValidationError, match="chart_area lon out of"):
            WorldviewPermalinkInputSchema(**self._base(chart_area=(-200.0, 0.0, 0.0, 10.0)))

    def test_chart_area_ignored_when_chart_inactive(self):
        # When chart_active is False, chart_area validation is skipped — only emission is gated.
        schema = WorldviewPermalinkInputSchema(
            layers=[LayerSpec(id="L")],
            chart_active=False,
            chart_area=(10.0, 0.0, 10.0, 5.0),  # would be rejected if chart_active=True
        )
        assert schema.chart_active is False


class TestChartTimeOrdering:
    """chart_time_start <= chart_time_end when both are supplied."""

    def _base(self, **overrides):
        params = dict(layers=[LayerSpec(id="L")], chart_active=True, chart_layer="L")
        params.update(overrides)
        return params

    def test_inverted_chart_time_rejected(self):
        with pytest.raises(ValidationError, match="chart_time_start .* must be <="):
            WorldviewPermalinkInputSchema(**self._base(chart_time_start="2025-09-30", chart_time_end="2025-09-01"))

    def test_equal_chart_time_accepted(self):
        schema = WorldviewPermalinkInputSchema(**self._base(chart_time_start="2025-09-15", chart_time_end="2025-09-15"))
        assert schema.chart_time_start == "2025-09-15"

    def test_ordered_chart_time_accepted(self):
        schema = WorldviewPermalinkInputSchema(**self._base(chart_time_start="2025-09-01", chart_time_end="2025-09-30"))
        assert schema.chart_time_end == "2025-09-30"

    def test_one_sided_chart_time_skipped(self):
        # Only one of (start, end) supplied — order check is skipped.
        schema = WorldviewPermalinkInputSchema(**self._base(chart_time_start="2025-09-15"))
        assert schema.chart_time_end is None
