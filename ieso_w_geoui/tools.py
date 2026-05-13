"""Local AKD tools exposing the GeoUI Protocol over the Worldview adapter.

Two tools, both pure / no I/O:

- ``GeoUIRenderIntentTool`` — agent constructs a ``GeoIntent`` describing
  the desired application state; tool returns a Worldview permalink URL.
- ``GeoUIGetStateTool`` — agent passes a Worldview URL; tool returns the
  current state as a ``GeoIntent``.

Wire these into a ``PydanticAIBaseAgentConfig`` via the ``tools`` field.
The base class auto-converts AKD ``BaseTool`` instances to pydantic_ai
tools.
"""

from __future__ import annotations

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool
from pydantic import Field

from ieso_w_geoui.adapter import intent_to_url, url_to_intent
from ieso_w_geoui.core import GeoIntent


# -----------------------------------------------------------------------------
# render_intent
# -----------------------------------------------------------------------------


class GeoUIRenderIntentInputSchema(InputSchema):
    """Input for ``GeoUIRenderIntentTool``."""

    intent: GeoIntent = Field(
        ...,
        description=(
            "GeoIntent describing the desired application state. "
            "Core fields: viewport (bbox + crs), time (instant), layers (id + visible + opacity). "
            "Use extensions by adding their URI to `geoui_extensions` and including the "
            "corresponding namespaced fields: "
            "geoui:compare/v1.0.0 → compare:layers, compare:time, compare:mode, "
            "compare:value, compare:active_side; "
            "geoui:chart/v1.0.0 → chart:layer, chart:area, chart:time, chart:autoload; "
            "geoui:raster-styling/v1.0.0 → on each LayerRef: raster-styling:palettes, "
            "raster-styling:min, raster-styling:max, raster-styling:squash, raster-styling:style."
        ),
    )


class GeoUIRenderIntentOutputSchema(OutputSchema):
    """Output for ``GeoUIRenderIntentTool``."""

    url: str = Field(
        ...,
        description="Worldview permalink URL that opens the map at the requested state.",
    )


class GeoUIRenderIntentTool(BaseTool[GeoUIRenderIntentInputSchema, GeoUIRenderIntentOutputSchema]):
    """Render a GeoIntent as a NASA Worldview permalink URL.

    Use this tool to materialise the agent's intended application state
    (expressed as a GeoIntent) into a URL the user can open. The agent
    reasons in GeoIntent terms, not Worldview-specific URL params.
    """

    input_schema = GeoUIRenderIntentInputSchema
    output_schema = GeoUIRenderIntentOutputSchema

    async def _arun(self, params: GeoUIRenderIntentInputSchema) -> GeoUIRenderIntentOutputSchema:
        return GeoUIRenderIntentOutputSchema(url=intent_to_url(params.intent))


# -----------------------------------------------------------------------------
# get_state
# -----------------------------------------------------------------------------


class GeoUIGetStateInputSchema(InputSchema):
    """Input for ``GeoUIGetStateTool``."""

    url: str = Field(..., description="Worldview permalink URL to parse.")


class GeoUIGetStateOutputSchema(OutputSchema):
    """Output for ``GeoUIGetStateTool``."""

    intent: GeoIntent = Field(
        ...,
        description="GeoIntent describing the application state encoded in the URL.",
    )


class GeoUIGetStateTool(BaseTool[GeoUIGetStateInputSchema, GeoUIGetStateOutputSchema]):
    """Read the current Worldview application state as a GeoIntent.

    Use this to observe the state implied by a Worldview URL — typically
    when continuing an iterative analysis: read current state, decide
    what to change, emit a new GeoIntent via ``geoui_render_intent``.

    Auto-injected base reflectance and reference overlay layers are
    preserved in the output for fidelity; ignore them when computing
    refinements.
    """

    input_schema = GeoUIGetStateInputSchema
    output_schema = GeoUIGetStateOutputSchema

    async def _arun(self, params: GeoUIGetStateInputSchema) -> GeoUIGetStateOutputSchema:
        return GeoUIGetStateOutputSchema(intent=url_to_intent(params.url))


# -----------------------------------------------------------------------------
# Smoke test (no LLM, no MCP, no API keys required)
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    import asyncio

    from ieso_w_geoui.core import LayerRef, TimeWindow, Viewport
    from ieso_w_geoui.extensions import chart, compare, raster_styling

    async def _smoke() -> None:
        render = GeoUIRenderIntentTool()
        get_state = GeoUIGetStateTool()

        # 1) Simple: render core fields → URL → parse back to GeoIntent.
        simple = GeoIntent(
            viewport=Viewport(bbox=[-125, 32, -114, 42], crs="EPSG:4326"),
            time=TimeWindow(instant="2025-09-15"),
            layers=[LayerRef(id="MODIS_Aqua_Aerosol", opacity=0.8)],
        )
        r1 = await render.arun(GeoUIRenderIntentInputSchema(intent=simple))
        print("[1] render_intent (simple) →")
        print(f"    url: {r1.url}\n")

        s1 = await get_state.arun(GeoUIGetStateInputSchema(url=r1.url))
        print("[2] get_state (simple) →")
        print(f"    intent: {s1.intent.model_dump_json(by_alias=True, exclude_none=True, indent=2)}\n")

        # 2) Rich: all three extensions declared and populated.
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
        r2 = await render.arun(GeoUIRenderIntentInputSchema(intent=rich))
        print("[3] render_intent (compare + chart + raster-styling) →")
        print(f"    url: {r2.url}\n")

        s2 = await get_state.arun(GeoUIGetStateInputSchema(url=r2.url))
        print("[4] get_state (rich) → extensions declared:")
        for uri in s2.intent.geoui_extensions:
            print(f"    - {uri}")

    asyncio.run(_smoke())
