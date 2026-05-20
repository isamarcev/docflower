"""Composition root — builds DB, repositories, use-cases, and the UI bundle.

Schema v2: introduces SqliteFileRepository for the new DocumentFile entity.
"""

from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from docflow.application.interactors.commands.create_branch import CreateBranch
from docflow.application.interactors.commands.create_version import CreateVersion
from docflow.application.interactors.commands.delete_document import DeleteDocument
from docflow.application.interactors.commands.export_document import ExportDocument
from docflow.application.interactors.commands.import_document import ImportDocument
from docflow.application.interactors.commands.manage_tags import (
    AttachTag,
    CreateTag,
    DeleteTag,
    DetachTag,
    UpdateTag,
)
from docflow.application.interactors.commands.revert_to_version import RevertToVersion
from docflow.application.interactors.commands.update_document import UpdateDocument
from docflow.application.interactors.queries.get_document_details import GetDocumentDetails
from docflow.application.interactors.queries.get_version_tree import GetVersionTree
from docflow.application.interactors.queries.list_audit import ListAudit
from docflow.application.interactors.queries.list_documents import ListDocuments
from docflow.application.interactors.queries.list_tags import ListTags
from docflow.infrastructure.db.connection import open_connection
from docflow.infrastructure.repositories.audit_repo import SqliteAuditRepository
from docflow.infrastructure.repositories.document_repo import SqliteDocumentRepository
from docflow.infrastructure.repositories.file_repo import SqliteFileRepository
from docflow.infrastructure.repositories.tag_repo import SqliteTagRepository
from docflow.infrastructure.repositories.version_repo import SqliteVersionRepository
from docflow.infrastructure.storage.file_storage import LocalFileStorage
from docflow.main.config import AppConfig


@dataclass(slots=True)
class UseCases:
    """Bundle of all use-cases plus a few UI-helper callables.

    The bundle lives in main/ so we keep the dependency rule clean:
    main wires it up and hands it to presentation as a plain DTO.
    """

    list_documents: ListDocuments
    list_tags: ListTags
    list_audit: ListAudit
    get_version_tree: GetVersionTree
    get_document_details: GetDocumentDetails

    import_document: ImportDocument
    delete_document: DeleteDocument
    update_document: UpdateDocument
    export_document: ExportDocument

    create_version: CreateVersion
    create_branch: CreateBranch
    revert_to_version: RevertToVersion

    create_tag: CreateTag
    update_tag: UpdateTag
    delete_tag: DeleteTag
    attach_tag: AttachTag
    detach_tag: DetachTag

    resolve_path: "ResolvePath"
    export_version_copy: "ExportVersionCopy"
    version_file_id: "VersionFileId"


@dataclass(slots=True)
class ResolvePath:
    storage: LocalFileStorage

    def __call__(self, relative_path: str) -> Path:
        return self.storage.resolve(relative_path)


@dataclass(slots=True)
class ExportVersionCopy:
    versions: SqliteVersionRepository
    files: SqliteFileRepository
    storage: LocalFileStorage

    def __call__(self, *, version_id: int, destination: Path) -> Path:
        v = self.versions.get_version(version_id)
        doc_file = self.files.get(v.file_id)
        src = self.storage.resolve(doc_file.relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, destination)
        return destination


@dataclass(slots=True)
class VersionFileId:
    """Helper: return the DocumentFile.id behind a given DocumentVersion.

    UI needs this when creating a branch in "copy from parent" mode, so the new
    DocumentVersion can reuse the parent's blob.
    """

    versions: SqliteVersionRepository

    def __call__(self, *, version_id: int) -> int:
        return self.versions.get_version(version_id).file_id


@dataclass(slots=True)
class Container:
    config: AppConfig
    conn: sqlite3.Connection
    use_cases: UseCases


def build_container(config: AppConfig | None = None) -> Container:
    cfg = config or AppConfig.default()
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.files_dir.mkdir(parents=True, exist_ok=True)

    conn = open_connection(cfg.db_path)

    documents = SqliteDocumentRepository(conn)
    versions = SqliteVersionRepository(conn)
    files = SqliteFileRepository(conn)
    tags = SqliteTagRepository(conn)
    audit = SqliteAuditRepository(conn)
    storage = LocalFileStorage(cfg.files_dir)

    use_cases = UseCases(
        list_documents=ListDocuments(documents=documents, versions=versions, tags=tags),
        list_tags=ListTags(tags=tags),
        list_audit=ListAudit(audit=audit),
        get_version_tree=GetVersionTree(versions=versions),
        get_document_details=GetDocumentDetails(
            documents=documents, versions=versions, files=files, tags=tags, audit=audit
        ),
        import_document=ImportDocument(
            documents=documents, versions=versions, files=files,
            tags=tags, audit=audit, storage=storage,
        ),
        delete_document=DeleteDocument(
            documents=documents, files=files, audit=audit, storage=storage
        ),
        update_document=UpdateDocument(documents=documents, audit=audit),
        export_document=ExportDocument(
            documents=documents, versions=versions, files=files,
            tags=tags, audit=audit, storage=storage,
        ),
        create_version=CreateVersion(
            documents=documents, versions=versions, files=files,
            audit=audit, storage=storage,
        ),
        create_branch=CreateBranch(documents=documents, versions=versions, audit=audit),
        revert_to_version=RevertToVersion(
            documents=documents, versions=versions, audit=audit
        ),
        create_tag=CreateTag(tags=tags),
        update_tag=UpdateTag(tags=tags),
        delete_tag=DeleteTag(tags=tags),
        attach_tag=AttachTag(tags=tags, documents=documents, audit=audit),
        detach_tag=DetachTag(tags=tags, documents=documents, audit=audit),
        resolve_path=ResolvePath(storage=storage),
        export_version_copy=ExportVersionCopy(versions=versions, files=files, storage=storage),
        version_file_id=VersionFileId(versions=versions),
    )
    return Container(config=cfg, conn=conn, use_cases=use_cases)
