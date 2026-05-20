"""Delete a document along with all versions, branches and storage blobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from docflow.application.interfaces import FileStorage
from docflow.application.interfaces.repositories import (
    AuditRepository,
    DocumentRepository,
    VersionRepository,
)
from docflow.domain.entities import AuditAction, AuditLogEntry


@dataclass(slots=True)
class DeleteDocument:
    documents: DocumentRepository
    versions: VersionRepository
    audit: AuditRepository
    storage: FileStorage

    def __call__(self, document_id: int, *, actor: str) -> None:
        doc = self.documents.get(document_id)
        # why: record audit FIRST, then delete. Otherwise audit_log.document_id FK
        # rejects the insert (ON DELETE SET NULL fires only when the row already exists).
        self.audit.record(
            AuditLogEntry(
                id=None,
                occurred_at=datetime.now(),
                actor=actor,
                action=AuditAction.DOCUMENT_DELETED,
                document_id=document_id,
                details=f"{doc.name} → корзина",
            )
        )
        # Best-effort: remove blobs; DB cascade handles versions/branches/tag-links.
        for v in self.versions.list_versions(document_id):
            try:
                self.storage.delete(v.file_path)
            except Exception:  # noqa: BLE001 — non-fatal; storage may be already missing
                pass
        self.documents.delete(document_id)
