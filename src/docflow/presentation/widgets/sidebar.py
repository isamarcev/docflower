"""Notion-style sidebar with workspace / tags / system sections.

Emits ``navigation_changed(str)`` when the active item changes. The string is
the section's stable identifier (e.g. ``"all"``, ``"recent"``, ``"audit"``,
``"tag:24"``).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from docflow.application.dto import TagView


class Sidebar(QFrame):
    navigation_changed = pyqtSignal(str)

    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setObjectName("Sidebar")
        self.setFixedWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Workspace header (single-admin product label)
        header = QLabel("📁  Документообіг\nслужба списання · локально")
        header.setStyleSheet(
            "padding: 14px 14px 10px; font-weight: 600; font-size: 13px;"
        )
        layout.addWidget(header)

        # Quick search box (Ctrl+F shortcut wired up in main window)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔎  Швидкий пошук…")
        self.search_box.setContentsMargins(10, 0, 10, 8)
        wrap = QFrame()
        wrap_l = QVBoxLayout(wrap)
        wrap_l.setContentsMargins(10, 0, 10, 10)
        wrap_l.addWidget(self.search_box)
        layout.addWidget(wrap)

        # Workspace section
        layout.addWidget(self._section_label("РОБОЧИЙ ПРОСТІР"))
        self.workspace_list = self._make_list()
        for label, key in [
            ("📄  Усі документи", "all"),
            ("★  Недавні", "recent"),
            ("✎  Чернетки", "drafts"),
        ]:
            self.workspace_list.addItem(QListWidgetItem(label))
            self.workspace_list.item(self.workspace_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, key
            )
        self.workspace_list.setCurrentRow(0)
        layout.addWidget(self.workspace_list)

        # Tags section
        layout.addWidget(self._section_label("ТЕГИ"))
        self.tag_list = self._make_list()
        layout.addWidget(self.tag_list)

        # System section
        layout.addWidget(self._section_label("СИСТЕМА"))
        self.system_list = self._make_list()
        for label, key in [
            ("📋  Журнал дій", "audit"),
            ("🗄  Архів", "archive"),
            ("⚙  Налаштування", "settings"),
        ]:
            self.system_list.addItem(QListWidgetItem(label))
            self.system_list.item(self.system_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, key
            )
        layout.addWidget(self.system_list)
        layout.addStretch(1)

        # Wire selection -> navigation_changed (mutually exclusive across lists)
        self.workspace_list.itemSelectionChanged.connect(
            lambda: self._emit_from(self.workspace_list, (self.tag_list, self.system_list))
        )
        self.tag_list.itemSelectionChanged.connect(
            lambda: self._emit_from(self.tag_list, (self.workspace_list, self.system_list))
        )
        self.system_list.itemSelectionChanged.connect(
            lambda: self._emit_from(self.system_list, (self.workspace_list, self.tag_list))
        )

    def set_tags(self, tags: list[TagView]) -> None:
        self.tag_list.clear()
        for tag in tags:
            item = QListWidgetItem(f"●  {tag.name}    {tag.document_count}")
            item.setData(Qt.ItemDataRole.UserRole, f"tag:{tag.id}")
            self.tag_list.addItem(item)

    # -- internals --

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("SidebarSection")
        return lbl

    def _make_list(self) -> QListWidget:
        lst = QListWidget()
        lst.setObjectName("SidebarList")
        lst.setFrameShape(QListWidget.Shape.NoFrame)
        lst.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        return lst

    def _emit_from(self, source: QListWidget, others: tuple[QListWidget, ...]) -> None:
        item = source.currentItem()
        if item is None:
            return
        for o in others:
            o.blockSignals(True)
            o.clearSelection()
            o.setCurrentRow(-1)
            o.blockSignals(False)
        key = item.data(Qt.ItemDataRole.UserRole)
        if key:
            self.navigation_changed.emit(str(key))
