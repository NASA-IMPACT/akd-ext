-- PostgresBackend schema for CARE v2 artifact workspace.
-- Mirrors StateBackend's flat-key model: paths are normalized absolute-style
-- ("/scope.md", "/contexts/index.md"); directories are implicit.

CREATE TABLE IF NOT EXISTS care_artifacts (
    workspace    TEXT        NOT NULL,
    path         TEXT        NOT NULL,
    content      TEXT        NOT NULL,
    size_bytes   INTEGER     NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    modified_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace, path)
);

CREATE INDEX IF NOT EXISTS care_artifacts_workspace_path_prefix
    ON care_artifacts (workspace, path text_pattern_ops);
