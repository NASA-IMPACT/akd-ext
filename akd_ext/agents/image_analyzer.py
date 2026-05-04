"""Generic Image Analyzer Agent.

Analyzes remote images and returns one structured :class:`FigureAnalysis` per
image.  The agent class is a zero-override config holder (like ``GapAgent``).
All orchestration — downloading, batching, calling ``responses.parse`` — lives
in the external :func:`analyze_image_urls` helper.
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any, Literal

from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from akd._base import InputSchema, OutputSchema, TextOutput
from akd_ext.agents._base import OpenAIBaseAgent, OpenAIBaseAgentConfig
from akd_ext.utils import download_images

__all__ = [
    "FigureAnalysis",
    "ImageAnalyzerAgent",
    "ImageAnalyzerConfig",
    "ImageAnalyzerInputSchema",
    "ImageAnalyzerOutputSchema",
    "analyze_image_urls",
    "render_markdown",
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
You are a meticulous figure analyst. The user message contains a `Context`
paragraph followed by a batch of images. Each image is followed by a caption:

    caption: [Image slug: <slug>]

Return one `FigureAnalysis` per image:

- **slug**: copy verbatim from the caption — never invent or shorten.
- **url**: leave empty (`""`); filled programmatically.
- **figure_type**: `"plot"` (axes/data), `"illustration"` (schematic/sketch),
  or `"unknown"`.
- **description**: 1–2 specific sentences using the context's vocabulary.
- **x_axis / y_axis**: label and visible range with units. Plots only.
- **legend**: legend entries verbatim with color (`["baseline — blue", ...]`).
  Plots only.
- **caption**: figure title or visible caption text.
- **notes**: anomalies, scale issues, suspicious spikes, or empty.

Rules:
- One entry per attached image. No skips, no inventions.
- Quote what is actually visible — no hallucinated values.
- For illustrations, leave x_axis/y_axis/legend empty.
- Unreadable image → `description="image could not be read"`,
  `figure_type="unknown"`, but still return the entry.
"""


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


class ImageAnalyzerConfig(OpenAIBaseAgentConfig):
    """Configuration for the Image Analyzer Agent."""

    system_prompt: str = Field(default=IMAGE_ANALYZER_SYSTEM_PROMPT)
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    download_concurrency: int = Field(default=8, ge=1)
    download_timeout_seconds: float = Field(default=60.0, gt=0)


# -----------------------------------------------------------------------------
# Agent  (zero-override — config holder only)
# -----------------------------------------------------------------------------


class ImageAnalyzerAgent(
    OpenAIBaseAgent[ImageAnalyzerInputSchema, ImageAnalyzerOutputSchema],
):
    """Image analyzer agent — no method overrides.

    Use :func:`analyze_image_urls` as the entry point.  The agent object
    supplies configuration (model, prompt, reasoning effort, concurrency).
    """

    input_schema = ImageAnalyzerInputSchema
    output_schema = ImageAnalyzerOutputSchema | TextOutput
    config_schema = ImageAnalyzerConfig


# -----------------------------------------------------------------------------
# Internal: single-batch LLM call via responses.parse
# -----------------------------------------------------------------------------


async def _analyze_batch(
    agent: ImageAnalyzerAgent,
    batch: list[dict[str, Any]],
    context: str,
    idx: int,
    total: int,
) -> list[FigureAnalysis]:
    """Send one batch of downloaded images to ``responses.parse``."""
    content: list[dict[str, Any]] = []
    if context:
        content.append({"type": "input_text", "text": f"## Context\n\n{context.strip()}"})
    content.append({
        "type": "input_text",
        "text": f"## Batch {idx} of {total}\n\nReturn one FigureAnalysis per attached image.",
    })
    for item in batch:
        b64 = base64.b64encode(item["bytes"]).decode("ascii")
        content.append({
            "type": "input_image",
            "image_url": f"data:{item['mime']};base64,{b64}",
        })
        content.append({"type": "input_text", "text": f"caption: [Image slug: {item['slug']}]"})

    kwargs: dict[str, Any] = {}
    if agent.config.reasoning_effort is not None:
        kwargs["reasoning"] = {"effort": agent.config.reasoning_effort}
    try:
        resp = await AsyncOpenAI().responses.parse(
            model=agent.config.model_name,
            instructions=agent.config.system_prompt,
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

    slug_to_url = {item["slug"]: item["url"] for item in batch}
    for a in parsed.analyses:
        a.url = slug_to_url.get(a.slug, "")
    return parsed.analyses


# -----------------------------------------------------------------------------
# External entry point: batch loop
# -----------------------------------------------------------------------------


async def analyze_image_urls(
    agent: ImageAnalyzerAgent,
    urls: list[str],
    context: str = "",
    batch_size: int = 10,
) -> ImageAnalyzerOutputSchema:
    """Download images, loop ``responses.parse`` per batch, concatenate.

    1. Dedupe URLs preserving order.
    2. Download all into a temp dir with bounded concurrency.
    3. Split into batches of *batch_size*.
    4. Per batch: call ``responses.parse`` for structured output.
    5. Map slug → url, concatenate, render Markdown.
    """
    urls = list(dict.fromkeys(urls))
    if not urls:
        return ImageAnalyzerOutputSchema(analyses=[], markdown="No URLs supplied.")

    with tempfile.TemporaryDirectory(prefix="image_analyzer_") as tmp:
        items = await download_images(
            urls,
            Path(tmp),
            concurrency=agent.config.download_concurrency,
            timeout=agent.config.download_timeout_seconds,
        )
    logger.info(f"[ImageAnalyzer] {len(items)}/{len(urls)} downloads succeeded")
    if not items:
        return ImageAnalyzerOutputSchema(
            analyses=[], markdown="All image downloads failed; check warnings.",
        )

    bs = batch_size
    total = (len(items) + bs - 1) // bs
    all_analyses: list[FigureAnalysis] = []
    for i in range(0, len(items), bs):
        all_analyses.extend(
            await _analyze_batch(agent, items[i : i + bs], context, i // bs + 1, total)
        )

    return ImageAnalyzerOutputSchema(
        analyses=all_analyses,
        markdown=render_markdown(all_analyses, context),
    )


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
