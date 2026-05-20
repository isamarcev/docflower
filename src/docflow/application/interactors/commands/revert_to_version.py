"""Revert to a chosen historical version.

Semantics: never rewrite history. Instead, we create a new commit in the
current branch whose contents match the chosen older version and whose
parent is the current HEAD (so the branch line stays linear). This matches
the "Відкотити до цієї версії" action in the wireframes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from docflow.application.interfaces import FileStorage
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
    storage: FileStorage

    def __call__(self, *, version_id: int, branch_id: int, actor: str) -> DocumentVersion:
        source_version = self.versions.get_version(version_id)
        doc = self.documents.get(source_version.document_id)
        branch = self.versions.get_branch(branch_id)

        # Use head of branch as parent. If none, fall back to the source version.
        head = self.versions.get_head(doc.id or 0, branch.name)
        parent_id = head.id if head else source_version.id

        # Copy the source file to a fresh storage blob.
        source_abs = self.storage.resolve(source_version.file_path)
        rel_path, size, sha1 = self.storage.save(source_abs, document_type=doc.doc_type.value)

        new_label = next_minor(head.label) if head else next_minor(source_version.label)
        now = datetime.now()
        version = self.versions.add_version(
            DocumentVersion(
                id=None,
                document_id=doc.id or 0,
                branch_id=branch.id or 0,
                label=new_label,
                message=f"Відкат до {source_version.label}",
                parent_version_id=parent_id,
                file_path=rel_path,
                file_size=size,
                sha1=sha1,
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
