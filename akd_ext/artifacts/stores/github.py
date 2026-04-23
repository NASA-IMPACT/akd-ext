from typing import Self

from akd_ext.artifacts._base import Artifact, ArtifactStore


class GitHubArtifactStore(ArtifactStore[str]):
    """GitHub-backed artifact store."""

    async def load_artifacts(self) -> Self:
        return self

    async def read_artifact(self, path: str) -> Artifact[str]:
        pass

    async def write_artifact(self, artifact: Artifact[str]) -> Artifact[str]:
        pass
