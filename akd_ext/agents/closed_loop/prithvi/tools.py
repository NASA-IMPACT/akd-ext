"""CM1-specific MCP tool factory functions.

These functions create HostedMCPTool instances configured for the CM1
experiment management MCP server.
"""

from __future__ import annotations

import os

from agents import HostedMCPTool

from akd_ext._types import OpenAITool


def get_default_impl_tools() -> list[OpenAITool]:
    """Default MCP tools for Stage 4A. Uses job_submit to submit experiments."""
    url = os.environ.get("EXPERIMENT_STATUS_MCP_URL", "")
    if not url:
        return []  # No MCP server configured — Phase 2 will be skipped
    return [
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "Job_Management_Server",
                "allowed_tools": ["job_submit"],
                "require_approval": "never",
                "server_description": "MCP server for submitting CM1 experiment jobs to Temporal",
                "server_url": url,
                "authorization": os.environ.get("EXPERIMENT_STATUS_MCP_KEY"),
            }
        ),
    ]


def get_default_report_tools() -> list[OpenAITool]:
    """Default tools for the Research Report Generator. Uses job management MCP server."""
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
                "server_url": os.environ.get(
                    "EXPERIMENT_STATUS_MCP_URL",
                    "",  # No default — must be configured
                ),
                "authorization": os.environ.get("EXPERIMENT_STATUS_MCP_KEY"),
            }
        ),
    ]
