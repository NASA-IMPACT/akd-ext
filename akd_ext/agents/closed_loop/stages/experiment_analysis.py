"""Stage-5 Experiment Analysis Agent (closed-loop).

Stage 5 is a thin orchestrator:

1.  Call ``job_status`` (deterministic, no LLM).  If the job is not
    complete, return a free-form ``TextOutput`` with the status.
2.  Call ``job_plot`` to get ``{experiment_id: [url, ...]}``.
3.  Build context: Stage-1 hypothesis + Stage-3 experiment spec +
    an **experiment–figure mapping** that tells the analyzer which
    image slugs belong to which experiment.
4.  Hand the (flattened) URLs + context to the generic
    :class:`~akd_ext.agents.image_analyzer.ImageAnalyzerAgent`.
5.  Wrap the analyzer's output in a :class:`ExperimentAnalysisOutputSchema`.

The agent itself never invokes the LLM — all "intelligence" lives in
:class:`ImageAnalyzerAgent`.  Stage 5's job is the deterministic MCP I/O
and the completion-status branching around it.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
from typing import Any, Literal, cast

import httpx
from loguru import logger
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from pydantic import Field

from akd._base import (
    CompletedEvent,
    CompletedEventData,
    InputSchema,
    OutputSchema,
    PartialOutputEvent,
    RunContext,
    RunningEvent,
    StartingEvent,
    StartingEventData,
    StreamEvent,
    TextOutput,
)
from akd_ext.agents._base import OpenAIBaseAgent
from akd_ext.agents.closed_loop._base import ClosedLoopStageConfig
from akd_ext.agents.image_analyzer import (
    ImageAnalyzerAgent,
    ImageAnalyzerConfig,
    ImageAnalyzerInputSchema,
    ImageAnalyzerOutputSchema,
)

__all__ = [
    "ExperimentAnalysisAgent",
    "ExperimentAnalysisConfig",
    "ExperimentAnalysisInputSchema",
    "ExperimentAnalysisOutputSchema",
]

_COMPLETE = {"completed", "finished", "done", "success"}
_FAILED = {"failed", "cancelled", "canceled", "error"}

# File-type classification by extension
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".tiff", ".tif", ".bmp", ".webp"}
_TEXT_EXTS = {".md", ".markdown", ".txt", ".text", ".rst", ".log"}
_CSV_EXTS = {".csv", ".tsv"}

# Cap on fetched text payloads (markdown/txt/log) before they reach an LLM
# prompt — prevents a multi-MB pipeline log from ballooning the context.
_MAX_TEXT_CHARS = 20_000


# ---------------------------------------------------------------------------
# URL content utilities — fetch text/CSV content, separate from images
# ---------------------------------------------------------------------------


def _url_extension(url: str) -> str:
    """Extract lowercase file extension from a URL, ignoring query params."""
    from urllib.parse import urlparse

    path = urlparse(url).path
    dot = path.rfind(".")
    return path[dot:].lower() if dot != -1 else ""


def _slug(url: str) -> str:
    """Filename slug from a URL: last path segment, query stripped."""
    return url.rstrip("/").split("/")[-1].split("?")[0]


def _classify_url(url: str) -> str:
    """Classify a URL as ``'image'``, ``'csv'``, ``'text'``, or ``'unknown'``."""
    ext = _url_extension(url)
    if ext in _IMAGE_EXTS:
        return "image"
    if ext in _CSV_EXTS:
        return "csv"
    if ext in _TEXT_EXTS:
        return "text"
    return "unknown"


class _BinaryContent(Exception):
    """Raised when a fetched URL is binary (image/pdf/etc.) so it should be
    routed to the image analyzer instead of decoded as text. Needed because
    ``httpx.Response.text`` never raises on binary bytes — it just produces
    mojibake — so an extension check alone can't catch extensionless images."""


async def _fetch_text(url: str, client: httpx.AsyncClient) -> str:
    """Download a URL with a shared client and return its text content.

    Returns the raw text for markdown/txt, or a formatted markdown table
    for CSV/TSV files (up to 200 rows to avoid blowing up context).

    Raises ``_BinaryContent`` when the response Content-Type indicates binary
    (image/pdf/octet-stream) and the extension didn't already mark it text/CSV —
    the caller routes those to the image analyzer.
    """
    import csv
    import io

    ext = _url_extension(url)
    slug = _slug(url)

    resp = await client.get(url)
    resp.raise_for_status()

    # For non-text/CSV extensions, trust the Content-Type: binary content
    # (images, PDFs) must not be decoded as text and fed to the LLM.
    if ext not in _TEXT_EXTS and ext not in _CSV_EXTS:
        ctype = resp.headers.get("content-type", "").lower()
        if any(t in ctype for t in ("image/", "application/pdf", "application/octet-stream")):
            raise _BinaryContent(ctype or "binary")

    content = resp.text

    if ext in _CSV_EXTS:
        # Parse CSV/TSV → markdown table (cap at 200 rows)
        delimiter = "\t" if ext == ".tsv" else ","
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return f"*CSV `{slug}` is empty.*"
        header = rows[0]
        data = rows[1:201]  # cap
        lines = [
            f"### Data: `{slug}`",
            "",
            "| " + " | ".join(header) + " |",
            "| " + " | ".join("---" for _ in header) + " |",
        ]
        for row in data:
            # Pad/trim to header length
            padded = row + [""] * (len(header) - len(row))
            lines.append("| " + " | ".join(padded[: len(header)]) + " |")
        if len(rows) - 1 > 200:
            lines.append(f"\n*({len(rows) - 1} total rows — showing first 200)*")
        return "\n".join(lines)

    # Markdown / plain text — cap to avoid ballooning the LLM context with a
    # multi-MB log; note the truncation like the CSV branch does.
    if len(content) > _MAX_TEXT_CHARS:
        content = (
            content[:_MAX_TEXT_CHARS]
            + f"\n\n*(truncated — showing first {_MAX_TEXT_CHARS:,} of "
            f"{len(content):,} characters)*"
        )
    return f"### Report: `{slug}`\n\n{content}"


async def _categorize_and_fetch(
    urls: list[str], timeout: float = 60.0,
) -> tuple[list[str], str]:
    """Split URLs into image URLs and fetched text content.

    Text/CSV URLs are fetched concurrently through a single shared client.
    Unknown extensions are attempted as text and fall back to image on failure.

    Returns
    -------
    image_urls : list[str]
        URLs classified as images (passed to ImageAnalyzerAgent).
    text_context : str
        Concatenated text content from CSV / markdown / text URLs.
    """
    image_urls: list[str] = []
    to_fetch: list[str] = []  # csv/text/unknown URLs to download
    for url in urls:
        if _classify_url(url) == "image":
            image_urls.append(url)
        else:
            to_fetch.append(url)

    text_parts: list[str] = []
    if to_fetch:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            results = await asyncio.gather(
                *(_fetch_text(u, client) for u in to_fetch),
                return_exceptions=True,
            )
        for url, result in zip(to_fetch, results):
            if isinstance(result, _BinaryContent):
                # Content-Type says binary (image/pdf) — route to the analyzer.
                logger.debug(f"[Stage5] {url} is binary ({result}) — routing to image analyzer")
                image_urls.append(url)
            elif isinstance(result, Exception):
                if _classify_url(url) == "unknown":
                    # Unknown type that failed to fetch — treat as image.
                    image_urls.append(url)
                else:
                    logger.warning(f"[Stage5] failed to fetch {url}: {result}")
                    text_parts.append(f"*Could not fetch `{url}`: {result}*")
            else:
                logger.debug(f"[Stage5] fetched content from {url} ({len(result)} chars)")
                text_parts.append(result)

    text_context = ""
    if text_parts:
        text_context = (
            "\n\n---\n\n## Pipeline Output Data\n\n"
            + "\n\n---\n\n".join(text_parts)
        )
    return image_urls, text_context


# -----------------------------------------------------------------------------
# Configuration / Schemas
# -----------------------------------------------------------------------------


class ExperimentAnalysisConfig(ClosedLoopStageConfig):
    """Configuration for the Stage-5 Data Analysis Agent."""

    mcp_url: str = Field(
        default_factory=lambda: os.environ.get("CM1_MCP_URL", "https://fm.prism.nasa-impact.net/akd/cm1-mcp"),
        description="CM1 Temporal MCP server URL for job_status / job_plot calls.",
    )
    default_user_name: str = Field(
        default="igurung",
        description="Fallback user_name passed to job_plot when not provided in the input.",
    )
    plot_read_timeout_seconds: float = Field(
        default=600.0,
        description="Read timeout (s) for job_plot — plot generation can be slow.",
    )
    analyzer_config: ImageAnalyzerConfig = Field(
        default_factory=ImageAnalyzerConfig,
        description="Forwarded to the underlying ImageAnalyzerAgent.",
    )


class ExperimentAnalysisInputSchema(InputSchema):
    """Input schema for the Stage-5 Data Analysis Agent."""

    job_id: str = Field(..., description="Job ID returned by Stage 4.")
    workspace_name: str | None = Field(
        default=None,
        description="Workspace name. If omitted, derived from the job_status payload.",
    )
    user_name: str | None = Field(
        default=None,
        description="Optional user name. Falls back to config.default_user_name.",
    )
    hypothesis: str = Field(
        default="",
        description="Stage-1 research question and gap analysis output (Gap Agent).",
    )
    experiment_spec: str = Field(
        default="",
        description="Stage-3 implementation report (ExperimentImplementation output).",
    )
    skip_status_check: bool = Field(
        default=False,
        description="Skip job_status check and go straight to job_plot.",
    )
    message: str = Field(
        default="",
        description=(
            "The user's chat turn, for interactive Stage-5 orchestrators. "
            "Routes the lifecycle (design / approve / check status / analyze). "
            "The non-interactive base agent ignores it."
        ),
    )
    query: str | None = Field(
        default=None,
        description=(
            "Alias for the user's chat turn under the LangGraph/UI driver, "
            "which delivers the reply as 'query' (inputs.<node>.query on resume) "
            "rather than 'message'. Resolved alongside 'message'."
        ),
    )


class ExperimentAnalysisOutputSchema(OutputSchema):
    """Stage-5 structured output (only emitted when the job is complete).

    Stage 5 returns **structured figure analyses** and any fetched text
    data (CSVs, markdown reports from the pipeline).  It does NOT
    generate a narrative report — that is Stage 6's job.

    Downstream consumers (Stage 6 / Paper Assembly) receive:
    - ``analyses``: per-figure ``FigureAnalysis`` objects from ImageAnalyzerAgent
    - ``text_content``: concatenated CSV tables / markdown from pipeline outputs
    - ``experiment_map``: ``{experiment_id: [figure_slugs]}`` for cross-referencing
    - ``markdown``: rendered figure-analysis report (the human-facing response)
    """

    # Response channel must be a string (the _response computed field is typed
    # -> str). Point it at the rendered ``markdown``; ``analyses`` is the
    # structured list consumers read programmatically.
    __response_field__ = "markdown"

    status: Literal["completed"] = Field(default="completed")
    message: str = Field(default="Experiment analysis complete — figures analyzed")
    analyses: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Per-figure structured analyses from ImageAnalyzerAgent (FigureAnalysis dicts).",
    )
    text_content: str = Field(
        default="",
        description="Fetched text content from pipeline outputs (CSV tables, markdown reports).",
    )
    experiment_map: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Mapping of experiment_id → list of figure slugs.",
    )
    image_urls: list[str] = Field(
        default_factory=list,
        description="Original image URLs fetched from job_plot.",
    )
    markdown: str = Field(
        default="",
        description="Rendered markdown from ImageAnalyzerAgent — formatted figure descriptions for Stage 6 context.",
    )


# -----------------------------------------------------------------------------
# MCP helper — single function, called twice (job_status, job_plot)
# -----------------------------------------------------------------------------


async def _mcp_call(
    *,
    url: str,
    headers: dict[str, str],
    tool: str,
    args: dict[str, Any],
    read_timeout: float,
) -> dict[str, Any]:
    """Invoke an MCP tool via streamable-HTTP and return the parsed JSON dict.

    ``headers`` carries the auth header for the target server. The auth scheme
    is a per-server property (e.g. CM1 uses ``X-API-Key``, Prithvi uses
    ``Authorization: Bearer``); callers supply it via the agent's
    ``_auth_headers`` hook rather than hardcoding it here.

    Falls back to the structuredContent dict when present, otherwise parses
    the concatenated text content. Returns ``{}`` if neither yields a dict.

    Handles two common server wrappers:
    - FastMCP cloud wraps responses as ``{"result": "<json_string>"}`` — the
      inner JSON string is parsed and returned directly.
    - Servers that wrap the real payload as a JSON string under ``"payload"``
      — that gets unwrapped into ``"payload_parsed"``.
    """
    timeout = httpx.Timeout(connect=30.0, read=read_timeout, write=60.0, pool=60.0)
    async with httpx.AsyncClient(headers=headers, timeout=timeout) as http_client:
        async with streamable_http_client(url=url, http_client=http_client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.call_tool(tool, args)

    structured = getattr(res, "structuredContent", None)
    if isinstance(structured, dict):
        # FastMCP cloud wraps the real JSON payload as a string under "result"
        # e.g. {"result": '{"job_id": "abc", "status": "completed"}'}
        raw_result = structured.get("result")
        if isinstance(raw_result, str):
            try:
                inner = json.loads(raw_result)
                if isinstance(inner, dict):
                    return inner
            except json.JSONDecodeError:
                pass
        return structured

    text = "".join(getattr(b, "text", "") or "" for b in (getattr(res, "content", None) or [])).strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}
    # FastMCP result wrapper (same as structuredContent path)
    if isinstance(obj, dict) and isinstance(obj.get("result"), str):
        try:
            inner = json.loads(obj["result"])
            if isinstance(inner, dict):
                obj = inner
        except json.JSONDecodeError:
            pass
    if isinstance(obj, dict) and isinstance(obj.get("payload"), str):
        try:
            obj["payload_parsed"] = json.loads(obj["payload"])
        except json.JSONDecodeError:
            pass
    return obj if isinstance(obj, dict) else {}


# -----------------------------------------------------------------------------
# Experiment Analysis Agent
# -----------------------------------------------------------------------------


class ExperimentAnalysisAgent(
    OpenAIBaseAgent[ExperimentAnalysisInputSchema, ExperimentAnalysisOutputSchema],
):
    """Stage-5 orchestrator. Status check → URL fetch → delegate to ImageAnalyzerAgent."""

    input_schema = ExperimentAnalysisInputSchema
    output_schema = ExperimentAnalysisOutputSchema | TextOutput
    config_schema = ExperimentAnalysisConfig

    # -- Helpers -------------------------------------------------------

    @property
    def _api_key(self) -> str:
        key = os.environ.get("CM1_MCP_API_KEY")
        if not key:
            raise RuntimeError("CM1_MCP_API_KEY is not set; cannot reach the CM1 MCP.")
        return key

    @property
    def _auth_headers(self) -> dict[str, str]:
        """Auth header for the MCP server. Per-server scheme — override in
        subclasses whose server uses a different scheme (e.g. Prithvi uses
        ``Authorization: Bearer``). Defaults to CM1's ``X-API-Key``."""
        return {"X-API-Key": self._api_key}

    @staticmethod
    def _workspace_from(payload: dict[str, Any]) -> str | None:
        """Extract workspace_name from a job_status payload, top-level or wrapped."""
        for blob in (payload, payload.get("payload_parsed") or {}):
            if isinstance(blob, dict):
                ws = blob.get("workspace_name")
                if isinstance(ws, str) and ws:
                    return ws
        return None

    @staticmethod
    def _flatten(plot_urls: dict[str, list[str]]) -> list[str]:
        """``{exp_id: [urls]}`` → flat list, preserving order."""
        return [u for urls in plot_urls.values() for u in urls if isinstance(u, str)]

    @staticmethod
    def _build_experiment_map_context(experiment_urls: dict[str, list[str]]) -> str:
        """Build a markdown section mapping experiment IDs → figure slugs.

        This is injected into the ImageAnalyzer context so the LLM knows
        which figures belong to which experiment.
        """
        if not experiment_urls:
            return ""
        lines = [
            "## Experiment–Figure Mapping",
            "",
            "Each figure belongs to a specific experiment.  Use this mapping",
            "to identify which experiment produced each figure and label your",
            "analysis accordingly.",
            "",
        ]
        for exp_id, urls in experiment_urls.items():
            slugs = [_slug(url) for url in urls if isinstance(url, str)]
            lines.append(f"- **{exp_id}** ({len(slugs)} figures): {', '.join(slugs)}")
        return "\n".join(lines)

    @staticmethod
    def _build_context(
        params: ExperimentAnalysisInputSchema,
        experiment_urls: dict[str, list[str]] | None = None,
    ) -> str:
        """Concatenate hypothesis + experiment_spec + experiment–figure map."""
        parts: list[str] = []
        if params.hypothesis.strip():
            parts.append(f"## Hypothesis / Feasibility Report\n\n{params.hypothesis.strip()}")
        if params.experiment_spec.strip():
            parts.append(f"## Experiment Specification\n\n{params.experiment_spec.strip()}")
        if experiment_urls:
            exp_map = ExperimentAnalysisAgent._build_experiment_map_context(experiment_urls)
            if exp_map:
                parts.append(exp_map)
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _extract_status(payload: dict[str, Any]) -> str:
        """Extract status from top-level or wrapped payload_parsed."""
        for blob in (payload, payload.get("payload_parsed") or {}):
            if isinstance(blob, dict):
                s = blob.get("status")
                if isinstance(s, str) and s:
                    return s.lower()
        return "unknown"

    async def _check_job(self, job_id: str) -> dict[str, Any] | TextOutput:
        """MCP job_status → payload dict, or TextOutput on error / not-complete."""
        try:
            payload = await _mcp_call(
                url=self.config.mcp_url, headers=self._auth_headers,
                tool="job_status", args={"job_id": job_id}, read_timeout=60.0,
            )
        except Exception as exc:
            logger.warning(f"[Stage5] job_status failed: {exc!r}")
            return TextOutput(content=f"Could not reach MCP server for `{job_id}`: {exc}")

        logger.debug(f"[Stage5] job_status payload keys: {list(payload.keys())}")
        status = self._extract_status(payload)
        if status in _FAILED:
            return TextOutput(content=f"Job `{job_id}` failed (status=`{status}`). No analysis.")
        if status not in _COMPLETE:
            return TextOutput(
                content=(
                    f"Job `{job_id}` is still running (status=`{status}`). "
                    "Figure analysis has NOT started — it will only begin once the "
                    "job is complete. Ask me to check again in a bit."
                )
            )
        return payload

    def _resolve_workspace(
        self, params: ExperimentAnalysisInputSchema, payload: dict[str, Any],
    ) -> tuple[str, str] | TextOutput:
        """Return ``(workspace, user)`` or a TextOutput error."""
        workspace = params.workspace_name or self._workspace_from(payload)
        if not workspace:
            return TextOutput(
                content=f"Could not determine `workspace_name` for `{params.job_id}`. "
                "Pass it explicitly via the input schema."
            )
        return workspace, params.user_name or self.config.default_user_name

    async def _fetch_plot_urls(self, job_id: str, workspace: str, user: str) -> dict[str, list[str]] | TextOutput:
        """MCP job_plot → ``{group: [urls]}`` dict, or TextOutput on error / empty.

        Handles two response shapes:
        - **Grouped**: ``{experiment_id: [url, ...], ...}``  (list values)
        - **Flat + extras**: ``{"figures": [url, ...], "report_url": "..."}``

        String values that look like URLs (``http``-prefixed) are collected
        into a ``"results"`` group so they flow through the same pipeline.
        """
        try:
            plot_payload = await _mcp_call(
                url=self.config.mcp_url, headers=self._auth_headers,
                tool="job_plot",
                args={"job_id": job_id, "workspace_name": workspace, "user_name": user},
                read_timeout=self.config.plot_read_timeout_seconds,
            )
        except Exception as exc:
            logger.warning(f"[Stage5] job_plot failed: {exc!r}")
            return TextOutput(content=f"Failed to fetch plots for `{job_id}`: {exc}")

        plot_urls: dict[str, list[str]] = {}
        extra_urls: list[str] = []

        for k, v in plot_payload.items():
            if k.startswith("_") or k in ("payload", "job_id"):
                continue
            if isinstance(v, list):
                # List of URLs (grouped by experiment or "figures")
                urls = [u for u in v if isinstance(u, str) and u.startswith("http")]
                if urls:
                    plot_urls[k] = urls
            elif isinstance(v, str) and v.startswith("http"):
                # Single URL string (e.g. report_url, summary_url)
                extra_urls.append(v)

        if extra_urls:
            plot_urls.setdefault("results", []).extend(extra_urls)

        n_total = len(self._flatten(plot_urls))
        if not n_total:
            return TextOutput(content=f"Job `{job_id}` is complete but `job_plot` returned no figures or data.")
        logger.debug(f"[Stage5] job_id={job_id} workspace={workspace!r} urls={n_total} groups={list(plot_urls.keys())}")
        return plot_urls

    # -- Output builders (shared by _arun and _astream) ----------------

    @staticmethod
    def _build_exp_map(experiment_urls: dict[str, list[str]]) -> dict[str, list[str]]:
        """Map each experiment id → its figure slugs."""
        return {
            exp_id: [_slug(u) for u in urls if isinstance(u, str)]
            for exp_id, urls in experiment_urls.items()
        }

    @staticmethod
    def _text_only_output(
        fetched_text: str, exp_map: dict[str, list[str]]
    ) -> ExperimentAnalysisOutputSchema:
        """Output for the no-image case (text artifacts only, no figures).

        ``markdown`` is the response channel (__response_field__), so it must be
        set here too — otherwise a no-figure run returns a blank response.
        """
        body = fetched_text or "No figures or data returned by job_plot."
        return ExperimentAnalysisOutputSchema(
            text_content=body,
            markdown=body,
            experiment_map=exp_map,
        )

    @staticmethod
    def _analyzed_output(
        result: ImageAnalyzerOutputSchema,
        fetched_text: str,
        exp_map: dict[str, list[str]],
        image_urls: list[str],
    ) -> ExperimentAnalysisOutputSchema:
        """Output wrapping the ImageAnalyzer's per-figure analyses."""
        return ExperimentAnalysisOutputSchema(
            analyses=[a.model_dump() for a in result.analyses],
            text_content=fetched_text,
            experiment_map=exp_map,
            image_urls=image_urls,
            markdown=result.markdown,
        )

    # -- Pipeline (_arun) ----------------------------------------------

    async def _arun(
        self, params: ExperimentAnalysisInputSchema, run_context: RunContext, **kwargs: Any
    ) -> ExperimentAnalysisOutputSchema | TextOutput:
        if params.skip_status_check:
            payload: dict[str, Any] = {}
            logger.debug(f"[Stage5] Skipping status check for {params.job_id}")
        else:
            payload = await self._check_job(params.job_id)
            if isinstance(payload, TextOutput):
                return payload

        ws = self._resolve_workspace(params, payload)
        if isinstance(ws, TextOutput):
            return ws
        workspace, user = ws

        experiment_urls = await self._fetch_plot_urls(params.job_id, workspace, user)
        if isinstance(experiment_urls, TextOutput):
            return experiment_urls

        all_urls = self._flatten(experiment_urls)

        # Separate images from text content (CSV, markdown, etc.)
        image_urls, fetched_text = await _categorize_and_fetch(all_urls)
        logger.debug(
            f"[Stage5] {len(image_urls)} image URLs, "
            f"{len(fetched_text)} chars of fetched text content"
        )

        # fetched_text (report .md, CSVs) is saved in text_content for Stage 6
        # but NOT appended to the ImageAnalyzer context — the analyzer focuses
        # on interpreting the figures, not regurgitating report text.
        context = self._build_context(params, experiment_urls)
        exp_map = self._build_exp_map(experiment_urls)

        if not image_urls:
            return self._text_only_output(fetched_text, exp_map)

        result = await ImageAnalyzerAgent(self.config.analyzer_config).arun(
            ImageAnalyzerInputSchema(urls=image_urls, context=context),
        )
        if not isinstance(result, ImageAnalyzerOutputSchema):
            return cast(TextOutput, result)
        return self._analyzed_output(result, fetched_text, exp_map, image_urls)

    # -- Pipeline (_astream) -------------------------------------------

    async def _astream(
        self, params: ExperimentAnalysisInputSchema, run_context: RunContext, **kwargs: Any
    ) -> AsyncIterator[StreamEvent]:
        cn = self.__class__.__name__

        yield StartingEvent(
            source=cn, message=f"Starting {cn}",
            data=StartingEventData[ExperimentAnalysisInputSchema](params=params),
            run_context=run_context,
        )
        # 1. job_status
        if params.skip_status_check:
            payload: dict[str, Any] = {}
            logger.debug(f"[Stage5] Skipping status check for {params.job_id}")
            yield RunningEvent(source=cn, message="Skipping status check…", run_context=run_context)
        else:
            yield RunningEvent(source=cn, message="Checking job status…", run_context=run_context)
            payload = await self._check_job(params.job_id)
            if isinstance(payload, TextOutput):
                yield CompletedEvent(source=cn, message=f"Completed {cn}", data=CompletedEventData(output=payload), run_context=run_context)
                return

        # 2. workspace + user
        ws = self._resolve_workspace(params, payload)
        if isinstance(ws, TextOutput):
            yield CompletedEvent(source=cn, message=f"Completed {cn}", data=CompletedEventData(output=ws), run_context=run_context)
            return
        workspace, user = ws

        yield RunningEvent(source=cn, message=f"Job complete. Fetching plots for {workspace}…", run_context=run_context)

        # 3. job_plot
        experiment_urls = await self._fetch_plot_urls(params.job_id, workspace, user)
        if isinstance(experiment_urls, TextOutput):
            yield CompletedEvent(source=cn, message=f"Completed {cn}", data=CompletedEventData(output=experiment_urls), run_context=run_context)
            return

        all_urls = self._flatten(experiment_urls)

        # Separate images from text content (CSV, markdown, etc.)
        yield RunningEvent(source=cn, message=f"Got {len(all_urls)} URLs. Fetching text content…", run_context=run_context)
        image_urls, fetched_text = await _categorize_and_fetch(all_urls)
        yield RunningEvent(
            source=cn,
            message=f"{len(image_urls)} images, {len(fetched_text)} chars text. Analyzing…",
            run_context=run_context,
        )

        context = self._build_context(params, experiment_urls)
        exp_map = self._build_exp_map(experiment_urls)

        if not image_urls:
            final = self._text_only_output(fetched_text, exp_map)
            yield CompletedEvent(source=cn, message=f"Completed {cn}", data=CompletedEventData(output=final), run_context=run_context)
            return

        # 4. Delegate — forward ImageAnalyzerAgent's streaming events
        analyzer = ImageAnalyzerAgent(self.config.analyzer_config)
        result: ImageAnalyzerOutputSchema | TextOutput | None = None

        async for event in analyzer.astream(ImageAnalyzerInputSchema(urls=image_urls, context=context)):
            if isinstance(event, PartialOutputEvent):
                yield PartialOutputEvent(source=cn, message=event.message, data=event.data, run_context=run_context)
            elif isinstance(event, CompletedEvent):
                result = event.data.output

        # 5. Wrap — return structured analyses, NOT a rendered report
        if isinstance(result, ImageAnalyzerOutputSchema):
            final = self._analyzed_output(result, fetched_text, exp_map, image_urls)
        elif result is not None:
            final = cast(TextOutput, result)
        else:
            final = TextOutput(content="ImageAnalyzerAgent returned no output.")

        yield CompletedEvent(source=cn, message=f"Completed {cn}", data=CompletedEventData(output=final), run_context=run_context)

    # -- Output validation ---------------------------------------------

    def check_output(self, output) -> str | None:
        if isinstance(output, ExperimentAnalysisOutputSchema) and not output.analyses and not output.text_content.strip():
            return "No figure analyses or text content — the image analyzer produced no output."
        return super().check_output(output)
