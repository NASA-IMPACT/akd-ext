from datetime import datetime
from pathlib import Path
from typing import Self

from loguru import logger

from akd_ext.artifacts._base import Artifact, ArtifactStore


class LocalArtifactStore(ArtifactStore[str]):
    """Local file-system based artifact store."""

    async def load_artifacts(self) -> Self:
        """Populate the cache by walking `self.root` and reading every file
        whose extension is in `self.supported_extensions`. Each artifact's
        path is its slug relative to root; `updated_at` is taken from the
        filesystem mtime. Returns `self` for fluent chaining."""
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
