"""Barebone tests for ArtifactStore: load, read, write."""

from akd_ext.artifacts import Artifact, ArtifactStore


class _MemStore(ArtifactStore[str]):
    async def load_artifacts(self):
        self["test.md"] = Artifact[str](path="test.md", content="hi")
        return self

    async def read_artifact(self, path: str) -> Artifact[str]:
        return self[path]

    async def write_artifact(self, artifact: Artifact[str]) -> Artifact[str]:
        self[artifact.path] = artifact
        return artifact


async def test_load():
    store = await _MemStore(root="mem://").load_artifacts()
    assert "test.md" in store


async def test_read():
    store = await _MemStore(root="mem://").load_artifacts()
    assert (await store.read_artifact("test.md")).content == "hi"


async def test_write():
    store = _MemStore(root="mem://")
    await store.write_artifact(Artifact[str](path="new.md", content="fresh"))
    assert (await store.read_artifact("new.md")).content == "fresh"
