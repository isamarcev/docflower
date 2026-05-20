"""Create a new version inside an existing branch.

Deduplication: if the chosen source file's sha1 already exists for this
document (e.g. user re-imports an unchanged file), we reuse the existing
DocumentFile instead of saving a duplicate blob.
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
    FileRepository,
    VersionRepository,
)
from docflow.application.version_labels import next_minor
from docflow.domain.entities import (
    AuditAction,
    AuditLogEntry,
    DocumentFile,
    DocumentVersion,
)
from docflow.infrastructure.storage.file_storage import sha1_of_file


@dataclass(slots=True)
class CreateVersion:
    documents: DocumentRepository
    versions: VersionRepository
    files: FileRepository
    audit: AuditRepository
    storage: FileStorage

    def __call__(self, cmd: CreateVersionInput) -> DocumentVersion:
        if (cmd.source_path is None) == (cmd.reuse_file_id is None):
            raise ValueError(
                "CreateVersionInput requires exactly one of source_path or reuse_file_id"
            )

        doc = self.documents.get(cmd.document_id)
        branch = self.versions.get_branch(cmd.branch_id)

        parent = self.versions.get_version(cmd.parent_version_id) if cmd.parent_version_id else None
        # On a fresh branch with a parent commit, start the local series at d1.0,
        # otherwise bump minor from the parent's label (v1.2 -> v1.3).
        if parent is not None and parent.branch_id != cmd.branch_id:
            next_label = "d1.0"
        elif parent is not None:
            next_label = next_minor(parent.label)
        else:
            next_label = "v1.0"

        now = datetime.now()

        # Resolve file_id: either reuse an existing DocumentFile or import a new blob.
        if cmd.reuse_file_id is not None:
            file_id = cmd.reuse_file_id
        else:
            # Dedupe: peek at source sha1 before saving.
            src = Path(cmd.source_path)  # type: ignore[arg-type]
            src_sha1 = sha1_of_file(src)
            existing = self.files.find_by_sha1(cmd.document_id, src_sha1)
            if existing is not None:
                file_id = existing.id or 0
            else:
                rel_path, size, sha1 = self.storage.save(src, document_type=doc.doc_type.value)
                doc_file = self.files.add(
                    DocumentFile(
                        id=None,
                        document_id=cmd.document_id,
                        relative_path=rel_path,
                        size_bytes=size,
                        sha1=sha1,
                        created_at=now,
                    )
                )
                file_id = doc_file.id or 0

        version = self.versions.add_version(
            DocumentVersion(
                id=None,
                document_id=cmd.document_id,
                branch_id=cmd.branch_id,
                file_id=file_id,
                label=next_label,
                message=cmd.message,
                parent_version_id=cmd.parent_version_id,
                created_at=now,
                created_by=cmd.actor,
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
                actor=cmd.actor,
                action=AuditAction.VERSION_CREATED,
                document_id=cmd.document_id,
                details=f"{doc.name} → {next_label} (гілка {branch.name})",
            )
        )
        return version
