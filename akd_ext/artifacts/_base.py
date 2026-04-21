from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Self

from pydantic import BaseModel, Field, field_validator


class Artifact[T](BaseModel):
    path: str = Field(..., description="Slug that identifies the artifact.")
    name: str | None = Field(default=None, description="Name of the artifact.")
    description: str | None = Field(
        default=None,
        description="One-line summary; helps an agent decide whether to load this artifact.",
    )
    content: T = Field(..., description="The content of the artifact.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Backend-specific escape hatch (mime type, commit sha, author, tags, etc.). Could be loaded from frontmatter as well if md file",
    )
    created_at: datetime | None = Field(
        default=None,
        description=(
            "When the artifact was first stored. Output-only: populated by the store "
            "on read; ignored on write (stores set it according to their backend)."
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        description=(
            "When the artifact was last modified. Output-only: populated by the store "
            "on read; ignored on write (stores set it according to their backend)."
        ),
    )

    @field_validator("path")
    @classmethod
    def _normalize_path(cls, v: str) -> str:
        """Reject clearly broken paths; normalize obvious oddities.

        - Rejects: empty/whitespace-only, null byte, '..' segments.
        - Normalizes: leading '/' stripped, '//' collapsed, './' collapsed.
        - Backend-specific path-traversal defense still lives in each store.
        """
        v = v.strip()
        if not v:
            raise ValueError("path cannot be empty")
        if "\0" in v:
            raise ValueError("path contains null byte")
        p = PurePosixPath(v.lstrip("/"))
        if ".." in p.parts:
            raise ValueError(f"path contains '..' segment: {v!r}")
        return str(p)


class ArtifactStore[T](ABC):
    """
    Abstract storage for artifacts keyed by path.

    The in-memory `self._artifacts` dict is the authoritative index for listing.
    Subclasses are responsible for:
      - Populating `self._artifacts` (eagerly in __init__ or lazily on read).
      - Keeping it in sync on writes.
      - Overriding `refresh()` to re-sync from the backend if needed.

    Timestamp fields (`created_at`, `updated_at`) on Artifact are output-only:
    stores populate them on read; caller-supplied values on write are ignored.
    """

    def __init__(
        self,
        root: str,
        *,
        index_file: str | None = "index.md",
        debug: bool = False,
    ) -> None:
        self.root = root
        self.index_file = index_file
        self.debug = bool(debug)
        self._artifacts: dict[str, Artifact[T]] = {}

    def index_for(self, dir_path: str = "") -> Artifact[T] | None:
        """Return the designated index artifact for a directory (or the
        root overview if `dir_path` is empty). Returns None if `index_file`
        is None or no such artifact is cached.

        Transparent across backend conventions: set `index_file` to
        "index.md" (dev/local), "README.md" (GitHub), "SKILL.md" (Anthropic
        skills), or "AGENT.md" (agent manifests) per store."""
        if not self.index_file:
            return None
        dir_path = dir_path.strip("/")
        if not dir_path:
            return self._artifacts.get(self.index_file)
        key = str(PurePosixPath(dir_path) / self.index_file)
        return self._artifacts.get(key)

    @abstractmethod
    async def read_artifact(self, path: str) -> Artifact[T]:
        """Fetch a single artifact (content included). Raise on miss.
        Implementations MAY cache the result into `self._artifacts`."""
        raise NotImplementedError()

    @abstractmethod
    async def write_artifact(self, artifact: Artifact[T]) -> Artifact[T]:
        """Persist to the backend. Returns the stored artifact with timestamps
        populated. Implementations MUST update `self._artifacts` to keep the
        cache consistent."""
        raise NotImplementedError()

    @abstractmethod
    async def load_artifacts(self) -> Self:
        """Populate `self._artifacts` from the backend and return `self` for
        fluent chaining. Called once after construction (and again by
        `refresh()`). Functional counterpart of ada's
        `@model_validator(mode='after')` loader, but explicit so the base
        class does not depend on pydantic."""
        raise NotImplementedError()

    async def refresh(self) -> Self:
        """Re-sync the cache from the backend. Clears in-memory state and
        re-invokes `load_artifacts()`. Returns `self` for fluent chaining."""
        self._artifacts.clear()
        await self.load_artifacts()
        return self

    async def list_artifacts(self, prefix: str | None = None) -> list[Artifact[T]]:
        """List from the in-memory cache. Override only if the backend must be
        queried live."""
        if prefix is None:
            return list(self._artifacts.values())
        return [a for k, a in self._artifacts.items() if k.startswith(prefix)]

    def keys(self, prefix: str = "") -> list[str]:
        return [k for k in self._artifacts if k.startswith(prefix)]

    def __getitem__(self, path: str) -> Artifact[T]:
        """Cache-only lookup. Raises KeyError on miss. For async
        fetch-if-missing, use `await store.read_artifact(path)`."""
        return self._artifacts[path]

    def __setitem__(self, path: str, artifact: Artifact[T]) -> None:
        """Cache-only write. Does NOT persist to the backend. Subclasses use
        this inside `write_artifact` / `read_artifact` to keep the cache in
        sync after real I/O."""
        self._artifacts[path] = artifact

    def __delitem__(self, path: str) -> None:
        """Cache-only removal. Does NOT delete from the backend."""
        del self._artifacts[path]

    def __contains__(self, path: str) -> bool:
        return path in self._artifacts

    def __len__(self) -> int:
        return len(self._artifacts)

    def __iter__(self):
        return iter(self._artifacts)

    def __str__(self) -> str:
        """Flat bulleted list of paths (with descriptions where available),
        suitable for dropping into an LLM system prompt. Each line contains
        the exact path the caller should pass to `read_artifact`."""
        lines = []
        for path in sorted(self._artifacts):
            a = self._artifacts[path]
            desc = f" — {a.description}" if a.description else ""
            lines.append(f"- {path}{desc}")
        return "\n".join(lines)
