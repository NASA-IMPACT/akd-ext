"""Tests for PDF parser tool routing and errors."""

import pytest

from akd_ext.mcp.registry import MCPToolRegistry
from akd_ext.tools.pdf_parser import (
    DoclingScraperConfig,
    PDFParserTool,
    PDFParserToolConfig,
    PDFParserToolInputSchema,
    _normalize_url_or_path,
)


@pytest.mark.asyncio
async def test_pdf_parser_defaults_fast_to_akd_simple(monkeypatch):
    tool = PDFParserTool(config=PDFParserToolConfig(akd_simple_config={"foo": "bar"}))

    async def fake_simple(url_or_path, config=None):
        return {"content": "simple", "metadata": {"source": url_or_path, "config": config}}

    def fake_scraper_to_result(out):
        return out

    monkeypatch.setattr("akd_ext.tools.pdf_parser._run_akd_simple", fake_simple)
    monkeypatch.setattr("akd_ext.tools.pdf_parser._scraper_to_result", fake_scraper_to_result)

    result = await tool.arun(
        PDFParserToolInputSchema(
            url_or_path="https://example.com/test.pdf",
            mode="fast",
        )
    )

    assert result.content == "simple"
    assert result.metadata["backend"] == "akd_simple"
    assert result.metadata["config"] == {"foo": "bar"}


@pytest.mark.asyncio
async def test_pdf_parser_defaults_non_fast_to_akd_docling(monkeypatch):
    tool = PDFParserTool(
        config=PDFParserToolConfig(
            akd_docling_config=DoclingScraperConfig(pdf_mode="accurate", do_table_structure=False, use_ocr=True)
        )
    )

    async def fake_docling(url_or_path, mode, config=None):
        return {"content": f"docling-{mode}", "metadata": {"source": url_or_path, "config": config}}

    def fake_scraper_to_result(out):
        return out

    monkeypatch.setattr("akd_ext.tools.pdf_parser._run_akd_docling", fake_docling)
    monkeypatch.setattr("akd_ext.tools.pdf_parser._scraper_to_result", fake_scraper_to_result)

    result = await tool.arun(
        PDFParserToolInputSchema(
            url_or_path="https://example.com/test.pdf",
            mode="accurate",
        )
    )

    assert result.content == "docling-accurate"
    assert result.metadata["backend"] == "akd_docling"
    assert isinstance(result.metadata["config"], DoclingScraperConfig)
    assert result.metadata["config"].use_ocr is True


@pytest.mark.asyncio
async def test_pdf_parser_unsupported_backend(monkeypatch):
    tool = PDFParserTool()

    # Bypass schema validation intentionally to test runtime fallback branch.
    params = PDFParserToolInputSchema.model_construct(
        url_or_path="https://example.com/test.pdf",
        mode="fast",
        backend_hint="unknown_backend",
        return_format="markdown",
    )

    with pytest.raises(ValueError, match="Unsupported backend"):
        await tool._arun(params)


def test_pdf_parser_registered_in_mcp_registry():
    import akd_ext.tools  # noqa: F401

    tool_names = {tool.__name__ for tool in MCPToolRegistry().get_tools()}
    assert "PDFParserTool" in tool_names


def test_normalize_local_windows_path_keeps_path():
    normalized = _normalize_url_or_path("C:/temp/file.pdf")
    assert normalized.lower().endswith("file.pdf")
