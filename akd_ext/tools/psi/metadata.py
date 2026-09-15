"""Expand, cache, and rank NASA PSI investigation metadata.

Generates a markdown context file per investigation under a configurable
cache root. The full normalized metadata round-trips through a JSON header
(an HTML comment on the first line), so cache hits need no re-parsing. Cache
entries expire after a TTL and are invalidated by generator version bumps.
"""

import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import Field, model_validator

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool
from akd_ext.mcp import mcp_tool

from ._client import PsiToolConfig, get_json, make_async_client
from ._normalize import normalize_investigation, normalize_investigation_id, relevance_score

GENERATOR_VERSION = "1.0"
_CACHE_RE = re.compile(r"^<!-- psi-context-cache: (\{.*\}) -->$", re.MULTILINE)


class PsiMetadataExpansionInput(InputSchema):
    """Input schema for expanding and ranking PSI investigation metadata."""

    investigation_id: str | None = Field(
        default=None, description="Single PSI investigation id to expand, e.g. 'PSI-117'"
    )
    discovery_results: list[dict] | None = Field(
        default=None,
        description="Candidates from psi_discover_investigations (each needs investigation_id)",
    )
    query: str | None = Field(
        default=None, description="Research question used to rank candidates; required for multiple candidates"
    )
    max_candidates: int = Field(default=5, ge=1, le=20, description="Maximum candidates to expand")
    refresh_cache: bool = Field(default=False, description="Bypass fresh cache entries and refetch")

    @model_validator(mode="after")
    def _validate_candidates(self) -> "PsiMetadataExpansionInput":
        if not self.investigation_id and not self.discovery_results:
            raise ValueError("Provide investigation_id or at least one discovery result")
        if self.discovery_results and len(self.discovery_results) > 1 and not self.query:
            raise ValueError("query is required when ranking multiple candidates")
        return self


class PsiMetadataExpansionOutput(OutputSchema):
    """Output schema for expanding and ranking PSI investigation metadata."""

    enriched_investigations: list[dict] = Field(
        default_factory=list,
        description="Per candidate: normalized_metadata, context_cache status, relevance score/reasons, "
        "and a suggested next tool call",
    )
    warnings: list[dict] = Field(default_factory=list, description="Cache and upstream fallbacks that occurred")
    summary: str = Field(default="", description="One-sentence description of the strongest match")


class PsiMetadataExpansionConfig(PsiToolConfig):
    """Configuration for the PSI metadata expansion tool."""

    name: str = Field(default="metadata_expansion_tool", description="Tool name")
    context_root: str = Field(
        default=os.getenv("PSI_CONTEXT_ROOT", "./context/investigations"),
        description="Directory holding the generated markdown context cache",
    )
    cache_ttl_seconds: int = Field(
        default=int(os.getenv("PSI_CACHE_TTL_SECONDS", "86400")),
        description="Cache freshness window in seconds",
    )


@mcp_tool
class PsiMetadataExpansionTool(BaseTool[PsiMetadataExpansionInput, PsiMetadataExpansionOutput]):
    """Enrich PSI investigation candidates with normalized, cached metadata.

    Fetches full investigation metadata (with a markdown context cache and
    TTL), ranks candidates against the query by weighted keyword relevance,
    and suggests the next tool call. Falls back to stale cache entries when
    the PSI API is unavailable.
    """

    config_schema = PsiMetadataExpansionConfig
    input_schema = PsiMetadataExpansionInput
    output_schema = PsiMetadataExpansionOutput

    async def _arun(self, params: PsiMetadataExpansionInput, **kwargs) -> PsiMetadataExpansionOutput:
        candidates = params.discovery_results or [{"investigation_id": params.investigation_id}]
        candidates = candidates[: params.max_candidates]

        warnings: list[dict] = []
        enriched: list[dict] = []
        for candidate in candidates:
            investigation_id = normalize_investigation_id(str(candidate.get("investigation_id")))
            normalized, cache_info = await self._load_or_generate(
                investigation_id, candidate, params.refresh_cache, warnings
            )
            score, reasons = self._rank(params.query, normalized, candidate)
            enriched.append(
                {
                    "investigation_id": investigation_id,
                    "normalized_metadata": normalized,
                    "context_cache": cache_info,
                    "relevance": {"score": score, "reasons": reasons},
                    "suggested_next_call": {
                        "tool": "psi_api_tool",
                        "arguments": {
                            "operation": "navigate_dataset",
                            "investigation_id": investigation_id,
                        },
                    },
                }
            )

        if params.query:
            enriched.sort(key=lambda item: item["relevance"]["score"], reverse=True)

        if enriched:
            best = enriched[0]
            title = best["normalized_metadata"].get("title")
            summary = f"{best['investigation_id']} is the strongest available match"
            summary += f": {title}." if title else "."
        else:
            summary = "No investigation metadata could be expanded."
        return PsiMetadataExpansionOutput(enriched_investigations=enriched, warnings=warnings, summary=summary)

    def _rank(self, query: str | None, normalized: dict, discovery: dict) -> tuple[float, list[str]]:
        """Score one candidate against the query across weighted metadata fields."""
        if not query:
            return 1.0, ["A specific investigation ID was supplied."]
        publication_text = " ".join(
            str(item.get("title") or "") for item in normalized.get("publications") or [] if isinstance(item, dict)
        )
        score, reasons = relevance_score(
            query,
            [
                ("Title", 0.30, normalized.get("title") or discovery.get("title")),
                ("Objective", 0.30, normalized.get("objective") or discovery.get("objective")),
                ("Research area", 0.15, normalized.get("research_area")),
                ("Sub-research area", 0.10, normalized.get("sub_research_area")),
                (
                    "Approach and hypothesis",
                    0.10,
                    f"{normalized.get('approach') or ''} {normalized.get('hypothesis') or ''}",
                ),
                ("Available publication context", 0.05, publication_text),
            ],
        )
        if not reasons:
            reasons = ["No strong keyword overlap was found in the available metadata."]
        return score, reasons

    # ---- context cache ----

    def _cache_path(self, investigation_id: str) -> Path:
        return Path(self.config.context_root) / investigation_id / "investigation_metadata.md"

    def _load_cache(self, investigation_id: str) -> dict | None:
        """Read the cache header; returns None when missing or unparseable."""
        path = self._cache_path(investigation_id)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None
        match = _CACHE_RE.search(text)
        if not match:
            return None
        try:
            header = json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
        expires_at = header.get("expires_at")
        try:
            header["fresh"] = bool(
                expires_at
                and datetime.fromisoformat(expires_at).astimezone(UTC) > datetime.now(UTC)
                and header.get("generator_version") == GENERATOR_VERSION
            )
        except (TypeError, ValueError):
            header["fresh"] = False
        return header

    async def _load_or_generate(
        self, investigation_id: str, candidate: dict, refresh: bool, warnings: list[dict]
    ) -> tuple[dict, dict]:
        """Return (normalized metadata, cache info), preferring fresh cache entries."""
        cached = self._load_cache(investigation_id)
        path = str(self._cache_path(investigation_id))
        if cached and cached.get("fresh") and not refresh and isinstance(cached.get("normalized"), dict):
            return cached["normalized"], {
                "path": path,
                "status": "hit",
                "fresh": True,
                "generated_at": cached.get("generated_at"),
                "expires_at": cached.get("expires_at"),
            }

        url = self.config.investigation_url_template.format(investigation_id=investigation_id)
        try:
            async with make_async_client(self.config, getattr(self, "transport", None)) as client:
                raw = await get_json(client, url)
            normalized = normalize_investigation(raw if isinstance(raw, dict) else {})
        except (RuntimeError, TimeoutError) as exc:
            if cached and isinstance(cached.get("normalized"), dict):
                warnings.append(
                    {
                        "code": "STALE_CONTEXT_USED",
                        "message": f"Using stale cached context for {investigation_id}: {exc}",
                    }
                )
                return cached["normalized"], {"path": path, "status": "stale_fallback", "fresh": False}
            warnings.append(
                {
                    "code": "CONTEXT_GENERATION_FAILED",
                    "message": f"Could not fetch metadata for {investigation_id}: {exc}",
                }
            )
            fallback = {
                "investigation_id": investigation_id,
                "title": candidate.get("title") or "",
                "objective": candidate.get("objective") or "",
                "research_area": candidate.get("research_area"),
                "sub_research_area": candidate.get("sub_research_area"),
                "publications": [],
            }
            return fallback, {"path": path, "status": "fallback", "fresh": False}

        self._write_cache(investigation_id, normalized)
        return normalized, {
            "path": path,
            "status": "refreshed" if cached else "generated",
            "fresh": True,
        }

    def _write_cache(self, investigation_id: str, normalized: dict) -> None:
        """Write the markdown context file with its JSON cache header."""
        now = datetime.now(UTC)
        header = {
            "investigation_id": investigation_id,
            "generated_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=self.config.cache_ttl_seconds)).isoformat(),
            "generator_version": GENERATOR_VERSION,
            "source_modified_date": normalized.get("modified_date"),
            "normalized": normalized,
        }
        header_line = f"<!-- psi-context-cache: {json.dumps(header, separators=(',', ':'), ensure_ascii=False)} -->"
        path = self._cache_path(investigation_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(header_line + "\n" + _render_markdown(investigation_id, normalized), encoding="utf-8")


def _value(value: object) -> str:
    if value is None or value == "" or value == []:
        return "Not provided"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _render_markdown(investigation_id: str, normalized: dict) -> str:
    """Render the human-readable body of the context cache file."""
    lines = [
        f"# {investigation_id}: {_value(normalized.get('title'))}",
        "",
        "## Summary",
        "",
        f"- **Research area:** {_value(normalized.get('research_area'))}",
        f"- **Sub-research area:** {_value(normalized.get('sub_research_area'))}",
        f"- **Project type:** {_value(normalized.get('project_type'))}",
        f"- **DOI:** {_value(normalized.get('doi'))}",
        f"- **Public:** {_value(normalized.get('public'))}",
        f"- **Release date:** {_value(normalized.get('release_date'))}",
        f"- **Modified date:** {_value(normalized.get('modified_date'))}",
        "",
    ]
    for heading, key in (
        ("Objective", "objective"),
        ("Approach", "approach"),
        ("Hypothesis", "hypothesis"),
        ("Research impacts", "research_impacts"),
        ("Related investigations", "related_investigations"),
    ):
        lines += [f"## {heading}", "", _value(normalized.get(key)), ""]
    lines += ["## Publications", ""]
    publications = [item for item in normalized.get("publications") or [] if isinstance(item, dict)][:20]
    if publications:
        for item in publications:
            doi = f" — DOI: {item['doi']}" if item.get("doi") else ""
            lines.append(f"- {_value(item.get('title'))}{doi}")
    else:
        lines.append("- None listed")
    lines.append("")
    return "\n".join(lines)
