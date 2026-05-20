"""DocumentVersion entity — single commit/snapshot in a branch."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class DocumentVersion:
    """Labeled snapshot pointing at a DocumentFile.

    The version is *the label* (v1.0, message, parent in DAG); the underlying
    content lives in :class:`DocumentFile` (referenced by ``file_id``).
    Multiple versions can share the same ``file_id`` — that's how reverts
    avoid duplicating blobs on disk.
    """

    id: int | None
    document_id: int
    branch_id: int
    # FK to document_files.id — the actual content.
    file_id: int
    # Human-readable label: v1.0, v3.2, d1.1 (for draft branches), etc.
    label: str
    # Free-form change description.
    message: str
    # Parent in the DAG. None only for the very first version of a document.
    parent_version_id: int | None
    created_at: datetime
    created_by: str
