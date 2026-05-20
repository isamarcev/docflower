"""Domain-level exceptions.

Use-cases raise these; presentation layer maps them to user-visible messages.
Never raise generic Exception or framework-specific errors from domain/application.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors.

    Subclasses must override ``code`` (stable machine-readable identifier) and
    set ``message`` via constructor.
    """

    code: str = "domain_error"

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DocumentNotFoundError(DomainError):
    code = "document_not_found"


class VersionNotFoundError(DomainError):
    code = "version_not_found"


class BranchNotFoundError(DomainError):
    code = "branch_not_found"


class TagNotFoundError(DomainError):
    code = "tag_not_found"


class DuplicateTagError(DomainError):
    code = "duplicate_tag"


class UnsupportedFileTypeError(DomainError):
    code = "unsupported_file_type"


class StorageError(DomainError):
    """Raised when the filesystem-backed storage fails (I/O issue, missing file)."""

    code = "storage_error"
