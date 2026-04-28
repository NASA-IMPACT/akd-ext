"""Small, pure helpers shared by Artifact, ArtifactStore, and concrete backends."""


def canonical_ext(t: str) -> str:
    """Normalize a user-supplied file-type hint to canonical `.ext` form.

    Accepts any of:
      - 'md'    -> '.md'
      - '.md'   -> '.md'
      - '*.md'  -> '.md'
    """
    if t.startswith("*."):
        t = t[1:]
    if not t.startswith("."):
        t = f".{t}"
    return t
