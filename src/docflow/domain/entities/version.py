"""DocumentVersion entity — single commit/snapshot in a branch."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class DocumentVersion:
    id: int | None
    document_id: int
    branch_id: int
    # Human-readable label: v1.0, v3.2, d1.1 (for draft branches), etc.
    label: str
    # Free-form change description.
    message: str
    # Parent in the DAG. None only for the very first version of a document.
    parent_version_id: int | None
    # Pointer into FileStorage. Relative to data/files/, e.g. "acts/2024-q4/12af4e9c.docx".
    file_path: str
    file_size: int
    sha1: str
    created_at: datetime
    created_by: str
