"""File attachment data models and resolvers for agent file context injection."""

from __future__ import annotations

import base64
from typing import Any, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel, Field


# ── Data Models ──────────────────────────────────────────────────────


class FileAttachment(BaseModel):
    """Base file attachment — shared metadata."""

    file_id: str = Field(..., description="Unique identifier from backend")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(default="application/octet-stream", description="MIME type of the file")


class OpenAIFileAttachment(FileAttachment):
    """File uploaded via OpenAI Files API."""

    openai_file_id: str = Field(..., description="OpenAI Files API file ID")


class URLFileAttachment(FileAttachment):
    """File accessible via URL (presigned S3, GCS signed, etc.)."""

    url: str = Field(..., description="URL to fetch content from")


# ── Resolver Protocol + Implementations ──────────────────────────────


@runtime_checkable
class FileResolver(Protocol):
    """Turns a FileAttachment into Chat Completions multipart content parts."""

    async def resolve(self, attachment: FileAttachment) -> list[dict[str, Any]]: ...


class OpenAIFileResolver:
    """Passes file_id natively to OpenAI — no fetching needed."""

    async def resolve(self, attachment: OpenAIFileAttachment) -> list[dict[str, Any]]:
        return [{"type": "input_file", "file_id": attachment.openai_file_id}]


class URLFileResolver:
    """Fetches content from URL and inlines it into the message."""

    def __init__(self, client: httpx.AsyncClient | None = None, timeout: float = 30.0):
        self._client = client
        self._timeout = timeout

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def _fetch(self, url: str) -> bytes:
        client = await self._get_client()
        response = await client.get(url)
        response.raise_for_status()
        return response.content

    async def resolve(self, attachment: URLFileAttachment) -> list[dict[str, Any]]:
        raw = await self._fetch(attachment.url)

        if attachment.mime_type.startswith("image/"):
            encoded = base64.b64encode(raw).decode("utf-8")
            return [
                {
                    "type": "input_image",
                    "image_url": f"data:{attachment.mime_type};base64,{encoded}",
                }
            ]

        # Text-based files
        # can replace it with same base-64 encoding too: {"type": "input_file", "filename": "doc.pdf", "file_data": "data:application/pdf;base64,..."}
        # however, if we sought to apply token minimization techniques, raw text is good.
        text = raw.decode("utf-8")
        return [{"type": "input_text", "text": f"[File: {attachment.filename}]\n{text}"}]


# ── Default Resolver Registry ────────────────────────────────────────

DEFAULT_RESOLVERS: dict[type[FileAttachment], FileResolver] = {
    OpenAIFileAttachment: OpenAIFileResolver(),
    URLFileAttachment: URLFileResolver(),
}
