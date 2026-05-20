"""Colored tag chip widget (Gmail/Notion style)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from docflow.presentation.styles.theme import tag_chip_style


class TagChip(QLabel):
    def __init__(self, name: str, color: str = "gray", parent: object | None = None) -> None:
        super().__init__(name, parent)  # type: ignore[arg-type]
        self.setStyleSheet(tag_chip_style(color))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(20)
