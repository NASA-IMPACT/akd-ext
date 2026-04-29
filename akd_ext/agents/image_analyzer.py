"""Generic Image Analyzer Agent.

Takes a list of remote image URLs plus a free-form ``context`` paragraph and
returns one structured :class:`FigureAnalysis` per image.

Pipeline (all inside ``_arun``):

1. Dedupe URLs preserving order.
2. Download every URL into a managed ``tempfile.TemporaryDirectory()`` with
   bounded concurrency (auto-cleaned on exit).  Failures are logged and
   skipped.
3. Split into batches of ``batch_size`` (default 10).
4. Per batch: send a multimodal user message (context + base64 images +
   slug captions) to ``client.responses.parse`` with a Pydantic structured
   output.  Map ``slug`` → ``url`` deterministically.
5. Concatenate batches; render a Markdown summary.
"""

from __future__ import annotations

import asyncio
import base64
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Literal, cast

import httpx
from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from akd._base import (
    CompletedEvent,
    CompletedEventData,
    InputSchema,
    OutputSchema,
    RunContext,
    StreamEvent,
    TextOutput,
)
from akd_ext.agents._base import OpenAIBaseAgent, OpenAIBaseAgentConfig

__all__ = [
    "FigureAnalysis",
    "ImageAnalyzerAgent",
    "ImageAnalyzerConfig",
    "ImageAnalyzerInputSchema",
    "ImageAnalyzerOutputSchema",
]


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------


class FigureAnalysis(BaseModel):
    """Structured analysis of one image. ``url`` is filled by the agent
    post-LLM (slug → url); the model fills everything else."""

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
    """Container for ``responses.parse`` structured output (one per batch)."""

    analyses: list[FigureAnalysis] = Field(default_factory=list)


class ImageAnalyzerInputSchema(InputSchema):
    """List of image URLs plus a free-form context paragraph."""

    urls: list[str] = Field(default_factory=list)
    context: str = Field(default="")


class ImageAnalyzerOutputSchema(OutputSchema):
    """Aggregated analyses across all batches, plus a Markdown summary."""

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

    batch_size: int = Field(default=10, ge=1)
    download_concurrency: int = Field(default=8, ge=1)
    download_timeout_seconds: float = Field(default=60.0, gt=0)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _slug_of(url: str) -> str:
    return url.rstrip("/").split("/")[-1].split("?")[0]


def _sniff_image(blob: bytes) -> tuple[str, str] | None:
    """Detect (mime, ext) from PNG/JPEG magic bytes, else None."""
    if blob.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if blob[:3] == b"\xff\xd8\xff":
        return "image/jpeg", ".jpg"
    return None


def _render_markdown(analyses: list[FigureAnalysis], context: str) -> str:
    """Cheap Markdown render — one section per figure."""
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


async def _download_all(
    urls: list[str], tmpdir: Path, concurrency: int, timeout: float
) -> list[dict[str, Any]]:
    """Download every URL into ``tmpdir`` with bounded concurrency.

    Failed downloads (HTTP error, unsupported format) are logged and dropped.
    Returns successful items in original order.
    """
    sem = asyncio.Semaphore(concurrency)

    async def fetch(client: httpx.AsyncClient, url: str) -> dict[str, Any] | None:
        async with sem:
            try:
                r = await client.get(url, follow_redirects=True)
                r.raise_for_status()
            except Exception as exc:
                logger.warning(f"[ImageAnalyzer] download failed {url}: {exc!r}")
                return None
            sniff = _sniff_image(r.content)
            if sniff is None:
                logger.warning(f"[ImageAnalyzer] unsupported format for {url}; skipping.")
                return None
            mime, ext = sniff
            slug = _slug_of(url)
            (tmpdir / f"{slug}{ext}").write_bytes(r.content)
            return {"url": url, "slug": slug, "bytes": r.content, "mime": mime}

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        results = await asyncio.gather(*[fetch(client, u) for u in urls])
    return [r for r in results if r is not None]


# -----------------------------------------------------------------------------
# Agent
# -----------------------------------------------------------------------------


class ImageAnalyzerAgent(
    OpenAIBaseAgent[ImageAnalyzerInputSchema, ImageAnalyzerOutputSchema],
):
    """URL list + context → structured per-image analyses + Markdown.

    Bypasses the framework's LLM-loop machinery — calls the OpenAI Responses
    API ``parse`` helper directly per batch with a Pydantic structured-output
    schema. Keeps batching simple and produces deterministic JSON without
    prompting overhead.
    """

    input_schema = ImageAnalyzerInputSchema
    output_schema = ImageAnalyzerOutputSchema | TextOutput
    config_schema = ImageAnalyzerConfig

    async def _analyze_batch(
        self,
        client: AsyncOpenAI,
        batch: list[dict[str, Any]],
        context: str,
        idx: int,
        total: int,
    ) -> list[FigureAnalysis]:
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
        if self.config.reasoning_effort is not None:
            kwargs["reasoning"] = {"effort": self.config.reasoning_effort}
        try:
            resp = await client.responses.parse(
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

        slug_to_url = {item["slug"]: item["url"] for item in batch}
        for a in parsed.analyses:
            a.url = slug_to_url.get(a.slug, "")
        return parsed.analyses

    async def _run(
        self, params: ImageAnalyzerInputSchema
    ) -> ImageAnalyzerOutputSchema | TextOutput:
        urls = list(dict.fromkeys(params.urls))
        if not urls:
            return TextOutput(content="No URLs supplied.")

        with tempfile.TemporaryDirectory(prefix="image_analyzer_") as tmp:
            items = await _download_all(
                urls, Path(tmp),
                self.config.download_concurrency,
                self.config.download_timeout_seconds,
            )
            logger.info(f"[ImageAnalyzer] {len(items)}/{len(urls)} downloads succeeded")
            if not items:
                return TextOutput(content="All image downloads failed; check warnings.")

            client = AsyncOpenAI()
            bs = self.config.batch_size
            total = (len(items) + bs - 1) // bs
            analyses: list[FigureAnalysis] = []
            for i in range(0, len(items), bs):
                analyses.extend(
                    await self._analyze_batch(
                        client, items[i : i + bs], params.context, i // bs + 1, total,
                    )
                )

        return ImageAnalyzerOutputSchema(
            analyses=analyses,
            markdown=_render_markdown(analyses, params.context),
        )

    async def _arun(
        self, params: ImageAnalyzerInputSchema, run_context: RunContext, **kwargs: Any
    ) -> ImageAnalyzerOutputSchema | TextOutput:
        return cast(ImageAnalyzerOutputSchema | TextOutput, await self._run(params))

    async def _astream(
        self, params: ImageAnalyzerInputSchema, run_context: RunContext, **kwargs: Any
    ) -> AsyncIterator[StreamEvent]:
        output = await self._run(params)
        yield CompletedEvent(
            source=self.__class__.__name__,
            message=f"Completed {self.__class__.__name__}",
            data=CompletedEventData(output=output),
            run_context=run_context,
        )

    def check_output(self, output) -> str | None:
        if isinstance(output, ImageAnalyzerOutputSchema) and not output.analyses:
            return "No FigureAnalysis entries returned."
        return super().check_output(output)
