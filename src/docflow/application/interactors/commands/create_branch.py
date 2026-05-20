"""Create a new branch off an existing version.

The new branch is created with no commits of its own — the next CreateVersion call
will add the first commit (``d1.0``) and set HEAD. UI-wise this matches "Гілка
від обраного" in the wireframes: clicking the button creates the branch and then
opens NewVersionDialog in "version" mode against the new branch.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from docflow.application.dto import CreateBranchInput
from docflow.application.interfaces.repositories import (
    AuditRepository,
    DocumentRepository,
    VersionRepository,
)
from docflow.domain.entities import (
    AuditAction,
    AuditLogEntry,
    Branch,
)


@dataclass(slots=True)
class CreateBranch:
    documents: DocumentRepository
    versions: VersionRepository
    audit: AuditRepository

    def __call__(self, cmd: CreateBranchInput) -> Branch:
        doc = self.documents.get(cmd.document_id)
        parent_version = self.versions.get_version(cmd.parent_version_id)

        now = datetime.now()
        branch = self.versions.add_branch(
            Branch(
                id=None,
                document_id=cmd.document_id,
                name=cmd.name,
                created_at=now,
                created_by=cmd.actor,
                parent_version_id=parent_version.id,
                is_head=False,
            )
        )

        self.audit.record(
            AuditLogEntry(
                id=None,
                occurred_at=now,
                actor=cmd.actor,
                action=AuditAction.BRANCH_CREATED,
                document_id=cmd.document_id,
                details=f"{doc.name}: гілка '{cmd.name}' від {parent_version.label}",
            )
        )
        return branch
