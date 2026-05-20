"""Branch entity — Git-like named branch in a document's version tree."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Branch:
    id: int | None
    document_id: int
    name: str  # e.g. "main", "draft-Q1", "old-2023"
    created_at: datetime
    created_by: str
    # Version this branch forked off from. None for the root branch ("main").
    parent_version_id: int | None = None
    is_head: bool = False  # cached flag — true for branch HEAD pointer
