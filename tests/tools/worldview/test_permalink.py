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
