"""Application-layer DTOs.

These are the *inputs* and *outputs* of use-cases. They are independent of
both the database schema and the UI: the UI builds them from form values,
use-cases consume them, and they return read-models the UI can render directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from docflow.domain.entities import AuditAction, DocumentType


# -------- Commands (input DTOs) --------


@dataclass(slots=True)
class ImportDocumentInput:
    name: str
    source_path: Path
    actor: str
    description: str = ""
    tag_ids: list[int] = field(default_factory=list)


@dataclass(slots=True)
class CreateVersionInput:
    document_id: int
    branch_id: int
    parent_version_id: int | None
    source_path: Path
    message: str
    actor: str


@dataclass(slots=True)
class CreateBranchInput:
    document_id: int
    parent_version_id: int
    name: str
    actor: str


# -------- Read-models (output DTOs) --------


@dataclass(slots=True)
class TagView:
    id: int
    name: str
    color: str
    description: str = ""
    document_count: int = 0


@dataclass(slots=True)
class DocumentListRow:
    """A single row in the main document list. Pre-resolved for the UI."""

    id: int
    name: str
    doc_type: DocumentType
    head_label: str  # e.g. "v3.2"
    branches_count: int
    tags: list[TagView]
    updated_at: datetime
    author: str


@dataclass(slots=True)
class VersionNode:
    """Node in the version tree (used for tree-view rendering)."""

    version_id: int
    label: str
    branch_id: int
    branch_name: str
    parent_version_id: int | None
    message: str
    created_at: datetime
    created_by: str
    is_head: bool


@dataclass(slots=True)
class AuditRow:
    occurred_at: datetime
    actor: str
    action: AuditAction
    details: str


@dataclass(slots=True)
class DocumentDetails:
    """Everything the document-card page needs in a single read."""

    id: int
    name: str
    doc_type: DocumentType
    description: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    size_bytes: int
    sha1: str
    head_label: str
    branch_name: str
    versions_total: int
    branches_total: int
    file_path: str
    tags: list[TagView]
    recent_versions: list[VersionNode]
    recent_audit: list[AuditRow]


@dataclass(slots=True)
class SearchInput:
    name_query: str | None = None
    doc_types: list[DocumentType] = field(default_factory=list)
    must_have_tag_ids: list[int] = field(default_factory=list)
    must_not_have_tag_ids: list[int] = field(default_factory=list)
    branch_name: str | None = None
    updated_from: datetime | None = None
    updated_to: datetime | None = None
