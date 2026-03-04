"""MCP Tool Converter - Converts AKDTool to FastMCP compatible functions."""

from collections.abc import Callable
from typing import Awaitable, Any

from fastmcp import FastMCP

from akd_ext._types import AKDTool


def tool_converter(tool: AKDTool) -> Callable[..., Awaitable[Any]]:
    """Convert AKDTool to FastMCP-compatible async function.

    Uses ``AKDTool.as_function(mode="python")`` which returns
    ``model_dump()`` dict — what FastMCP expects from tool functions.

    Args:
        tool: An instance of AKDTool to convert.

    Returns:
        A FastMCP compatible async function with proper signature and metadata.

    Example:
        tool = DummyTool()
        mcp_func = tool_converter(tool)
        result = await mcp_func(query="hello")  # returns dict
    """
    return tool.as_function(mode="python")


def register_mcp_tool(mcp_func: Callable[..., Awaitable[Any]], mcp: FastMCP) -> Callable[..., Awaitable[Any]]:
    """
    Register a converted function with FastMCP server.

    Args:
        mcp_func: The converted MCP-compatible function (from tool_converter)
        mcp: FastMCP server instance to register the tool with

    Returns:
        The registered function.

    Example:
        mcp_func = tool_converter(DummyTool())
        register_mcp_tool(mcp_func, mcp)  # Tool now available via MCP
    """
    mcp.tool(name=mcp_func.__name__, description=mcp_func.__doc__ or "")(mcp_func)

    return mcp_func
