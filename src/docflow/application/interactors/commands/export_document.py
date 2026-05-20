"""Export a document with all its versions into a single zip archive.

Layout inside the archive::

    manifest.json                # metadata + version table
    versions/<branch>/<label>.<ext>

If two versions share a file_id (e.g. after a revert), they appear as two
separate entries pointing at the same content — we copy the blob once per
filename, which keeps the archive self-describing.
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
    FileRepository,
    TagRepository,
    VersionRepository,
)
from docflow.domain.entities import AuditAction, AuditLogEntry, Branch


def _archive_filename(label: str, branch_id: int, branches: list[Branch], ext: str) -> str:
    branch_name = next((b.name for b in branches if b.id == branch_id), "unknown")
    return f"versions/{branch_name}/{label}{ext}"


@dataclass(slots=True)
class ExportDocument:
    documents: DocumentRepository
    versions: VersionRepository
    files: FileRepository
    tags: TagRepository
    audit: AuditRepository
    storage: FileStorage

    def __call__(self, document_id: int, *, destination: Path, actor: str) -> Path:
        doc = self.documents.get(document_id)
        assert doc.id is not None
        branches = self.versions.list_branches(doc.id)
        all_versions = self.versions.list_versions(doc.id)
        doc_tags = self.tags.list_for_document(doc.id)
        files_by_id = {f.id: f for f in self.files.list_for_document(doc.id)}

        ext = f".{doc.doc_type.value}"
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
                    "file_id": v.file_id,
                    "sha1": files_by_id[v.file_id].sha1 if v.file_id in files_by_id else None,
                    "size": files_by_id[v.file_id].size_bytes if v.file_id in files_by_id else 0,
                    "filename": _archive_filename(v.label, v.branch_id, branches, ext),
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
                doc_file = files_by_id.get(v.file_id)
                if doc_file is None:
                    continue
                source = self.storage.resolve(doc_file.relative_path)
                if source.exists():
                    arcname = _archive_filename(v.label, v.branch_id, branches, ext)
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
