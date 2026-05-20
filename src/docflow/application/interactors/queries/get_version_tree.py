"""Build the per-document version tree as a flat list of nodes (UI flattens to its own model)."""

from __future__ import annotations

from dataclasses import dataclass

from docflow.application.dto import VersionNode
from docflow.application.interfaces.repositories import VersionRepository


@dataclass(slots=True)
class GetVersionTree:
    versions: VersionRepository

    def __call__(self, document_id: int) -> list[VersionNode]:
        branches = {b.id: b for b in self.versions.list_branches(document_id)}
        head_per_branch: dict[int, int | None] = {}
        for b in branches.values():
            assert b.id is not None
            versions_in_branch = self.versions.list_versions_in_branch(b.id)
            head_per_branch[b.id] = versions_in_branch[0].id if versions_in_branch else None

        nodes: list[VersionNode] = []
        for v in self.versions.list_versions(document_id):
            branch = branches.get(v.branch_id)
            branch_name = branch.name if branch else "?"
            is_head = head_per_branch.get(v.branch_id) == v.id
            nodes.append(
                VersionNode(
                    version_id=v.id or 0,
                    label=v.label,
                    branch_id=v.branch_id,
                    branch_name=branch_name,
                    parent_version_id=v.parent_version_id,
                    message=v.message,
                    created_at=v.created_at,
                    created_by=v.created_by,
                    is_head=is_head,
                )
            )
        return nodes
