"""MCP Tool Registry"""

from akd.tools._base import BaseTool


class MCPToolRegistry:
    """
    MCP Tool registry implements singleton pattern to ensure consistent tool registration.

    Example:
        from akd_ext.mcp.registry import mcp_tool_registry

        mcp_tool_registry.register(MyTool)
        tools = mcp_tool_registry.get_tools()
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the registry."""
        if not MCPToolRegistry._initialized:
            self._tools: list[type[BaseTool]] = []
            MCPToolRegistry._initialized = True

    def register(self, tool_class: type[BaseTool]) -> type[BaseTool]:
        """
        Register a tool class.

        Args:
            tool_class: BaseTool subclass to register.

        Returns:
            The same tool class.

        Example:
            mcp_tool_registry.register(DummyTool)
        """
        if tool_class not in self._tools:
            self._tools.append(tool_class)
        return tool_class

    def get_tools(self) -> list[type[BaseTool]]:
        """
        Get all registered tool classes.

        Returns:
            Copy of the registered tools list.

        Example:
            tools = mcp_tool_registry.get_tools()  # [DummyTool, AnotherTool]
        """
        return self._tools.copy()

    def clear(self):
        """Clear all registered tools."""
        self._tools.clear()

    @classmethod
    def _reset_singleton(cls) -> None:
        """Reset the singleton instance (for testing purposes only)."""
        cls._instance = None
        cls._initialized = False


mcp_tool_registry = MCPToolRegistry()
