"""Domain entities — pure data, no I/O, no framework imports."""

from docflow.domain.entities.audit import AuditAction, AuditLogEntry
from docflow.domain.entities.branch import Branch
from docflow.domain.entities.document import Document, DocumentType
from docflow.domain.entities.tag import Tag, TagColor
from docflow.domain.entities.version import DocumentVersion

__all__ = [
    "AuditAction",
    "AuditLogEntry",
    "Branch",
    "Document",
    "DocumentType",
    "DocumentVersion",
    "Tag",
    "TagColor",
]
