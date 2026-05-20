"""Create a new version inside an existing branch.

Inputs:
  * ``document_id`` and ``branch_id`` — where to append the new commit.
  * ``parent_version_id`` — explicit parent; usually the current HEAD of the branch,
    but we accept any version so the same use-case backs "Revert to this version".
  * ``source_path`` — file on disk to copy into FileStorage.
  * ``message`` — free-form description (shown in version tree).
  * ``actor`` — user performing the action (single-admin MVP: always "Адмін").
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from docflow.application.dto import CreateVersionInput
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
class CreateVersion:
    documents: DocumentRepository
    versions: VersionRepository
    audit: AuditRepository
    storage: FileStorage

    def __call__(self, cmd: CreateVersionInput) -> DocumentVersion:
        doc = self.documents.get(cmd.document_id)
        branch = self.versions.get_branch(cmd.branch_id)

        parent = self.versions.get_version(cmd.parent_version_id) if cmd.parent_version_id else None
        next_label = next_minor(parent.label) if parent else "v1.0"

        rel_path, size, sha1 = self.storage.save(
            Path(cmd.source_path), document_type=doc.doc_type.value
        )

        now = datetime.now()
        version = self.versions.add_version(
            DocumentVersion(
                id=None,
                document_id=cmd.document_id,
                branch_id=cmd.branch_id,
                label=next_label,
                message=cmd.message,
                parent_version_id=cmd.parent_version_id,
                file_path=rel_path,
                file_size=size,
                sha1=sha1,
                created_at=now,
                created_by=cmd.actor,
            )
        )
        assert version.id is not None
        self.versions.set_head(branch.id or 0, version.id)

        # Bump document's updated_at
        doc.updated_at = now
        self.documents.update(doc)

        self.audit.record(
            AuditLogEntry(
                id=None,
                occurred_at=now,
                actor=cmd.actor,
                action=AuditAction.VERSION_CREATED,
                document_id=cmd.document_id,
                details=f"{doc.name} → {next_label} (гілка {branch.name})",
            )
        )
        return version
