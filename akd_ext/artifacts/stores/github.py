import os
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Self

from github import Auth, Github, UnknownObjectException
from loguru import logger

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
        """Load all available artifacts into the cache.

        Returns:
            Self, for fluent chaining.
        """
        prefix = PurePosixPath(self.path_prefix) if self.path_prefix else None
        with Github(auth=self._auth, retry=None) as gh:
            repo = gh.get_repo(self.repo_name)
            tree = repo.get_git_tree(self.branch, recursive=True)
            for entry in tree.tree:
                if entry.type != "blob":
                    continue
                full = PurePosixPath(entry.path)
                if prefix and not full.is_relative_to(prefix):
                    continue
                slug = str(full.relative_to(prefix)) if prefix else entry.path
                if not self._is_supported(slug):
                    continue
                content_file = repo.get_contents(entry.path, ref=self.branch)
                self[slug] = Artifact[str](
                    path=slug,
                    content=content_file.decoded_content.decode("utf-8"),
                    metadata={"sha": entry.sha},
                    updated_at=content_file.last_modified_datetime,
                )
        logger.info(
            "[GitHubArtifactStore] loaded {} artifacts from {}",
            len(self),
            self.root,
        )
        return self

    async def read_artifact(self, path: str) -> Artifact[str]:
        """Fetch an artifact by path from the cache.

        Cache-only — does not hit the GitHub API. Call `refresh()` to
        re-sync after external changes to the repo.

        Args:
            path: Path of the artifact to load (e.g. "contexts/role.md").

        Returns:
            The artifact including its content.

        Raises:
            KeyError: If the artifact is not in the cache — call
                `load_artifacts()` or `refresh()` first.
        """
        return self[path]

    async def write_artifact(self, artifact: Artifact[str]) -> Artifact[str]:
        """Persist an artifact to the repo as a commit.

        Args:
            artifact: Artifact to write. Commit message comes from
                `artifact.metadata["commit_message"]` if set, else
                "Update {path}".

        Returns:
            Stored artifact with refreshed `metadata["sha"]` and
            `updated_at` from the new commit.
        """
        full_path = str(PurePosixPath(self.path_prefix) / artifact.path) if self.path_prefix else artifact.path
        message = artifact.metadata.get("commit_message") or f"Update {artifact.path}"

        cached = self._artifacts.get(artifact.path)
        # Fast-path: skip write if content is unchanged vs. cache — avoids a
        # spurious commit with identical tree.
        if cached and cached.content == artifact.content:
            logger.debug(
                "[GitHubArtifactStore] no-op write (unchanged): {}",
                artifact.path,
            )
            return cached
        sha = cached.metadata.get("sha") if cached else None

        with Github(auth=self._auth, retry=None) as gh:
            repo = gh.get_repo(self.repo_name)

            # Probe remote if we don't already know the sha
            if sha is None:
                try:
                    sha = repo.get_contents(full_path, ref=self.branch).sha
                except UnknownObjectException:
                    pass  # stays None → will create

            common = dict(
                path=full_path,
                message=message,
                content=artifact.content,
                branch=self.branch,
            )
            result = repo.update_file(sha=sha, **common) if sha else repo.create_file(**common)

        stored = artifact.model_copy(
            update={
                "metadata": {**artifact.metadata, "sha": result["content"].sha},
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self[artifact.path] = stored
        logger.info(
            "[GitHubArtifactStore] wrote: {} (sha={})",
            stored.path,
            result["content"].sha,
        )
        return stored
