"""Unit tests for file attachment data models and resolvers."""

import base64
from unittest.mock import AsyncMock

import httpx
import pytest

from akd_ext.files import (
    FileAttachment,
    OpenAIFileAttachment,
    OpenAIFileResolver,
    URLFileAttachment,
    URLFileResolver,
)


# ── Data Model Tests ─────────────────────────────────────────────────


class TestFileAttachmentModels:
    def test_base_attachment(self):
        att = FileAttachment(file_id="f1", filename="test.txt")
        assert att.file_id == "f1"
        assert att.filename == "test.txt"
        assert att.mime_type == "application/octet-stream"

    def test_openai_attachment(self):
        att = OpenAIFileAttachment(file_id="f1", filename="report.pdf", openai_file_id="file-abc123")
        assert att.openai_file_id == "file-abc123"
        assert isinstance(att, FileAttachment)

    def test_openai_attachment_requires_openai_file_id(self):
        with pytest.raises(Exception):
            OpenAIFileAttachment(file_id="f1", filename="test.txt")

    def test_url_attachment(self):
        att = URLFileAttachment(file_id="f1", filename="data.csv", url="https://example.com/data.csv")
        assert att.url == "https://example.com/data.csv"
        assert isinstance(att, FileAttachment)

    def test_url_attachment_requires_url(self):
        with pytest.raises(Exception):
            URLFileAttachment(file_id="f1", filename="test.txt")

    def test_mime_type_override(self):
        att = URLFileAttachment(
            file_id="f1", filename="img.png", mime_type="image/png", url="https://example.com/img.png"
        )
        assert att.mime_type == "image/png"


# ── OpenAIFileResolver Tests ────────────────────────────────────────


class TestOpenAIFileResolver:
    @pytest.mark.asyncio
    async def test_resolve_returns_file_content_part(self):
        resolver = OpenAIFileResolver()
        att = OpenAIFileAttachment(file_id="f1", filename="report.pdf", openai_file_id="file-abc123")
        parts = await resolver.resolve(att)

        assert len(parts) == 1
        assert parts[0] == {"type": "input_file", "file_id": "file-abc123"}


# ── URLFileResolver Tests ───────────────────────────────────────────


class TestURLFileResolver:
    @pytest.mark.asyncio
    async def test_resolve_text_file(self):
        """Text file content is inlined with filename header."""
        resolver = URLFileResolver()
        resolver._fetch = AsyncMock(return_value=b"col1,col2\na,b")

        att = URLFileAttachment(
            file_id="f1", filename="data.csv", mime_type="text/csv", url="https://example.com/data.csv"
        )
        parts = await resolver.resolve(att)

        assert len(parts) == 1
        assert parts[0]["type"] == "input_text"
        assert "[File: data.csv]" in parts[0]["text"]
        assert "col1,col2" in parts[0]["text"]
        resolver._fetch.assert_awaited_once_with("https://example.com/data.csv")

    @pytest.mark.asyncio
    async def test_resolve_image_file(self):
        """Image file is base64-encoded as image_url content part."""
        image_bytes = b"\x89PNG\r\n\x1a\n"  # PNG header
        resolver = URLFileResolver()
        resolver._fetch = AsyncMock(return_value=image_bytes)

        att = URLFileAttachment(
            file_id="f1", filename="img.png", mime_type="image/png", url="https://example.com/img.png"
        )
        parts = await resolver.resolve(att)

        assert len(parts) == 2
        assert parts[0]["type"] == "input_image"
        expected_b64 = base64.b64encode(image_bytes).decode("utf-8")
        assert parts[0]["image_url"] == f"data:image/png;base64,{expected_b64}"
        assert parts[1]["type"] == "input_text"
        assert "img.png" in parts[1]["text"]

    @pytest.mark.asyncio
    async def test_resolve_with_custom_client(self):
        """Resolver accepts a custom client."""
        resolver = URLFileResolver(timeout=60.0)
        resolver._fetch = AsyncMock(return_value=b"hello")

        att = URLFileAttachment(
            file_id="f1", filename="file.txt", mime_type="text/plain", url="https://example.com/file.txt"
        )
        parts = await resolver.resolve(att)

        assert parts[0]["type"] == "input_text"
        assert "hello" in parts[0]["text"]

    @pytest.mark.asyncio
    async def test_resolve_http_error_raises(self):
        """HTTP errors propagate."""
        resolver = URLFileResolver()
        resolver._fetch = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not Found",
                request=httpx.Request("GET", "https://example.com/missing.txt"),
                response=httpx.Response(404),
            )
        )

        att = URLFileAttachment(
            file_id="f1", filename="missing.txt", mime_type="text/plain", url="https://example.com/missing.txt"
        )

        with pytest.raises(httpx.HTTPStatusError):
            await resolver.resolve(att)
