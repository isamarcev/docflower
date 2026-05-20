"""Delete a document along with all versions, branches, files, and blobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from docflow.application.interfaces import FileStorage
from docflow.application.interfaces.repositories import (
    AuditRepository,
    DocumentRepository,
    FileRepository,
)
from docflow.domain.entities import AuditAction, AuditLogEntry


@dataclass(slots=True)
class DeleteDocument:
    documents: DocumentRepository
    files: FileRepository
    audit: AuditRepository
    storage: FileStorage

    def __call__(self, document_id: int, *, actor: str) -> None:
        doc = self.documents.get(document_id)
        # why: record audit FIRST. After CASCADE the document row is gone and FK
        # would reject an INSERT with that document_id.
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
        # Unlink every blob that belonged to this document. Because all blobs are
        # scoped to one document, we don't need to check reference counts.
        for f in self.files.list_for_document(document_id):
            try:
                self.storage.delete(f.relative_path)
            except Exception:  # noqa: BLE001 — non-fatal; storage may be already missing
                pass
        # ON DELETE CASCADE handles versions, branches, document_files, document_tags.
        self.documents.delete(document_id)
