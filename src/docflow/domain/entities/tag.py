"""Tag entity — colored chip label attached to documents."""

from __future__ import annotations

from dataclasses import dataclass


# Allowed tag colors. UI maps these to QColor. Keep in sync with styles.theme.TAG_COLORS.
TagColor = str  # one of: "yellow" | "mint" | "blue" | "pink" | "purple" | "orange" | "gray"


@dataclass(slots=True)
class Tag:
    id: int | None
    name: str
    color: TagColor
    description: str = ""
