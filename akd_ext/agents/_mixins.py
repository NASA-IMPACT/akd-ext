"""Mixins for agent capabilities."""

from __future__ import annotations

from typing import Any

from akd._base import RunContext

from akd_ext.files import DEFAULT_RESOLVERS, FileAttachment, FileResolver


class FileAttachmentMixin:
    """Mixin that gives any agent file attachment capability.

    Lightweight orchestration only — all resolution logic lives in FileResolver implementations.
    Add to an agent's inheritance to enable file context injection before LLM calls.

    Usage:
        class MyAgent(FileAttachmentMixin, BaseAgent[In, Out]):
            ...

    The mixin reads ``file_attachments`` from RunContext (passed as an extra field)
    and resolves them into multipart content parts injected into the last user message.
    """

    file_resolvers: dict[type[FileAttachment], FileResolver] = DEFAULT_RESOLVERS

    async def _resolve_and_inject_files(
        self,
        messages: list[dict[str, Any]],
        run_context: RunContext,
    ) -> None:
        """Resolve file attachments and inject content into the last user message."""

        attachments: list[FileAttachment] = getattr(run_context, "file_attachments", [])
        print("??????", attachments)

        if not attachments:
            return

        # Find last user message and convert to multipart content array
        for msg in reversed(messages):
            if msg.get("role") == "user":
                existing = msg["content"]
                parts = [{"type": "text", "text": existing}] if isinstance(existing, str) else list(existing)
                for att in attachments:
                    resolver = self.file_resolvers.get(type(att))
                    if resolver is None:
                        raise TypeError(f"No resolver registered for attachment type {type(att).__name__}")
                    parts.extend(await resolver.resolve(att))
                msg["content"] = parts
                break

        print("2*******")
        print(messages)
        print("*******")
