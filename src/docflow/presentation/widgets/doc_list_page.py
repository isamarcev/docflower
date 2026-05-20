"""Main document list — table with type/name/version/branches/tags/modified columns."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from docflow.application.dto import DocumentListRow
from docflow.presentation.styles.theme import doc_type_badge_style
from docflow.presentation.widgets.tag_chip import TagChip


class DocumentListPage(QWidget):
    document_activated = pyqtSignal(int)  # document_id

    # Columns: type-badge, name, version-label, branches-count, tag-chips, modified
    COLS = ["", "Назва", "Версія", "Гілки", "Теги", "Змінено"]

    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Breadcrumb / title
        self._title = QLabel("📄  Усі документи")
        self._title.setObjectName("PageTitle")
        layout.addWidget(self._title)

        self._subtitle = QLabel("0 документів")
        self._subtitle.setObjectName("PageSubtitle")
        layout.addWidget(self._subtitle)

        # Filter chips bar (placeholder for now)
        filter_bar = QHBoxLayout()
        filter_bar.setContentsMargins(16, 0, 16, 0)
        filter_bar.addWidget(QLabel("Фільтри:"))
        filter_bar.addStretch(1)
        layout.addLayout(filter_bar)

        # Table
        self._table = QTableWidget(0, len(self.COLS))
        self._table.setHorizontalHeaderLabels(self.COLS)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 50)
        self._table.setColumnWidth(2, 70)
        self._table.setColumnWidth(3, 70)
        self._table.setColumnWidth(5, 130)
        self._table.itemDoubleClicked.connect(self._on_double_click)
        # Sorting: click any header to sort. Note: cell-widget columns (type, tags)
        # don't have meaningful keys, so we leave them effectively no-op.
        self._table.setSortingEnabled(True)
        layout.addWidget(self._table, stretch=1)

    def set_title(self, title: str, subtitle: str = "") -> None:
        self._title.setText(title)
        self._subtitle.setText(subtitle)

    def set_rows(self, rows: list[DocumentListRow]) -> None:
        # why: turn sorting off during bulk insert; turning it on triggers a re-sort
        # after every setItem call which is O(n²).
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        for r in rows:
            row_idx = self._table.rowCount()
            self._table.insertRow(row_idx)
            self._table.setRowHeight(row_idx, 36)

            # type badge
            badge = QLabel(r.doc_type.value)
            badge.setStyleSheet(doc_type_badge_style(r.doc_type.value))
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setCellWidget(row_idx, 0, _padded(badge))

            # name (stores id in UserRole)
            name_item = QTableWidgetItem(r.name)
            name_item.setData(Qt.ItemDataRole.UserRole, r.id)
            self._table.setItem(row_idx, 1, name_item)

            # version label
            self._table.setItem(row_idx, 2, QTableWidgetItem(r.head_label))

            # branches
            branches_text = f"⑂ {r.branches_count}" if r.branches_count > 1 else "—"
            self._table.setItem(row_idx, 3, QTableWidgetItem(branches_text))

            # tag chips
            tag_widget = QWidget()
            tag_layout = QHBoxLayout(tag_widget)
            tag_layout.setContentsMargins(8, 2, 8, 2)
            tag_layout.setSpacing(4)
            for tag in r.tags[:4]:
                tag_layout.addWidget(TagChip(tag.name, tag.color))
            if len(r.tags) > 4:
                tag_layout.addWidget(TagChip(f"+{len(r.tags) - 4}", "gray"))
            tag_layout.addStretch(1)
            self._table.setCellWidget(row_idx, 4, tag_widget)

            # modified — store ISO string in user-role so sort is by datetime, not display
            mod_item = QTableWidgetItem(r.updated_at.strftime("%d.%m %H:%M"))
            mod_item.setData(Qt.ItemDataRole.UserRole, r.updated_at.isoformat())
            self._table.setItem(row_idx, 5, mod_item)

        self._subtitle.setText(f"{len(rows)} документ(ів)")
        self._table.setSortingEnabled(True)
        # Default sort: by "Змінено" desc
        self._table.sortItems(5, Qt.SortOrder.DescendingOrder)

    def _on_double_click(self, item: QTableWidgetItem) -> None:
        row = item.row()
        name_item = self._table.item(row, 1)
        if name_item is None:
            return
        doc_id = name_item.data(Qt.ItemDataRole.UserRole)
        if isinstance(doc_id, int):
            self.document_activated.emit(doc_id)


def _padded(widget: QWidget) -> QWidget:
    """Wrap a widget so it has consistent table-cell padding."""
    wrap = QWidget()
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(8, 4, 8, 4)
    lay.addWidget(widget)
    lay.addStretch(1)
    return wrap
