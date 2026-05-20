"""Update document metadata (name, description).

Renames file blob on disk is intentionally NOT done — version blobs keep their
storage UUIDs forever, what changes is the human-visible ``Document.name``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from docflow.application.interfaces.repositories import (
    AuditRepository,
    DocumentRepository,
)
from docflow.domain.entities import AuditAction, AuditLogEntry


@dataclass(slots=True)
class UpdateDocument:
    documents: DocumentRepository
    audit: AuditRepository

    def __call__(
        self,
        *,
        document_id: int,
        name: str | None,
        description: str | None,
        actor: str,
    ) -> None:
        doc = self.documents.get(document_id)
        change_bits: list[str] = []

        if name is not None and name != doc.name:
            old_name = doc.name
            doc.name = name
            change_bits.append(f"перейменовано {old_name} → {name}")
        if description is not None and description != doc.description:
            doc.description = description
            change_bits.append("оновлено опис")

        if not change_bits:
            return  # nothing to do

        doc.updated_at = datetime.now()
        self.documents.update(doc)

        self.audit.record(
            AuditLogEntry(
                id=None,
                occurred_at=doc.updated_at,
                actor=actor,
                action=AuditAction.DOCUMENT_UPDATED,
                document_id=doc.id,
                details=f"{doc.name}: " + "; ".join(change_bits),
            )
        )
