"""Unit tests for worldview utils module."""

from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from akd_ext.tools.worldview.utils import (
    LayerSpec,
    build_worldview_permalink,
)


def query_string(url: str) -> str:
    """Return the part of the URL after `?`."""
    return url.split("?", 1)[1]


class TestLayerFormatting:
    """LayerSpec → URL token formatting."""

    def test_layerspec_id_is_required(self):
        with pytest.raises(ValidationError):
            LayerSpec(opacity=0.5)  # type: ignore[call-arg]

    def test_all_defaults_renders_bare_id(self):
        # LAYER_X is a non-base id, so pre-processing prepends a base and appends
        # default reference overlays. LAYER_X itself still renders bare (no parens).
        url = build_worldview_permalink(layers=[LayerSpec(id="LAYER_X")])
        assert ",LAYER_X," in query_string(url)
        # No layer in the resulting list has modifiers, so no parens anywhere.
        assert "(" not in query_string(url)

    def test_hidden(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="LAYER_X", hidden=True)])
        assert "LAYER_X(hidden)" in url

    def test_opacity(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="LAYER_X", opacity=0.7)])
        assert "LAYER_X(opacity=0.7)" in url

    def test_palettes(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="LAYER_X", palettes=["red", "blue"])])
        assert "LAYER_X(palettes=red,blue)" in url

    def test_style(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="LAYER_X", style="vector_style")])
        assert "LAYER_X(style=vector_style)" in url

    def test_min_max(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="LAYER_X", min=0, max=100)])
        assert "LAYER_X(min=0,max=100)" in url

    def test_squash(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="LAYER_X", squash=True)])
        assert "LAYER_X(squash)" in url

    def test_multiple_modifiers_use_documented_token_order(self):
        # _format_layer order: hidden, opacity, palettes, style, min, max, squash
        url = build_worldview_permalink(
            layers=[
                LayerSpec(
                    id="LAYER_X",
                    hidden=True,
                    opacity=0.5,
                    palettes=["red"],
                    squash=True,
                )
            ]
        )
        assert "LAYER_X(hidden,opacity=0.5,palettes=red,squash)" in url

    def test_multiple_layers_comma_joined(self):
        # Both LAYER_A and LAYER_B are non-base; canonical reorder keeps user-supplied
        # order within the overlay partition.
        url = build_worldview_permalink(layers=[LayerSpec(id="LAYER_A"), LayerSpec(id="LAYER_B", opacity=0.5)])
        assert "LAYER_A,LAYER_B(opacity=0.5)" in url


class TestTimeFormatting:
    """Time conversion behaviour via the `time` param."""

    def test_date_emits_daily_form(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="L")], time=date(2025, 9, 15))
        assert "t=2025-09-15" in url
        assert "T" not in url.split("t=")[1].split("&")[0]

    def test_datetime_with_time_emits_subdaily(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L")],
            time=datetime(2025, 9, 15, 12, 30, 45),
        )
        assert "t=2025-09-15T12:30:45Z" in url

    def test_datetime_at_midnight_emits_daily(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L")],
            time=datetime(2025, 9, 15, 0, 0, 0),
        )
        t_segment = url.split("t=")[1].split("&")[0]
        assert t_segment == "2025-09-15"

    def test_tz_aware_datetime_normalised_to_utc(self):
        est = timezone(timedelta(hours=-5))
        dt = datetime(2025, 9, 15, 12, 0, 0, tzinfo=est)
        url = build_worldview_permalink(layers=[LayerSpec(id="L")], time=dt)
        assert "t=2025-09-15T17:00:00Z" in url

    def test_string_iso_date(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="L")], time="2025-09-15")
        assert "t=2025-09-15" in url

    def test_string_human_readable(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="L")], time="September 15, 2025")
        assert "t=2025-09-15" in url

    def test_string_slash_form(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="L")], time="2025/09/15")
        assert "t=2025-09-15" in url

    def test_string_tz_aware_iso_normalises_to_utc(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="L")], time="2025-09-15T12:00:00-05:00")
        assert "t=2025-09-15T17:00:00Z" in url

    def test_unparseable_string_raises(self):
        with pytest.raises(ValueError, match="banana"):
            build_worldview_permalink(layers=[LayerSpec(id="L")], time="banana")

    def test_none_defaults_to_yesterday_utc(self):
        # Function defaults `time` to yesterday (UTC) to avoid Worldview's
        # partially-rendered "today" scenes.
        url = build_worldview_permalink(layers=[LayerSpec(id="L")])
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
        assert f"t={yesterday}" in url


class TestCoreParams:
    """bbox, projection, rotation."""

    def test_bbox_round_trip(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L")],
            bbox=(-125, 32, -114, 42),
        )
        assert "v=-125,32,-114,42" in url

    def test_projection_default_is_geographic(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="L")])
        assert "p=geographic" in url

    def test_projection_arctic_with_rotation(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L")],
            projection="arctic",
            rotation=45,
        )
        assert "p=arctic" in url
        assert "r=45" in url

    def test_no_rotation_omits_param(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="L")])
        assert "r=" not in query_string(url)

    def test_embed_mode_always_emitted(self):
        # Embed mode is unconditional — em=true must appear on every URL so
        # the link renders cleanly in chat / iframe contexts.
        url = build_worldview_permalink(layers=[LayerSpec(id="L")])
        assert "em=true" in url


class TestCompareMode:
    """compare_active gate behaviour."""

    def test_gate_on_a_side_emits_full_block(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L_A")],
            time="2025-09-15",
            compare_active=True,
            compare_layers=[LayerSpec(id="L_B")],
            compare_time="2025-09-14",
            compare_mode="swipe",
            compare_value=50,
        )
        # B-state list is also pre-processed: base prepended, refs appended.
        assert ",L_B," in url
        assert "t1=2025-09-14" in url
        assert "ca=true" in url
        assert "cm=swipe" in url
        assert "cv=50" in url

    def test_gate_on_b_side_emits_ca_false(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L_A")],
            compare_active=False,
            compare_layers=[LayerSpec(id="L_B")],
        )
        assert "ca=false" in url
        assert ",L_B," in url

    def test_gate_off_short_circuits_stray_args(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L_A")],
            compare_active=None,
            compare_layers=[LayerSpec(id="L_B")],
            compare_time="2025-09-14",
            compare_mode="opacity",
            compare_value=80,
        )
        qs = query_string(url)
        assert "l1=" not in qs
        assert "t1=" not in qs
        assert "ca=" not in qs
        assert "cm=" not in qs
        assert "cv=" not in qs

    def test_gate_on_without_compare_layers_raises(self):
        with pytest.raises(ValueError, match="compare_layers is required"):
            build_worldview_permalink(
                layers=[LayerSpec(id="L_A")],
                compare_active=True,
                compare_layers=None,
            )

    def test_compare_time_is_optional_when_gate_on(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L_A")],
            compare_active=True,
            compare_layers=[LayerSpec(id="L_B")],
        )
        assert "ca=true" in url
        assert ",L_B," in url
        assert "t1=" not in query_string(url)


class TestChartingMode:
    """chart_active gate behaviour."""

    def test_gate_on_emits_full_block(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L")],
            chart_active=True,
            chart_layer="L_CHART",
            chart_area=(-125, 32, -114, 42),
            chart_time_start="2025-09-01",
            chart_time_end="2025-09-30",
            chart_autoload=True,
        )
        assert "cha=true" in url
        assert "chl=L_CHART" in url
        assert "chc=-125,32,-114,42" in url
        assert "cht=2025-09-01" in url
        assert "cht2=2025-09-30" in url
        assert "chch=true" in url

    def test_gate_off_short_circuits_stray_args(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L")],
            chart_active=False,
            chart_layer="L_CHART",
            chart_area=(-125, 32, -114, 42),
            chart_time_start="2025-09-01",
            chart_autoload=True,
        )
        qs = query_string(url)
        assert "cha=" not in qs
        assert "chl=" not in qs
        assert "chc=" not in qs
        assert "cht=" not in qs
        assert "cht2=" not in qs
        assert "chch=" not in qs

    def test_gate_on_without_chart_layer_raises(self):
        with pytest.raises(ValueError, match="chart_layer is required"):
            build_worldview_permalink(
                layers=[LayerSpec(id="L")],
                chart_active=True,
                chart_layer=None,
            )

    def test_chart_autoload_default_false(self):
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L")],
            chart_active=True,
            chart_layer="L_CHART",
        )
        assert "chch=false" in url


class TestLayerPreprocessing:
    """Unconditional pre-processing: auto-add base, auto-append default reference
    overlays, canonical reorder. Same logic applies to compare_layers."""

    def _layer_list(self, url: str, key: str = "l") -> list[str]:
        """Extract the comma-separated layer ids from `?<key>=...&...`."""
        return url.split(f"{key}=")[1].split("&")[0].split(",")

    @pytest.mark.parametrize(
        "base_id",
        [
            "MODIS_Terra_CorrectedReflectance_TrueColor",
            "MODIS_Aqua_CorrectedReflectance_TrueColor",
            "VIIRS_SNPP_CorrectedReflectance_TrueColor",
            "VIIRS_NOAA20_CorrectedReflectance_TrueColor",
            "VIIRS_NOAA21_CorrectedReflectance_TrueColor",
        ],
    )
    def test_known_base_layer_is_recognised(self, base_id):
        # When the user supplies any known base, no second base is auto-prepended.
        url = build_worldview_permalink(layers=[LayerSpec(id=base_id)])
        ids = self._layer_list(url)
        bases_in_url = [
            i
            for i in ids
            if i.split("(")[0]
            in {
                "MODIS_Terra_CorrectedReflectance_TrueColor",
                "MODIS_Aqua_CorrectedReflectance_TrueColor",
                "VIIRS_SNPP_CorrectedReflectance_TrueColor",
                "VIIRS_NOAA20_CorrectedReflectance_TrueColor",
                "VIIRS_NOAA21_CorrectedReflectance_TrueColor",
            }
        ]
        assert bases_in_url == [base_id]

    def test_auto_add_base_when_missing(self):
        # MODIS_Aqua_AOD is an overlay — pre-processor must prepend the default base.
        url = build_worldview_permalink(layers=[LayerSpec(id="MODIS_Aqua_AOD")])
        ids = self._layer_list(url)
        assert ids[0] == "MODIS_Terra_CorrectedReflectance_TrueColor"
        assert "MODIS_Aqua_AOD" in ids

    def test_auto_append_default_reference_overlays(self):
        url = build_worldview_permalink(layers=[LayerSpec(id="MODIS_Aqua_AOD")])
        assert "Coastlines_15m" in url
        assert "Reference_Features_15m" in url

    def test_partial_reference_overlay_already_present_only_missing_appended(self):
        # User supplies Coastlines_15m themselves; pre-processor must not duplicate it,
        # but must still append the missing Reference_Features_15m.
        url = build_worldview_permalink(layers=[LayerSpec(id="MODIS_Aqua_AOD"), LayerSpec(id="Coastlines_15m")])
        ids = self._layer_list(url)
        assert ids.count("Coastlines_15m") == 1
        assert "Reference_Features_15m" in ids

    def test_canonical_reorder_baselayers_first(self):
        # User supplies overlay before base; pre-processor moves base to front and
        # preserves user-supplied order within the overlay partition.
        url = build_worldview_permalink(
            layers=[
                LayerSpec(id="MODIS_Aqua_AOD"),  # overlay
                LayerSpec(id="VIIRS_NOAA21_CorrectedReflectance_TrueColor"),  # base
                LayerSpec(id="MODIS_Terra_AOD"),  # overlay
            ]
        )
        ids = self._layer_list(url)
        assert ids[0] == "VIIRS_NOAA21_CorrectedReflectance_TrueColor"
        assert ids.index("MODIS_Aqua_AOD") < ids.index("MODIS_Terra_AOD")
        assert "Coastlines_15m" in ids
        assert "Reference_Features_15m" in ids

    def test_compare_layers_also_get_pre_processing(self):
        # compare_layers (B-state) gets the same pre-processing as `layers`.
        url = build_worldview_permalink(
            layers=[LayerSpec(id="L_A")],
            compare_active=True,
            compare_layers=[LayerSpec(id="L_B")],
        )
        b_ids = self._layer_list(url, key="l1")
        assert b_ids[0] == "MODIS_Terra_CorrectedReflectance_TrueColor"
        assert "L_B" in b_ids
        assert "Coastlines_15m" in b_ids
        assert "Reference_Features_15m" in b_ids
