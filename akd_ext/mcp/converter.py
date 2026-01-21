"""MCP Tool Converter - Converts akd BaseTool to FastMCP compatible functions."""

from collections.abc import Callable
from inspect import Signature, Parameter
from typing import Awaitable, Any

from fastmcp import FastMCP
from akd.tools._base import BaseTool


def tool_converter(tool: BaseTool) -> Callable[..., Awaitable[Any]]:
    """
    Convert akd BaseTool to FastMCP-compatible async function.

    Args:
        tool: An instance of akd BaseTool to convert. Must have input_schema defined.

    Returns:
        A FastMCP compatible async function with proper signature and metadata.

    Example:
        tool = DummyTool()
        mcp_func = tool_converter(tool)
        result = await mcp_func(query="hello")
    """
    tool_name = getattr(tool, "name", None) or tool.__class__.__name__
    tool_description = getattr(tool, "description", None) or ""
    InputModel = tool.input_schema

    # Build signature from InputModel fields
    field_info = InputModel.model_fields
    parameters = []
    annotations = {}

    for field_name, field in field_info.items():
        field_type = field.annotation
        annotations[field_name] = field_type

        if field.default is not ...:
            param = Parameter(field_name, Parameter.POSITIONAL_OR_KEYWORD, default=field.default, annotation=field_type)
        else:
            param = Parameter(field_name, Parameter.POSITIONAL_OR_KEYWORD, annotation=field_type)
        parameters.append(param)

    wrapper_sig = Signature(parameters)

    # Create async closure that captures InputModel and tool
    def _create_wrapper():
        async def _async_wrapper(*args, **kwargs):
            bound = wrapper_sig.bind(*args, **kwargs)
            bound.apply_defaults()
            params = InputModel(**bound.arguments)
            result = await tool.arun(params)
            return result.model_dump()

        return _async_wrapper

    mcp_tool_wrapper = _create_wrapper()

    # Set function metadata
    mcp_tool_wrapper.__name__ = tool_name
    mcp_tool_wrapper.__doc__ = tool_description
    mcp_tool_wrapper.__signature__ = wrapper_sig
    mcp_tool_wrapper.__annotations__ = annotations

    return mcp_tool_wrapper


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
