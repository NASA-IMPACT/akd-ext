from datetime import datetime
from pathlib import Path
from typing import Self

from loguru import logger

from akd_ext.artifacts._base import Artifact, ArtifactStore


class LocalArtifactStore(ArtifactStore[str]):
    """Local file-system based artifact store.

    Treats `self.root` as a directory on disk. `load_artifacts()` eagerly
    walks the tree, filtering by `self.supported_extensions` and reading
    each matched file as UTF-8 text into the cache.

    Caching strategy: reads are freshness-checked against disk — the
    cached copy is served only if its `updated_at` matches the file's
    current mtime; otherwise the file is re-read and the cache is
    refreshed. This keeps the store in sync with external edits without
    requiring an explicit refresh.

    Writes flush to disk (creating parent directories as needed) and
    update the cache with the post-write mtime.

    Path traversal is rejected at both the model level (via
    `Artifact.path` validation) and the store level (via `_resolve`,
    which rejects any path that escapes `self.root` via `..` or
    symlinks).
    """

    def _resolve(self, rel_path: str) -> Path:
        """Resolve a relative path to an absolute path under root.

        Args:
            rel_path: Path relative to `self.root`.

        Returns:
            Absolute filesystem path.

        Raises:
            ValueError: If the resolved path escapes `self.root`.
        """
        root_abs = Path(self.root).resolve()
        full = (Path(self.root) / rel_path).resolve()
        if not full.is_relative_to(root_abs):
            raise ValueError(f"path escapes store root: {rel_path!r}")
        return full

    async def load_artifacts(self) -> Self:
        """Load all available artifacts into the cache.

        Returns:
            Self, for fluent chaining.
        """
        root = Path(self.root)
        if not root.exists():
            logger.warning(
                "[LocalArtifactStore] root does not exist: {} — nothing to load",
                root,
            )
            return self
        for f in sorted(root.rglob("*")):
            if not f.is_file():
                continue
            rel = str(f.relative_to(root))
            if not self._is_supported(rel):
                continue
            st = f.stat()
            self[rel] = Artifact[str](
                path=rel,
                content=f.read_text(),
                updated_at=datetime.fromtimestamp(st.st_mtime),
            )
        return self

    async def read_artifact(self, path: str) -> Artifact[str]:
        """Load the content of an artifact.

        Args:
            path: Path of the artifact to load (e.g. "contexts/role.md").

        Returns:
            The artifact including its content.

        Raises:
            FileNotFoundError: If no artifact exists at that path.
        """
        full = self._resolve(path)
        if not full.is_file():
            if path in self:
                del self[path]
            raise FileNotFoundError(f"artifact not found: {path!r}")

        disk_mtime = datetime.fromtimestamp(full.stat().st_mtime)
        cached = self._artifacts.get(path)
        if cached is not None and cached.updated_at == disk_mtime:
            return cached

        artifact = Artifact[str](
            path=path,
            content=full.read_text(),
            updated_at=disk_mtime,
        )
        self[path] = artifact
        return artifact

    async def write_artifact(self, artifact: Artifact[str]) -> Artifact[str]:
        """Persist an artifact to disk.

        Args:
            artifact: Artifact to write. Its content is saved as UTF-8 text
                at the artifact's `path`.

        Returns:
            The stored artifact with `updated_at` set from disk.
        """
        full = self._resolve(artifact.path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(artifact.content)
        st = full.stat()
        stored = artifact.model_copy(update={"updated_at": datetime.fromtimestamp(st.st_mtime)})
        self[artifact.path] = stored
        if self.debug:
            logger.debug("[LocalArtifactStore] wrote: {}", stored)
        return stored
