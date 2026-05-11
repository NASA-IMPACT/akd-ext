"""Shared utilities for akd-ext."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx
from loguru import logger


def sniff_image(blob: bytes) -> tuple[str, str] | None:
    """Detect (mime, ext) from magic bytes, else None."""
    if blob.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if blob[:3] == b"\xff\xd8\xff":
        return "image/jpeg", ".jpg"
    if blob[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif", ".gif"
    if len(blob) >= 12 and blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
        return "image/webp", ".webp"
    return None


def slug_of(url: str) -> str:
    """Extract a short filename slug from a URL."""
    return url.rstrip("/").split("/")[-1].split("?")[0]


async def download_images(
    urls: list[str],
    tmpdir: Path,
    concurrency: int = 8,
    timeout: float = 60.0,
) -> list[dict[str, Any]]:
    """Download image URLs into *tmpdir* with bounded concurrency.

    Returns successful items (in original order) as dicts with keys:
    ``url``, ``slug``, ``bytes``, ``mime``.
    Failed or non-image downloads are logged and skipped.
    """
    sem = asyncio.Semaphore(concurrency)

    async def fetch(client: httpx.AsyncClient, url: str) -> dict[str, Any] | None:
        async with sem:
            try:
                r = await client.get(url, follow_redirects=True)
                r.raise_for_status()
            except Exception as exc:
                logger.warning(f"[download_images] failed {url}: {exc!r}")
                return None
            sniff = sniff_image(r.content)
            if sniff is None:
                logger.warning(f"[download_images] unsupported format for {url}; skipping.")
                return None
            mime, ext = sniff
            slug = slug_of(url)
            (tmpdir / f"{slug}{ext}").write_bytes(r.content)
            return {"url": url, "slug": slug, "bytes": r.content, "mime": mime}

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        results = await asyncio.gather(*[fetch(client, u) for u in urls])
    return [r for r in results if r is not None]


async def download_image_batch(
    urls: list[str],
    concurrency: int = 8,
    timeout: float = 60.0,
) -> list[dict[str, Any]]:
    """Download image URLs into a temporary directory.

    Convenience wrapper around :func:`download_images` that manages its own
    temp directory.  Returns the same list of dicts (``url``, ``slug``,
    ``bytes``, ``mime``).
    """
    import tempfile

    with tempfile.TemporaryDirectory(prefix="image_batch_") as tmp:
        return await download_images(
            urls, Path(tmp), concurrency=concurrency, timeout=timeout,
        )
