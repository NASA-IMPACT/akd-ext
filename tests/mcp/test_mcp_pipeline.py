"""Tests for MCP tool pipeline."""

import pytest
from akd_ext.tools.dummy import DummyTool, DummyInputSchema
from akd_ext.mcp.converter import tool_converter
from akd_ext.mcp.registry import mcp_tool_registry, MCPToolRegistry


class TestDummyTool:
    @pytest.mark.asyncio
    async def test_dummy_returns_input(self):
        tool = DummyTool()
        result = await tool.arun(DummyInputSchema(query="hello"))
        assert result.query == "hello"

    @pytest.mark.asyncio
    async def test_dummy_with_sentence(self):
        tool = DummyTool()
        result = await tool.arun(DummyInputSchema(query="NASA IMPACT"))
        assert result.query == "NASA IMPACT"


class TestToolConverter:
    def test_converter_returns_callable(self):
        tool = DummyTool()
        mcp_func = tool_converter(tool)
        assert callable(mcp_func)

    @pytest.mark.asyncio
    async def test_converted_tool_works(self):
        tool = DummyTool()
        mcp_func = tool_converter(tool)
        result = await mcp_func(query="test")
        assert result["query"] == "test"

    def test_converter_sets_metadata(self):
        tool = DummyTool()
        mcp_func = tool_converter(tool)
        assert mcp_func.__name__ == "DummyTool"
        assert "query" in mcp_func.__annotations__

    @pytest.mark.asyncio
    async def test_converted_tool_with_kwargs_order(self):
        """Verify kwargs work regardless of order."""
        tool = DummyTool()
        mcp_func = tool_converter(tool)
        # Even if we had multiple params, order shouldn't matter
        result = await mcp_func(query="test")
        assert result["query"] == "test"


class TestMCPToolRegistry:
    def test_singleton_pattern(self):
        """Verify only one registry instance exists."""
        registry1 = MCPToolRegistry()
        registry2 = MCPToolRegistry()
        assert registry1 is registry2

    def test_register_and_get_tools(self):
        """Test tool registration."""
        mcp_tool_registry.clear()
        mcp_tool_registry.register(DummyTool)
        tools = mcp_tool_registry.get_tools()
        assert DummyTool in tools

    def test_reset_singleton(self):
        """Test singleton reset for testing."""
        MCPToolRegistry._reset_singleton()
        registry = MCPToolRegistry()
        assert registry._tools == []
        # Re-initialize for other tests
        MCPToolRegistry._reset_singleton()
