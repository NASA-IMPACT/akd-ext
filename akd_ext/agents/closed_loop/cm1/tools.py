"""CM1-specific MCP tool factory functions.

These functions create HostedMCPTool instances configured for the CM1
experiment management MCP server.
"""

from __future__ import annotations

import os

from agents import HostedMCPTool

from akd_ext._types import OpenAITool


def _mcp_auth_headers(api_key: str, url: str) -> dict[str, str]:
    """Auth header for the CM1 MCP server.

    Scheme resolution:
      1. Explicit ``CM1_MCP_AUTH`` env var (``bearer`` or ``x-api-key``) wins.
      2. Otherwise auto-detect: FastMCP Cloud (``*.fastmcp.app``) uses a
         bearer token; the production Temporal server uses ``X-API-Key``.
    """
    scheme = os.environ.get("CM1_MCP_AUTH", "").lower()
    if not scheme:
        scheme = "bearer" if "fastmcp.app" in url else "x-api-key"
    if scheme == "bearer":
        return {"Authorization": f"Bearer {api_key}"}
    return {"X-API-Key": api_key}


def get_default_impl_tools() -> list[OpenAITool]:
    """Default MCP tools for Stage 4A — uses the CM1 job-management MCP server.

    Allowed tools:
      - ``job_submit``: submit an experiment batch to the job-management server
      - ``jobs_list``: list previously submitted jobs (useful for dedup / resume checks)

    Configure via environment (BOTH ``CM1_MCP_URL`` and ``CM1_MCP_API_KEY`` are
    required; if either is missing the tool is skipped so the agent fails loudly
    with "no job tool" instead of silently falling back to a default endpoint
    that may be down):
      - ``CM1_MCP_URL``      — server URL (a FastMCP mock or the production server).
        Point this at a mock endpoint to get an instant job_id + workspace_name
        without waiting for a real ~2-hour experiment run.
      - ``CM1_MCP_API_KEY``  — credential.
      - ``CM1_MCP_AUTH``     — ``bearer`` or ``x-api-key`` (auto-detected from the
        URL if unset: ``*.fastmcp.app`` → bearer, otherwise x-api-key).
    """
    api_key = os.environ.get("CM1_MCP_API_KEY")
    url = os.environ.get("CM1_MCP_URL")
    if not api_key or not url:
        # Not configured (no silent default) — Stage 4 job submission is skipped.
        return []
    return [
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "CM1_Job_Management_Server",
                "allowed_tools": ["job_submit", "jobs_list"],
                "require_approval": "never",
                "server_description": "CM1 job-management MCP server — submit experiment batches and list job history.",
                "server_url": url,
                "headers": _mcp_auth_headers(api_key, url),
            }
        ),
    ]


def get_default_report_tools() -> list[OpenAITool]:
    """Default tools for the Research Report Generator. Uses job management MCP server.

    Auth is passed via ``headers`` (a real header dict), NOT a top-level
    ``authorization`` field: the OpenAI hosted-MCP tool_config only honors
    ``headers``. Sending ``authorization`` was silently ignored, so OpenAI
    connected to the (bearer-protected) FastMCP server with no credential, got
    a 401, and the Responses streaming call failed with a generic 500
    ("An error occurred while processing your request"). This mirrors
    ``get_default_impl_tools`` (which already worked).
    """
    # Prefer the dedicated status endpoint, but fall back to the CM1 job
    # server (same job_submit/job_status/job_plot contract) when it isn't
    # configured separately — newer deployments route everything through
    # CM1_MCP_* and don't set EXPERIMENT_STATUS_MCP_*.
    api_key = os.environ.get("EXPERIMENT_STATUS_MCP_KEY") or os.environ.get("CM1_MCP_API_KEY")
    url = os.environ.get("EXPERIMENT_STATUS_MCP_URL") or os.environ.get("CM1_MCP_URL")
    if not api_key or not url:
        # Not configured — skip the tool rather than emit one with no/blank auth
        # that 500s the model call.
        return []
    return [
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "Job_Management_Server",
                "allowed_tools": [
                    "job_status",
                    "job_plot",
                ],
                "require_approval": "never",
                "server_description": "MCP server for checking CM1 experiment job status and fetching result figures",
                "server_url": url,
                "headers": _mcp_auth_headers(api_key, url),
            }
        ),
    ]
