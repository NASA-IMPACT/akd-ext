"""Decorators for MCP tool registration."""

from akd.tools._base import BaseTool
from akd_ext.mcp.registry import mcp_tool_registry


def mcp_tool(cls: type[BaseTool]) -> type[BaseTool]:
    """
    Decorator to mark a BaseTool class for automatic MCP registration.

    Args:
        cls: BaseTool subclass to register.

    Returns:
        The same class, marked with _is_mcp_tool = True.

    Raises:
        TypeError: If cls is not a BaseTool subclass.

    Usage:
        @mcp_tool
        class MyTool(BaseTool):
            ...
    """
    if not issubclass(cls, BaseTool):
        raise TypeError(f"@mcp_tool can only be applied to BaseTool subclasses, got {cls}")

    cls._is_mcp_tool = True
    mcp_tool_registry.register(cls)

    return cls
