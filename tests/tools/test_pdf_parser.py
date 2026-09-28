"""Tests for PDF parser tool routing and errors."""

import pytest

from akd_ext.mcp.registry import MCPToolRegistry
from akd_ext.tools.pdf_parser import (
    PDFParserTool,
    PDFParserToolInputSchema,
    _normalize_url_or_path,
)


@pytest.mark.asyncio
async def test_pdf_parser_routes_to_akd_simple(monkeypatch):
    tool = PDFParserTool()

    async def fake_simple(url):
        return {"content": "simple", "metadata": {"source": url}}

    def fake_scraper_to_result(out):
        return out

    monkeypatch.setattr("akd_ext.tools.pdf_parser._run_akd_simple", fake_simple)
    monkeypatch.setattr("akd_ext.tools.pdf_parser._scraper_to_result", fake_scraper_to_result)

    result = await tool.arun(
        PDFParserToolInputSchema(url="https://example.com/test.pdf"),
    )

    assert result.content == "simple"
    assert result.metadata["backend"] == "akd_simple"
    assert result.metadata["return_format"] == "markdown"


def test_pdf_parser_registered_in_mcp_registry():
    import akd_ext.tools  # noqa: F401

    tool_names = {tool.__name__ for tool in MCPToolRegistry().get_tools()}
    assert "PDFParserTool" in tool_names


def test_normalize_local_windows_path_keeps_path():
    normalized = _normalize_url_or_path("C:/temp/file.pdf")
    assert normalized.lower().endswith("file.pdf")
