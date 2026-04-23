"""Barebone tests for LocalArtifactStore: load, read, write."""

from pathlib import Path

from akd_ext.artifacts import Artifact
from akd_ext.artifacts.stores.local import LocalArtifactStore


async def test_load(artifact_tree: Path):
    store = await LocalArtifactStore(root=str(artifact_tree)).load_artifacts()
    assert len(store) == 3
    assert "index.md" in store
    assert "contexts/index.md" in store
    assert "contexts/role.md" in store
    # non-markdown file is filtered out by default supported_extensions
    assert "data.json" not in store


async def test_read(artifact_tree: Path):
    store = await LocalArtifactStore(root=str(artifact_tree)).load_artifacts()
    artifact = await store.read_artifact("contexts/role.md")
    assert artifact.path == "contexts/role.md"
    assert artifact.content.strip() == "# Role"


async def test_write(artifact_tree: Path):
    store = await LocalArtifactStore(root=str(artifact_tree)).load_artifacts()
    stored = await store.write_artifact(Artifact(path="notes/todo.md", content="# Todo"))
    assert stored.path == "notes/todo.md"
    # file exists on disk
    assert (artifact_tree / "notes" / "todo.md").read_text() == "# Todo"
    # cache updated
    assert "notes/todo.md" in store
