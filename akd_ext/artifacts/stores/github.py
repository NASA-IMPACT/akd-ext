import os
import re
from pathlib import PurePosixPath
from typing import Self

from github import Auth

from akd_ext.artifacts._base import Artifact, ArtifactStore


class GitHubArtifactStore(ArtifactStore[str]):
    """GitHub-backed artifact store.

    Reads and writes artifacts inside a sub-tree of a GitHub repo via
    the GitHub REST API (PyGithub). `root` can be either
    "owner/repo[/path/within/repo]" or a github.com URL; in both cases
    the first two segments identify the repo and any remaining segments
    scope the store to that sub-tree. Slugs returned by the store are
    relative to the sub-tree, matching `LocalArtifactStore`'s form — so
    an agent's tool calls don't depend on which backend is in use.
    """

    def __init__(
        self,
        root: str,
        *,
        branch: str = "main",
        access_token: str | None = None,
        index_file: str | None = "README.md",
        supported_extensions: tuple[str, ...] = (".md",),
        debug: bool = False,
    ) -> None:
        """Construct a GitHub-backed artifact store.

        Args:
            root: "owner/repo[/path]" or a github.com URL (e.g.
                "https://github.com/NASA-IMPACT/akd/tree/main/agents/x/artifacts").
            branch: Branch to read/write. Defaults to "main". A branch
                embedded in a `.../tree/<branch>/...` URL takes precedence
                over this kwarg.
            access_token: GitHub personal access token. Falls back to
                the `GITHUB_ACCESS_TOKEN` env var. Anonymous (public-read
                only) if neither is set.
            index_file: Directory-overview filename (defaults to README.md,
                which GitHub renders at the directory level).
            supported_extensions: Extensions to include; see ArtifactStore.
            debug: Enable debug logging.

        Raises:
            ValueError: If `root` does not contain at least "owner/repo".
        """
        super().__init__(
            root=root,
            index_file=index_file,
            supported_extensions=supported_extensions,
            debug=debug,
        )
        self.repo_name, self.path_prefix, url_branch = self._parse_root(root)
        self.branch = url_branch or branch
        self._token = access_token or os.getenv("GITHUB_ACCESS_TOKEN")
        self._auth = Auth.Token(self._token) if self._token else None

    @staticmethod
    def _parse_root(root: str) -> tuple[str, str, str | None]:
        """Parse `root` into (repo_name, path_prefix, branch_hint).

        Accepts plain ``owner/repo[/path]`` or a github.com URL (with or
        without scheme; with or without a ``/tree/<branch>/...`` segment).
        `branch_hint` is the URL-extracted branch if present, else None.
        """
        s = re.sub(r"^(?:https?://)?(?:www\.)?github\.com/?", "", root.strip()).rstrip("/")
        parts = PurePosixPath(s).parts
        if len(parts) < 2:
            raise ValueError(f"GitHub root must be 'owner/repo[/path]' or a github.com URL, got {root!r}")
        repo_name = f"{parts[0]}/{parts[1]}"
        if len(parts) >= 4 and parts[2] in ("tree", "blob"):
            return repo_name, "/".join(parts[4:]), parts[3]
        return repo_name, "/".join(parts[2:]), None

    async def load_artifacts(self) -> Self:
        return self

    async def read_artifact(self, path: str) -> Artifact[str]:
        pass

    async def write_artifact(self, artifact: Artifact[str]) -> Artifact[str]:
        pass
