"""AKD Tool for the NASA Worldview permalink builder.

Wraps `build_worldview_permalink` from `utils.py` as a `BaseTool`. Field descriptions on the input
schema are written as agent-facing guidance and mirror the docstring of the
underlying function.
"""

import os
from datetime import date, datetime
from typing import Literal, Self

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field, model_validator

from akd_ext.mcp import mcp_tool
from akd_ext.tools.worldview.utils import LayerSpec, build_worldview_permalink


class WorldviewPermalinkToolConfig(BaseToolConfig):
    """Configuration for the WorldviewPermalinkTool Tool."""

    base_url: str = Field(
        default=os.getenv("WORLDVIEW_BASE_URL", "https://worldview.earthdata.nasa.gov/"),
        description="Base URL for the NASA WORLDVIEW",
    )


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
            "dateutil). If None, Worldview defaults to today. Note: ambiguous "
            "slash-separated strings like '01/02/2025' are interpreted as month/day/year "
            "by default; pass an unambiguous form ('2025-01-02') if the order matters."
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


class WorldviewPermalinkOutputSchema(OutputSchema):
    """Output schema for the Worldview Permalink Tool."""

    url: str = Field(
        ...,
        description="A complete NASA Worldview permalink URL that opens the map at the requested state.",
    )


@mcp_tool
class WorldviewPermalinkTool(BaseTool[WorldviewPermalinkInputSchema, WorldviewPermalinkOutputSchema]):
    """
    Build a NASA Worldview permalink URL.

    Generates a deep link to NASA Worldview (https://worldview.earthdata.nasa.gov)
    that opens the interactive map at a specific layer configuration, time,
    viewport, and (optionally) comparison or charting state. No I/O — pure URL
    string assembly.

    Use this tool after a dataset has been confirmed with the user, to produce
    the visualization link the user will open. The IESO Worldview agent calls
    this in its "Visualization Construction" and "Analysis Support" steps.

    Required:
    - layers: at least one LayerSpec (GIBS layer ID + optional rendering modifiers)

    Optional viewport / time:
    - projection, time, bbox, rotation — omit any to inherit Worldview's defaults

    Optional feature blocks (each gated by an _active flag; the rest of the
    block is silently ignored when the gate is off):
    - Comparison: set compare_active=True (A side) or False (B side) and
      provide compare_layers; optionally compare_time / compare_mode /
      compare_value. TODO: make this a boolean on and off.
    - Charting: set chart_active=True and provide chart_layer; optionally
      chart_area / chart_time_start / chart_time_end / chart_autoload.
    """

    input_schema = WorldviewPermalinkInputSchema
    output_schema = WorldviewPermalinkOutputSchema
    config_schema = WorldviewPermalinkToolConfig

    async def _arun(self, params: WorldviewPermalinkInputSchema) -> WorldviewPermalinkOutputSchema:
        url = build_worldview_permalink(
            base_url=self.config.base_url,
            layers=params.layers,
            projection=params.projection,
            time=params.time,
            bbox=params.bbox,
            rotation=params.rotation,
            compare_active=params.compare_active,
            compare_layers=params.compare_layers,
            compare_time=params.compare_time,
            compare_mode=params.compare_mode,
            compare_value=params.compare_value,
            chart_active=params.chart_active,
            chart_layer=params.chart_layer,
            chart_area=params.chart_area,
            chart_time_start=params.chart_time_start,
            chart_time_end=params.chart_time_end,
            chart_autoload=params.chart_autoload,
        )
        # validate the url, throw proper error
        return WorldviewPermalinkOutputSchema(url=url)
