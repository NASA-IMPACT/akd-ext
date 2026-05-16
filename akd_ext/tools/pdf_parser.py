"""PDF parser tool using AKD core backends."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from akd.tools.scrapers import (
    DoclingScraper,
    DoclingScraperConfig,
    ScraperToolOutputSchema,
    SimplePDFScraper,
)
from pydantic import Field

from akd_ext.mcp import mcp_tool

Mode = Literal["fast", "accurate", "ocr"]
BackendHint = Literal[
    "akd_simple",
    "akd_docling",
]


class PDFParserToolInputSchema(InputSchema):
    """Input schema for PDF parsing."""

    url_or_path: str = Field(..., description="HTTP(S) URL or local filesystem path to a PDF")
    mode: Mode = Field(default="accurate", description="Parsing mode: fast, accurate, or ocr")
    backend_hint: BackendHint | None = Field(
        default=None,
        description="Optional backend override (akd_simple or akd_docling)",
    )
    return_format: Literal["markdown", "html", "json"] = Field(
        default="markdown",
        description="Preferred output format hint for backend parsing",
    )


class PDFParserToolOutputSchema(OutputSchema):
    """Output schema for parsed PDF content."""

    content: str = Field(..., description="Parsed text content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Parser and document metadata")


class PDFParserToolConfig(BaseToolConfig):
    """Configuration for PDF parser backend scrapers."""

    akd_simple_config: dict[str, Any] | None = Field(
        default=None,
        description="Optional configuration forwarded to SimplePDFScraper.",
    )
    akd_docling_config: DoclingScraperConfig | None = Field(
        default=None,
        description="Optional configuration forwarded to DoclingScraper.",
    )


def _normalize_url_or_path(url_or_path: str) -> str:
    lower = url_or_path.lower()
    if lower.startswith(("http://", "https://", "file://")):
        return url_or_path

    p = Path(url_or_path).expanduser().resolve()
    as_uri = p.as_uri()
    local_path = str(p)

    if sys.platform.startswith("win"):
        return local_path
    return as_uri

async def _run_akd_simple(
    url_or_path: str, config: dict[str, Any] | None = None
) -> ScraperToolOutputSchema:
    scraper = SimplePDFScraper(config=config)
    params = scraper.input_schema(url=_normalize_url_or_path(url_or_path))
    return await scraper.arun(params)


async def _run_akd_docling(
    url_or_path: str, mode: Mode, config: DoclingScraperConfig | None = None
) -> ScraperToolOutputSchema:
    if mode == "fast":
        default_cfg = DoclingScraperConfig(pdf_mode="fast", do_table_structure=False, use_ocr=False)
    elif mode == "accurate":
        default_cfg = DoclingScraperConfig(pdf_mode="accurate", do_table_structure=True, use_ocr=False)
    else:
        default_cfg = DoclingScraperConfig(pdf_mode="accurate", do_table_structure=True, use_ocr=True)

    scraper = DoclingScraper(config=config or default_cfg)
    params = scraper.input_schema(url=_normalize_url_or_path(url_or_path))
    return await scraper.arun(params)


def _scraper_to_result(out: ScraperToolOutputSchema) -> dict[str, Any]:
    return {"content": out.content, "metadata": out.metadata.model_dump()}


@mcp_tool
class PDFParserTool(BaseTool[PDFParserToolInputSchema, PDFParserToolOutputSchema]):
    """Parse PDFs into LLM-ready content using AKD core backends."""

    input_schema = PDFParserToolInputSchema
    output_schema = PDFParserToolOutputSchema
    config_schema = PDFParserToolConfig

    async def _arun(self, params: PDFParserToolInputSchema) -> PDFParserToolOutputSchema:
        backend = params.backend_hint
        if backend is None:
            backend = "akd_simple" if params.mode == "fast" else "akd_docling"

        tool_config = self.config

        if backend == "akd_simple":
            result = _scraper_to_result(
                await _run_akd_simple(
                    params.url_or_path,
                    config=tool_config.akd_simple_config,
                )
            )
        elif backend == "akd_docling":
            result = _scraper_to_result(
                await _run_akd_docling(
                    params.url_or_path,
                    params.mode,
                    config=tool_config.akd_docling_config,
                )
            )
        else:
            raise ValueError(f"Unsupported backend: {backend!r}")

        metadata = result.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {"raw_metadata": metadata}
        metadata["backend"] = backend
        metadata["return_format"] = params.return_format

        return PDFParserToolOutputSchema(
            content=str(result.get("content", "") or ""),
            metadata=metadata,
        )
