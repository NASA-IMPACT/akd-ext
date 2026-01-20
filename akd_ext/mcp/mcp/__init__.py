"""MCP (Model Context Protocol) module for akd_ext."""

from akd_ext.mcp.converter import tool_converter, register_mcp_tool
from akd_ext.mcp.decorators import mcp_tool
from akd_ext.mcp.registry import MCPToolRegistry, mcp_tool_registry
from akd_ext.mcp.server import mcp

__all__ = [
    "tool_converter",
    "register_mcp_tool",
    "mcp_tool",
    "MCPToolRegistry",
    "mcp_tool_registry",
    "mcp",
]
