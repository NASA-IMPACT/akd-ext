"""Barebone mocked tests for GitHubArtifactStore: load, read, write.

Uses the `github_client` injection kwarg rather than patching — see
`GitHubArtifactStore.__init__` docstring.
"""

from unittest.mock import MagicMock

import pytest
from github import UnknownObjectException

from akd_ext.artifacts import Artifact
from akd_ext.artifacts.stores.github import GitHubArtifactStore


def _tree_entry(path: str, sha: str, type_: str = "blob"):
    e = MagicMock()
    e.path = path
    e.sha = sha
    e.type = type_
    return e


def _content_file(content: str, sha: str):
    cf = MagicMock()
    cf.decoded_content = content.encode()
    cf.sha = sha
    cf.last_modified_datetime = None
    return cf


@pytest.fixture
def mock_github():
    """Return (github_client_mock, repo_mock) for tests to configure."""
    gh = MagicMock()
    repo = gh.get_repo.return_value
    return gh, repo


async def test_load(mock_github):
    gh, repo = mock_github
    repo.get_git_tree.return_value.tree = [
        _tree_entry("index.md", "sha1"),
        _tree_entry("data.json", "sha2"),  # filtered by supported_extensions
    ]
    repo.get_contents.return_value = _content_file("root", "sha1")

    store = await GitHubArtifactStore("akd/test", github_client=gh).load_artifacts()

    assert "index.md" in store
    assert "data.json" not in store
    assert store["index.md"].metadata["sha"] == "sha1"


async def test_read(mock_github):
    gh, repo = mock_github
    repo.get_git_tree.return_value.tree = []
    store = await GitHubArtifactStore("akd/test", github_client=gh).load_artifacts()
    store["foo.md"] = Artifact(path="foo.md", content="hi")

    got = await store.read_artifact("foo.md")
    assert got.content == "hi"


async def test_write(mock_github):
    gh, repo = mock_github
    repo.get_git_tree.return_value.tree = []
    repo.get_contents.side_effect = UnknownObjectException(404, {}, {})
    repo.create_file.return_value = {
        "content": _content_file("new", "new_sha"),
        "commit": MagicMock(),
    }

    store = await GitHubArtifactStore("akd/test", github_client=gh).load_artifacts()
    stored = await store.write_artifact(Artifact(path="new.md", content="hello"))

    repo.create_file.assert_called_once()
    assert stored.metadata["sha"] == "new_sha"
    assert "new.md" in store
