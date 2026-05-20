"""Export a document with all its versions into a single zip archive.

Layout inside the archive::

    <doc-name>/
        manifest.json        # metadata + version map (label -> filename)
        versions/
            v1.0.docx
            v2.0.docx
            d1.0.docx
            ...
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from docflow.application.interfaces import FileStorage
from docflow.application.interfaces.repositories import (
    AuditRepository,
    DocumentRepository,
    TagRepository,
    VersionRepository,
)
from docflow.domain.entities import AuditAction, AuditLogEntry, Branch


def _archive_filename(label: str, branch_id: int, branches: list[Branch], file_path: str) -> str:
    branch_name = next((b.name for b in branches if b.id == branch_id), "unknown")
    ext = Path(file_path).suffix
    return f"versions/{branch_name}/{label}{ext}"


@dataclass(slots=True)
class ExportDocument:
    documents: DocumentRepository
    versions: VersionRepository
    tags: TagRepository
    audit: AuditRepository
    storage: FileStorage

    def __call__(self, document_id: int, *, destination: Path, actor: str) -> Path:
        doc = self.documents.get(document_id)
        assert doc.id is not None
        branches = self.versions.list_branches(doc.id)
        all_versions = self.versions.list_versions(doc.id)
        doc_tags = self.tags.list_for_document(doc.id)

        manifest = {
            "exported_at": datetime.now().isoformat(),
            "exported_by": actor,
            "document": {
                "name": doc.name,
                "doc_type": doc.doc_type.value,
                "description": doc.description,
                "created_at": doc.created_at.isoformat(),
                "created_by": doc.created_by,
            },
            "tags": [{"name": t.name, "color": t.color} for t in doc_tags],
            "branches": [
                {"name": b.name, "created_at": b.created_at.isoformat()} for b in branches
            ],
            "versions": [
                {
                    "label": v.label,
                    "branch": next((b.name for b in branches if b.id == v.branch_id), "?"),
                    "message": v.message,
                    "parent": next(
                        (vv.label for vv in all_versions if vv.id == v.parent_version_id), None
                    ),
                    "created_at": v.created_at.isoformat(),
                    "created_by": v.created_by,
                    "sha1": v.sha1,
                    "size": v.file_size,
                    # why: same label can exist in different branches (v1.2 in main and
                    # v1.2 in draft-Q1), so we namespace files by branch in the zip.
                    "filename": _archive_filename(v.label, v.branch_id, branches, v.file_path),
                }
                for v in all_versions
            ],
        }

        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2),
            )
            for v in all_versions:
                source = self.storage.resolve(v.file_path)
                if source.exists():
                    arcname = _archive_filename(v.label, v.branch_id, branches, v.file_path)
                    zf.write(source, arcname=arcname)

        self.audit.record(
            AuditLogEntry(
                id=None,
                occurred_at=datetime.now(),
                actor=actor,
                action=AuditAction.DOCUMENT_EXPORTED,
                document_id=doc.id,
                details=f"Експорт {doc.name} → {destination.name}",
            )
        )
        return destination
