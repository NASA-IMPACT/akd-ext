"""PDF parser tool using AKD core backends."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool
from akd.tools.scrapers.pdf_scrapers import (
    ScraperToolOutputSchema,
    SimplePDFScraper,
)
from pydantic import Field

from akd_ext.mcp import mcp_tool


class PDFParserToolInputSchema(InputSchema):
    """Input schema for PDF parsing."""

    url: str = Field(..., description="HTTP(S) URL to a PDF")
    return_format: Literal["markdown", "html", "json"] = Field(
        default="markdown",
        description="Preferred output format hint for backend parsing",
    )


class PDFParserToolOutputSchema(OutputSchema):
    """Output schema for parsed PDF content."""

    content: str = Field(..., description="Parsed text content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Parser and document metadata")


def _normalize_url_or_path(url: str) -> str:
    lower = url.lower()
    if lower.startswith(("http://", "https://", "file://")):
        return url

    p = Path(url).expanduser().resolve()
    as_uri = p.as_uri()
    local_path = str(p)

    if sys.platform.startswith("win"):
        return local_path
    return as_uri


async def _run_akd_simple(url: str, config: dict[str, Any] | None = None) -> ScraperToolOutputSchema:
    scraper = SimplePDFScraper(config=config)
    params = scraper.input_schema(url=_normalize_url_or_path(url))
    return await scraper.arun(params)


def _scraper_to_result(out: ScraperToolOutputSchema) -> dict[str, Any]:
    return {"content": out.content, "metadata": out.metadata.model_dump()}


@mcp_tool
class PDFParserTool(BaseTool[PDFParserToolInputSchema, PDFParserToolOutputSchema]):
    """Parse a PDF into LLM-ready text.

    Given an HTTP(S) URL to a PDF, returns the parsed text content plus a
    metadata dict (backend, return_format, plus parser/document metadata).

    Output text format is selectable via ``return_format``: ``markdown``
    (default), ``html``, or ``json``.

    Uses a simple PDF scraper backend — best for digital-native PDFs. Does
    not perform OCR (scanned or image-only PDFs will yield poor or empty
    text), does not discover or search for PDFs (URL must be supplied),
    and does not summarize.
    """

    input_schema = PDFParserToolInputSchema
    output_schema = PDFParserToolOutputSchema

    async def _arun(self, params: PDFParserToolInputSchema) -> PDFParserToolOutputSchema:
        result = _scraper_to_result(await _run_akd_simple(params.url))

        metadata = result.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {"raw_metadata": metadata}
        metadata["backend"] = "akd_simple"
        metadata["return_format"] = params.return_format

        return PDFParserToolOutputSchema(
            content=str(result.get("content", "") or ""),
            metadata=metadata,
        )
