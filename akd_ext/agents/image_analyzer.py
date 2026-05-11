"""Generic Image Analyzer Agent.

Analyzes remote images and returns one structured :class:`FigureAnalysis` per
image.  Callers use ``agent.arun(params)`` or
``async for event in agent.astream(params)`` like any other agent.

Internally URLs are chunked by ``batch_size``, downloaded, base64-encoded, and
sent to ``responses.parse`` for structured output.  ``_astream`` yields
temporally consistent events: one starting event, per-batch partial events,
one final completed event.
"""

from __future__ import annotations

import base64
from collections.abc import AsyncIterator
from typing import Any, Literal

from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from akd._base import (
    CompletedEvent,
    CompletedEventData,
    InputSchema,
    OutputSchema,
    PartialEventData,
    PartialOutputEvent,
    RunContext,
    RunningEvent,
    StartingEvent,
    StartingEventData,
    StreamEvent,
    TextOutput,
)
from akd_ext.agents._base import OpenAIBaseAgent, OpenAIBaseAgentConfig
from akd_ext.utils import download_image_batch

__all__ = [
    "ImageAnalyzerAgent",
    "ImageAnalyzerConfig",
    "ImageAnalyzerInputSchema",
    "ImageAnalyzerOutputSchema",
]


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------


class FigureAnalysis(BaseModel):
    """Structured analysis of one image."""

    slug: str = Field(..., description="Filename slug — copy verbatim from the caption.")
    url: str = Field(default="", description="Filled programmatically; leave empty.")
    figure_type: Literal["plot", "illustration", "unknown"] = Field(default="unknown")
    description: str = Field(default="")
    x_axis: str = Field(default="", description="Axis label and visible range with units. Plots only.")
    y_axis: str = Field(default="", description="Axis label and visible range with units. Plots only.")
    legend: list[str] = Field(default_factory=list, description="Legend entries verbatim with color. Plots only.")
    caption: str = Field(default="", description="Title or caption text visible in the image.")
    notes: str = Field(default="", description="Anomalies, scale issues, suspicious data, etc.")


class _BatchOutput(BaseModel):
    """Container for ``responses.parse`` structured output."""

    analyses: list[FigureAnalysis] = Field(default_factory=list)


class ImageAnalyzerInputSchema(InputSchema):
    """Image URLs plus a free-form context paragraph."""

    urls: list[str] = Field(default_factory=list)
    context: str = Field(default="")


class ImageAnalyzerOutputSchema(OutputSchema):
    """Per-image analyses plus a Markdown summary."""

    __response_field__ = "markdown"

    analyses: list[FigureAnalysis] = Field(default_factory=list)
    markdown: str = Field(default="")


# -----------------------------------------------------------------------------
# Prompt
# -----------------------------------------------------------------------------


IMAGE_ANALYZER_SYSTEM_PROMPT = """\
You are a meticulous scientific figure analyst. The user message contains a
`Context` paragraph followed by a batch of images. Each image is followed by:

    caption: [Image slug: <slug>]

Return one `FigureAnalysis` per image.

CORE PRINCIPLE — FAITHFULNESS OVER NARRATIVE:
The Context tells you what the authors *intended* or are *studying*. The
image shows what actually happened. When they disagree, report the image.
Use Context only to resolve ambiguous labels and domain terminology — never
to override what the figure actually shows. Do not smooth, simplify, or
narrativize a figure to match the surrounding paper's framing.

STEP 1 — Identify the figure type before describing it.
Common types you will encounter:

  * line_plot: one or more curves over a continuous x-axis (time series,
    loss curves, profiles).
  * scatter_plot: discrete (x, y) points, possibly with categories.
  * bar_chart: categorical comparisons, possibly grouped or stacked.
  * histogram_or_density: distribution of a single variable (histogram,
    KDE, violin, box plot).
  * heatmap_or_matrix: 2D grid of values (confusion matrix, correlation
    matrix, attention map, generic heatmap).
  * map_or_spatial_field: geographic or 2D spatial field (lat-lon plot,
    contour map, satellite image, simulation snapshot).
  * vector_field: quiver, streamline, or flow visualization.
  * surface_or_contour: 3D surface, contour plot, phase portrait.
  * network_or_graph: nodes and edges.
  * image_or_micrograph: photograph, microscopy, experimental imagery.
  * table_image: a rendered table.
  * illustration: schematic, diagram, architecture sketch, conceptual
    figure with no quantitative axes.
  * composite: multi-panel figure mixing types — describe each panel
    according to its own type.
  * unknown: cannot determine.

Set figure_type to one of: "plot", "illustration", or "unknown" (this is
the schema-level field). Within `description`, name the specific subtype
from the list above so downstream readers know what they're getting.

STEP 2 — Write description according to figure type.

`description` has NO length limit. Write as much as the figure warrants.
Be exhaustive but precise. Quote visible values; do not invent precision.
If a number is hard to read, say "approximately." Cover everything a
reader would need to reconstruct the figure's content without seeing it.

Type-specific content requirements:

  * line_plot — for each series: starting value and x-location, ending
    value and x-location, every notable inflection (peaks, troughs,
    plateaus, regime changes, step jumps) with approximate locations and
    values, monotonicity (state explicitly if non-monotonic), noise
    character, overall change. For multi-series: which is higher/lower,
    crossings, divergences.

  * scatter_plot — number of points if estimable, overall correlation
    direction and strength, cluster structure, outliers with approximate
    locations, regression or trend line if shown, point density patterns,
    category separation if color-coded.

  * bar_chart — every bar's category and approximate value, ranking from
    largest to smallest, error bars or significance markers if present,
    grouping or stacking structure, baseline or reference if shown.

  * histogram_or_density — modality (uni/bi/multi-modal), skew, tail
    behavior, central tendency, spread, any outliers or unusual features,
    bin count if histogram, comparison between distributions if multiple
    overlaid.

  * heatmap_or_matrix — value range, where the high and low regions are,
    diagonal vs off-diagonal structure (for square matrices), notable
    rows or columns, any block structure, color scale interpretation. For
    confusion matrices: dominant diagonal entries, notable confusions.

  * map_or_spatial_field — geographic extent, where high and low values
    are located (use compass directions or named regions if identifiable),
    spatial gradients and fronts, symmetries or asymmetries, land/ocean
    or domain boundaries, contour spacing, any localized features
    (vortices, plumes, fronts).

  * vector_field — overall flow direction, convergence and divergence
    zones, vortex or saddle locations, vector magnitude variation across
    the domain.

  * surface_or_contour — topology (peaks, valleys, ridges, saddles), level
    set structure, gradient direction, monotonicity along key axes.

  * network_or_graph — number of nodes and edges if estimable, cluster or
    community structure, hub nodes, isolated components, edge weight or
    direction conventions.

  * image_or_micrograph — visible features and their spatial arrangement,
    scale bar value if present, contrast or staining patterns, regions of
    interest, annotations or arrows.

  * table_image — column headers, row labels, notable values, overall
    structure. Do not transcribe every cell unless the table is small.

  * illustration — components and their spatial arrangement, arrows and
    flow direction, labels verbatim, hierarchical structure, what process
    or system the schematic represents.

  * composite — describe each panel in turn using its own type's
    requirements, then describe cross-panel relationships and any
    apparent narrative connecting them.

STEP 3 — Fill remaining fields.

- slug: copy verbatim from the caption. Never invent or shorten.

- url: "" (filled programmatically).

- figure_type: "plot" if the figure has quantitative axes or encodes
  data values (includes maps, heatmaps, scatter, bars, histograms,
  surfaces, vector fields). "illustration" for schematics and conceptual
  diagrams. "unknown" if undetermined.

- x_axis / y_axis: axis label verbatim and visible numeric range with
  units. Fill for any figure with quantitative axes. Leave empty for
  illustrations, network diagrams, or images without axes. For maps, use
  longitude/latitude ranges.

- legend: legend entries verbatim with their visual encoding, e.g.
  ["baseline — blue solid", "ablation — orange dashed", "ground truth —
  black dotted"]. Include color, line style, or marker shape as visible.
  Leave empty if no legend.

- caption: figure title or visible caption text exactly as shown.

- notes: ONLY genuine anomalies — axis clipping, suspicious scaling,
  missing data, outliers inconsistent with the rest, suspected plotting
  bugs, legend/series mismatches, unit problems, illegible regions. Do
  NOT put primary content here — that goes in description. Empty if
  nothing anomalous.

CONSISTENCY RULE:
description and notes must not contradict. description is the canonical
narrative; notes only flags issues on top of it.

General rules:
- One entry per attached image. No skips, no inventions.
- Quote what is visible. Never fabricate values or trends.
- Unreadable image → description="image could not be read",
  figure_type="unknown", but still return the entry.
"""


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


class ImageAnalyzerConfig(OpenAIBaseAgentConfig):
    """Configuration for the Image Analyzer Agent."""

    system_prompt: str = Field(default=IMAGE_ANALYZER_SYSTEM_PROMPT)
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    batch_size: int = Field(default=10, ge=1)
    download_concurrency: int = Field(default=8, ge=1)
    download_timeout_seconds: float = Field(default=60.0, gt=0)


# -----------------------------------------------------------------------------
# Agent
# -----------------------------------------------------------------------------


class ImageAnalyzerAgent(
    OpenAIBaseAgent[ImageAnalyzerInputSchema, ImageAnalyzerOutputSchema],
):
    """Image analyzer with standard ``arun``/``astream`` semantics.

    Callers see one agent: ``StartingEvent → PartialOutputEvent* → CompletedEvent``.
    Internally URLs are chunked by ``batch_size`` and each chunk is downloaded,
    base64-encoded, and sent to ``responses.parse`` for structured output.
    """

    input_schema = ImageAnalyzerInputSchema
    output_schema = ImageAnalyzerOutputSchema | TextOutput
    config_schema = ImageAnalyzerConfig

    # -- private helpers -----------------------------------------------------

    async def _run_batch(
        self,
        items: list[dict[str, Any]],
        context: str,
        idx: int,
        total: int,
    ) -> list[FigureAnalysis]:
        """Send one batch of downloaded images to the LLM for analysis."""
        content: list[dict[str, Any]] = []
        if context:
            content.append({"type": "input_text", "text": f"## Context\n\n{context.strip()}"})
        content.append({
            "type": "input_text",
            "text": f"## Batch {idx} of {total}\n\nReturn one FigureAnalysis per attached image.",
        })
        for item in items:
            b64 = base64.b64encode(item["bytes"]).decode("ascii")
            content.append({
                "type": "input_image",
                "image_url": f"data:{item['mime']};base64,{b64}",
            })
            content.append({"type": "input_text", "text": f"caption: [Image slug: {item['slug']}]"})

        kwargs: dict[str, Any] = {}
        if self.config.reasoning_effort is not None:
            kwargs["reasoning"] = {"effort": self.config.reasoning_effort}
        try:
            resp = await AsyncOpenAI().responses.parse(
                model=self.config.model_name,
                instructions=self.config.system_prompt,
                input=[{"role": "user", "content": content}],
                text_format=_BatchOutput,
                **kwargs,
            )
        except Exception as exc:
            logger.warning(f"[ImageAnalyzer] batch {idx}/{total} LLM call failed: {exc!r}")
            return []

        parsed = resp.output_parsed
        if parsed is None:
            return []

        slug_to_url = {item["slug"]: item["url"] for item in items}
        for a in parsed.analyses:
            a.url = slug_to_url.get(a.slug, "")
        return parsed.analyses

    async def _process_batches(
        self, params: ImageAnalyzerInputSchema,
    ) -> AsyncIterator[tuple[int, int, list[FigureAnalysis]]]:
        """Dedupe, chunk, download, analyse. Yields ``(idx, total, analyses)`` per batch."""
        urls = list(dict.fromkeys(params.urls))
        bs = self.config.batch_size
        chunks = [urls[i : i + bs] for i in range(0, len(urls), bs)]

        for idx, chunk in enumerate(chunks, 1):
            items = await download_image_batch(
                chunk,
                concurrency=self.config.download_concurrency,
                timeout=self.config.download_timeout_seconds,
            )
            if not items:
                logger.warning(f"[ImageAnalyzer] batch {idx}/{len(chunks)}: all downloads failed")
                continue
            analyses = await self._run_batch(items, params.context, idx, len(chunks))
            yield idx, len(chunks), analyses

    # -- _arun ---------------------------------------------------------------

    async def _arun(
        self, params: ImageAnalyzerInputSchema, run_context: RunContext, **kwargs: Any
    ) -> ImageAnalyzerOutputSchema | TextOutput:
        if not params.urls:
            return TextOutput(content="No URLs supplied.")

        all_analyses: list[FigureAnalysis] = []
        async for _idx, _total, analyses in self._process_batches(params):
            all_analyses.extend(analyses)

        if not all_analyses:
            return TextOutput(content="No figures could be analyzed; check warnings.")

        return ImageAnalyzerOutputSchema(
            analyses=all_analyses,
            markdown=render_markdown(all_analyses, params.context),
        )

    # -- _astream: temporally consistent events ------------------------------

    async def _astream(
        self, params: ImageAnalyzerInputSchema, run_context: RunContext, **kwargs: Any
    ) -> AsyncIterator[StreamEvent]:
        class_name = self.__class__.__name__

        # 1. Starting → Running (matches base class lifecycle)
        yield StartingEvent(
            source=class_name,
            message=f"Starting {class_name}",
            data=StartingEventData[ImageAnalyzerInputSchema](params=params),
            run_context=run_context,
        )
        yield RunningEvent(
            source=class_name,
            message=f"Running {class_name}",
            run_context=run_context,
        )

        if not params.urls:
            yield CompletedEvent(
                source=class_name,
                message=f"Completed {class_name}",
                data=CompletedEventData(output=TextOutput(content="No URLs supplied.")),
                run_context=run_context,
            )
            return

        all_analyses: list[FigureAnalysis] = []

        # 2. Process each batch → emit PartialOutputEvent per batch
        async for idx, total, analyses in self._process_batches(params):
            all_analyses.extend(analyses)
            yield PartialOutputEvent(
                source=class_name,
                message=f"Batch {idx}/{total} complete",
                data=PartialEventData(
                    partial_output=ImageAnalyzerOutputSchema(
                        analyses=list(all_analyses),
                        markdown="",
                    ),
                ),
                run_context=run_context,
            )

        # 3. Single final completed event
        final = ImageAnalyzerOutputSchema(
            analyses=all_analyses,
            markdown=render_markdown(all_analyses, params.context),
        )
        yield CompletedEvent(
            source=class_name,
            message=f"Completed {class_name}",
            data=CompletedEventData(output=final),
            run_context=run_context,
        )

    def check_output(self, output) -> str | None:
        if isinstance(output, ImageAnalyzerOutputSchema) and not output.analyses:
            return "No FigureAnalysis entries returned."
        return super().check_output(output)


# -----------------------------------------------------------------------------
# Markdown renderer
# -----------------------------------------------------------------------------


def render_markdown(analyses: list[FigureAnalysis], context: str = "") -> str:
    """Render a Markdown report from a list of :class:`FigureAnalysis`."""
    parts: list[str] = ["# Image Analysis Report\n"]
    if context:
        parts.append(f"## Context\n\n{context.strip()}\n")
    parts.append(f"## Figures ({len(analyses)} total)\n")
    for i, f in enumerate(analyses, 1):
        parts.append(f"### {i}. `{f.slug}` — _{f.figure_type}_\n")
        if f.url:
            parts.append(f"![{f.slug}]({f.url})\n")
        for label, value in (
            ("Caption", f.caption),
            ("Description", f.description),
            ("X-axis", f.x_axis),
            ("Y-axis", f.y_axis),
            ("Notes", f.notes),
        ):
            if value:
                parts.append(f"**{label}:** {value}\n")
        if f.legend:
            parts.append("**Legend:**\n" + "\n".join(f"- {e}" for e in f.legend) + "\n")
    return "\n".join(parts)
