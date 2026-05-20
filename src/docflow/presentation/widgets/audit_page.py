"""Audit-log page — flat table of recent actions with filter chips and CSV export."""

from __future__ import annotations

import csv
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from docflow.application.dto import AuditRow

ACTION_LABELS = {
    "document_created": "створено документ",
    "document_imported": "імпортовано",
    "document_renamed": "перейменовано",
    "document_deleted": "видалено",
    "document_exported": "експортовано",
    "document_updated": "оновлено картку",
    "version_created": "створено версію",
    "version_reverted": "відкат версії",
    "branch_created": "створено гілку",
    "branch_merged": "об'єднано гілку",
    "tag_added": "додано тег",
    "tag_removed": "видалено тег",
    "tags_edited": "редаговано теги",
}

ACTION_COLORS = {
    # action -> (bg, fg) for the small chip
    "document_created": ("#A8DBC1", "#1F4D3A"),
    "document_imported": ("#A8DBC1", "#1F4D3A"),
    "document_renamed": ("#F4D87A", "#5A4A1A"),
    "document_deleted": ("#F4A8B5", "#5A1F2C"),
    "document_exported": ("#B5D4E8", "#1F3F5A"),
    "document_updated": ("#F4D87A", "#5A4A1A"),
    "version_created": ("#A8DBC1", "#1F4D3A"),
    "version_reverted": ("#C7B4D9", "#3F2C5A"),
    "branch_created": ("#B5D4E8", "#1F3F5A"),
    "branch_merged": ("#B5D4E8", "#1F3F5A"),
    "tag_added": ("#F4D87A", "#5A4A1A"),
    "tag_removed": ("#F4A8B5", "#5A1F2C"),
    "tags_edited": ("#F4D87A", "#5A4A1A"),
}


class AuditPage(QWidget):
    """Renders the audit log. Filters are applied on the loaded data client-side."""

    export_csv_requested = pyqtSignal(str)  # destination path

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_rows: list[AuditRow] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("📋  Журнал дій")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # Filter + search row
        filt_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔎  пошук у журналі…")
        self._search.textChanged.connect(self._apply_filters)
        filt_row.addWidget(self._search)

        self._active_actions: set[str] = set()  # empty == all
        for label, action_key in [
            ("створення", "version_created"),
            ("редагування", "document_updated"),
            ("видалення", "document_deleted"),
            ("гілки", "branch_created"),
        ]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.toggled.connect(
                lambda checked, key=action_key: self._toggle_action(key, checked)
            )
            filt_row.addWidget(btn)

        filt_row.addStretch(1)
        export_btn = QPushButton("⬇  Експорт CSV")
        export_btn.clicked.connect(self._on_export_csv)
        filt_row.addWidget(export_btn)
        layout.addLayout(filt_row)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["КОЛИ", "ХТО", "ДІЯ", "ДЕТАЛІ"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 130)
        self._table.setColumnWidth(1, 130)
        self._table.setColumnWidth(2, 180)
        layout.addWidget(self._table, stretch=1)

        self._footer = QLabel("0 записів")
        self._footer.setStyleSheet("color: #7A7257;")
        layout.addWidget(self._footer)

    def set_rows(self, rows: list[AuditRow]) -> None:
        self._all_rows = list(rows)
        self._apply_filters()

    def _toggle_action(self, key: str, checked: bool) -> None:
        if checked:
            self._active_actions.add(key)
        else:
            self._active_actions.discard(key)
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self._search.text().strip().lower()
        rows = self._all_rows
        if self._active_actions:
            rows = [r for r in rows if r.action.value in self._active_actions]
        if query:
            rows = [
                r
                for r in rows
                if query in r.actor.lower() or query in r.details.lower()
            ]
        self._render(rows)

    def _render(self, rows: list[AuditRow]) -> None:
        self._table.setRowCount(0)
        for r in rows:
            idx = self._table.rowCount()
            self._table.insertRow(idx)
            self._table.setItem(idx, 0, QTableWidgetItem(r.occurred_at.strftime("%d.%m %H:%M")))
            self._table.setItem(idx, 1, QTableWidgetItem(r.actor))

            label = ACTION_LABELS.get(r.action.value, r.action.value)
            bg, fg = ACTION_COLORS.get(r.action.value, ("#DDD", "#2C2C2C"))
            chip = QLabel(label)
            chip.setStyleSheet(
                f"background: {bg}; color: {fg}; border-radius: 10px; "
                f"padding: 2px 8px; font-size: 11px;"
            )
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            wrap = QWidget()
            wlay = QHBoxLayout(wrap)
            wlay.setContentsMargins(6, 2, 6, 2)
            wlay.addWidget(chip)
            wlay.addStretch(1)
            self._table.setCellWidget(idx, 2, wrap)

            self._table.setItem(idx, 3, QTableWidgetItem(r.details))
        self._footer.setText(f"{len(rows)} з {len(self._all_rows)} записів")

    def _on_export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти журнал у CSV", "docflow_audit.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Коли", "Хто", "Дія", "Деталі"])
                for r in self._all_rows:
                    w.writerow(
                        [
                            r.occurred_at.isoformat(),
                            r.actor,
                            ACTION_LABELS.get(r.action.value, r.action.value),
                            r.details,
                        ]
                    )
        except OSError as e:
            QMessageBox.critical(self, "Помилка експорту", str(e))
            return
        QMessageBox.information(self, "Експорт", f"Збережено: {path}")
