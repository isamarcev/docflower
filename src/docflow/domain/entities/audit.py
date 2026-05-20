"""AuditLogEntry entity — single line in the action audit log."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AuditAction(str, Enum):
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_IMPORTED = "document_imported"
    DOCUMENT_RENAMED = "document_renamed"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_EXPORTED = "document_exported"
    DOCUMENT_UPDATED = "document_updated"
    VERSION_CREATED = "version_created"
    VERSION_REVERTED = "version_reverted"
    BRANCH_CREATED = "branch_created"
    BRANCH_MERGED = "branch_merged"
    TAG_ADDED = "tag_added"
    TAG_REMOVED = "tag_removed"
    TAGS_EDITED = "tags_edited"


@dataclass(slots=True)
class AuditLogEntry:
    id: int | None
    occurred_at: datetime
    actor: str  # name of the user performing the action
    action: AuditAction
    document_id: int | None
    # Free-form human-readable details: "Акт_списання_2024-Q4.docx → v3.2"
    details: str
