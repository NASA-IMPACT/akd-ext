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
    and resolves them into a new user message appended to the conversation.
    """

    file_resolvers: dict[type[FileAttachment], FileResolver] = DEFAULT_RESOLVERS

    async def _resolve_and_inject_files(
        self,
        run_context: RunContext,
    ) -> None:
        """Resolve file attachments and append as a new user message."""
        attachments: list[FileAttachment] = getattr(run_context, "file_attachments", [])
        if not attachments or not run_context:
            return

        parts: list[dict[str, Any]] = []
        for att in attachments:
            resolver = self.file_resolvers.get(type(att))
            if resolver is None:
                raise TypeError(f"No resolver registered for attachment type {type(att).__name__}")
            parts.extend(await resolver.resolve(att))

        if not parts:
            return

        if run_context.messages is None:
            run_context.messages = []

        run_context.messages.append({"role": "user", "content": parts})

        # Clear attachments so they aren't re-injected on subsequent runs
        run_context.file_attachments = []
