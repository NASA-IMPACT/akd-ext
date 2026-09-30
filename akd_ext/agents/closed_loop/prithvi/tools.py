"""Prithvi-specific MCP tool wiring for closed-loop stages.

All tools are served by the hosted MCP server (PRITHVI_MCP_URL).
Each stage gets a filtered view via ``allowed_tools``:

- Stage 3: geocode, reverse_geocode
- Stage 4: screen_events, check_screening, job_submit
- Stage 5: job_status, job_plot
"""

from __future__ import annotations

import os

from agents import HostedMCPTool

from akd_ext._types import OpenAITool

_SERVER_LABEL = "Prithvi_Temporal_MCP_Server"


def _prithvi_mcp_tool(allowed_tools: list[str], description: str) -> list[OpenAITool]:
    """Build a single HostedMCPTool restricted to ``allowed_tools``.

    Returns an empty list unless BOTH ``PRITHVI_MCP_API_KEY`` and
    ``PRITHVI_MCP_URL`` are set, so a stage degrades to tool-less rather than
    building a tool with an empty ``server_url`` (which fails at the LLM API).
    All Prithvi stages share one MCP server and differ only in ``allowed_tools``.
    """
    api_key = os.environ.get("PRITHVI_MCP_API_KEY")
    url = os.environ.get("PRITHVI_MCP_URL")
    if not api_key or not url:
        return []
    return [
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": _SERVER_LABEL,
                "allowed_tools": allowed_tools,
                "require_approval": "never",
                "server_description": description,
                "server_url": url,
                "headers": {"Authorization": f"Bearer {api_key}"},
            }
        ),
    ]


# ---------------------------------------------------------------------------
# Public API — tool lists for each stage (all tools served by hosted MCP)
# ---------------------------------------------------------------------------


def get_default_spec_builder_tools() -> list[OpenAITool]:
    """Stage 3 (Workflow Spec Builder): geocode + reverse_geocode.

    Used when the user names a region or supplies a custom AOI while the spec
    is being built.
    """
    return _prithvi_mcp_tool(
        ["geocode", "reverse_geocode"],
        "Prithvi pipeline MCP server — geocode (place name → bbox) and "
        "reverse_geocode (bbox → US state/county) for resolving regions and "
        "custom AOIs while building the workflow spec.",
    )


def get_default_impl_tools() -> list[OpenAITool]:
    """Stage 4 (Experiment Implementation): screen_events + check_screening + job_submit.

    screen_events starts an async screening job (returns a task_id),
    check_screening polls it, and job_submit pushes the validated config onto
    the Temporal workflow queue.
    """
    return _prithvi_mcp_tool(
        ["screen_events", "check_screening", "job_submit"],
        "Prithvi pipeline Temporal workflow MCP server — screen flood/burn "
        "events (screen_events starts a job, check_screening polls until done) "
        "and submit pipeline configs.",
    )


def get_default_report_tools() -> list[OpenAITool]:
    """Stage 5 (Experiment Analysis): job_status + job_plot."""
    return _prithvi_mcp_tool(
        ["job_status", "job_plot"],
        "Prithvi pipeline MCP server for checking job status and fetching "
        "result figures/tables/maps.",
    )
