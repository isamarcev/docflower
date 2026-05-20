"""DocumentFile — immutable blob in storage.

A DocumentFile is a *content-addressable* unit: identified by its sha1 and
materialized as one file on disk under ``data/files/``. Multiple
DocumentVersion rows can point at the same DocumentFile (e.g. after a revert),
so we deduplicate on disk automatically.

The mapping DocumentFile -> Document is intentionally one-to-many: every blob
belongs to exactly one document so we can cascade-delete cleanly. We do NOT
share DocumentFiles across different Documents — that would complicate delete
semantics and produce surprising "ghost references" if a document is removed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class DocumentFile:
    id: int | None
    document_id: int
    relative_path: str   # storage path, e.g. "docx/2026/05/abc12345.docx"
    size_bytes: int
    sha1: str
    created_at: datetime
