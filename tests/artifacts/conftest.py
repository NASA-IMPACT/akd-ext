"""Shared fixtures for artifact tests."""

from pathlib import Path

import pytest


@pytest.fixture
def artifact_tree(tmp_path: Path) -> Path:
    """Build a small artifact tree on disk and return its root.

    Layout:
        artifacts/
        ├── index.md
        ├── contexts/
        │   ├── index.md
        │   └── role.md
        └── data.json     # non-md, should be filtered out of the store
    """
    root = tmp_path / "artifacts"
    root.mkdir()
    (root / "index.md").write_text("# Root")
    (root / "contexts").mkdir()
    (root / "contexts" / "index.md").write_text("# Contexts")
    (root / "contexts" / "role.md").write_text("# Role")
    (root / "data.json").write_text("{}")
    return root
