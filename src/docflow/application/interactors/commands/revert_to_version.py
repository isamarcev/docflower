"""Revert to a chosen historical version.

With the v2 schema we no longer copy the blob — the new DocumentVersion simply
reuses the source version's ``file_id``. On disk that's one file shared by two
DocumentVersion rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from docflow.application.interfaces.repositories import (
    AuditRepository,
    DocumentRepository,
    VersionRepository,
)
from docflow.application.version_labels import next_minor
from docflow.domain.entities import (
    AuditAction,
    AuditLogEntry,
    DocumentVersion,
)


@dataclass(slots=True)
class RevertToVersion:
    documents: DocumentRepository
    versions: VersionRepository
    audit: AuditRepository

    def __call__(self, *, version_id: int, branch_id: int, actor: str) -> DocumentVersion:
        source_version = self.versions.get_version(version_id)
        doc = self.documents.get(source_version.document_id)
        branch = self.versions.get_branch(branch_id)

        head = self.versions.get_head(doc.id or 0, branch.name)
        parent_id = head.id if head else source_version.id

        new_label = next_minor(head.label) if head else next_minor(source_version.label)
        now = datetime.now()
        version = self.versions.add_version(
            DocumentVersion(
                id=None,
                document_id=doc.id or 0,
                branch_id=branch.id or 0,
                # why: reuse the original blob — that's the whole point of a revert.
                file_id=source_version.file_id,
                label=new_label,
                message=f"Відкат до {source_version.label}",
                parent_version_id=parent_id,
                created_at=now,
                created_by=actor,
            )
        )
        assert version.id is not None
        self.versions.set_head(branch.id or 0, version.id)

        doc.updated_at = now
        self.documents.update(doc)

        self.audit.record(
            AuditLogEntry(
                id=None,
                occurred_at=now,
                actor=actor,
                action=AuditAction.VERSION_REVERTED,
                document_id=doc.id,
                details=f"{doc.name}: відкат {source_version.label} → {new_label}",
            )
        )
        return version
