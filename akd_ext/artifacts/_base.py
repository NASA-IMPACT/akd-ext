from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Artifact[T](BaseModel):
    path: str = Field(..., description="Slug that identifies the artifact.")
    name: str | None = Field(default=None, description="Name of the artifact.")
    description: str | None = Field(
        default=None,
        description="One-line summary; helps an agent decide whether to load this artifact.",
    )
    content: T = Field(..., description="The content of the artifact.")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Backend-specific escape hatch (mime type, commit sha, author, tags, etc.). Could be loaded from frontmatter as well if md file",
    )
    created_at: datetime | None = Field(
        default=None,
        description=(
            "When the artifact was first stored. Output-only: populated by the store "
            "on read; ignored on write (stores set it according to their backend)."
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        description=(
            "When the artifact was last modified. Output-only: populated by the store "
            "on read; ignored on write (stores set it according to their backend)."
        ),
    )
