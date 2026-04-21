from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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

    def __init__(self, debug: bool = False) -> None:
        self.debug = bool(debug)
        self._artifacts: dict[str, Artifact[T]] = {}

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
    async def load_artifacts(self) -> None:
        """Populate `self._artifacts` from the backend. Called once after
        construction (and again by `refresh()`). Functional counterpart of
        ada's `@model_validator(mode='after')` loader, but explicit so the
        base class does not depend on pydantic."""
        raise NotImplementedError()

    # ---------------- defaults built on the cache ----------------

    async def refresh(self) -> None:
        """Re-sync the cache from the backend. Clears in-memory state and
        re-invokes `load_artifacts()`. Callers use this after external writes."""
        self._artifacts.clear()
        await self.load_artifacts()

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

    def __contains__(self, path: str) -> bool:
        return path in self._artifacts

    def __len__(self) -> int:
        return len(self._artifacts)

    def __iter__(self):
        return iter(self._artifacts)
