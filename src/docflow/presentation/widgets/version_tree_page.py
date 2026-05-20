"""Version tree page.

Layout matches the wireframe "Git-стиль вертикальне дерево":
  * left  : branch list + small legend
  * center: flat commit log (newest first) grouped visually by branch
  * right : panel showing the chosen version with action buttons

A real custom-painted DAG can come later; for MVP the QTreeWidget is enough
to walk history, pick a version and trigger revert/branch/version actions.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from docflow.application.dto import VersionNode


class VersionTreePage(QWidget):
    back_requested = pyqtSignal()
    new_version_requested = pyqtSignal()
    new_branch_from_requested = pyqtSignal(int)   # source version_id
    revert_to_requested = pyqtSignal(int)         # source version_id
    export_copy_requested = pyqtSignal(int)       # version_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._nodes_by_id: dict[int, VersionNode] = {}
        self._chosen_version_id: int | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()
        back = QPushButton("← До списку")
        back.clicked.connect(self.back_requested)
        toolbar.addWidget(back)
        self._new_ver = QPushButton("⨁  Нова версія")
        self._new_ver.setObjectName("Primary")
        self._new_ver.clicked.connect(self.new_version_requested)
        toolbar.addWidget(self._new_ver)
        self._new_branch = QPushButton("⑂  Гілка від обраного")
        self._new_branch.clicked.connect(self._on_new_branch)
        toolbar.addWidget(self._new_branch)
        self._revert = QPushButton("↩  Відкотити до цієї версії")
        self._revert.clicked.connect(self._on_revert)
        toolbar.addWidget(self._revert)
        toolbar.addStretch(1)
        outer.addLayout(toolbar)

        # Header
        self._title = QLabel("🌲  Дерево версій")
        self._title.setObjectName("PageTitle")
        outer.addWidget(self._title)
        self._subtitle = QLabel("")
        self._subtitle.setObjectName("PageSubtitle")
        outer.addWidget(self._subtitle)

        # Body splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter, stretch=1)

        # LEFT — branches
        left = QFrame()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(_section_label("ГІЛКИ"))
        self._branches = QListWidget()
        left_layout.addWidget(self._branches, stretch=1)
        legend = QLabel(
            "<small>"
            "● — коміт у main<br>"
            "○ — коміт у гілці<br>"
            "★ — поточний HEAD<br>"
            "↩ — відкат"
            "</small>"
        )
        legend.setStyleSheet("color: #7A7257; padding: 8px;")
        left_layout.addWidget(legend)
        left.setMinimumWidth(180)
        splitter.addWidget(left)

        # CENTER — commits
        center = QFrame()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(_section_label("КОМІТИ"))
        self._commits = QTreeWidget()
        self._commits.setHeaderLabels(["", "версія", "опис", "автор · коли"])
        self._commits.setRootIsDecorated(False)
        self._commits.setAlternatingRowColors(True)
        self._commits.setColumnWidth(0, 30)
        self._commits.setColumnWidth(1, 90)
        self._commits.itemSelectionChanged.connect(self._on_select)
        center_layout.addWidget(self._commits)
        splitter.addWidget(center)

        # RIGHT — selected version panel
        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_box = QGroupBox("Обрана версія")
        right_box_layout = QVBoxLayout(self._right_box)
        self._chosen_label = QLabel("—")
        self._chosen_label.setStyleSheet("font-size: 16px; font-weight: 700;")
        right_box_layout.addWidget(self._chosen_label)
        form = QFormLayout()
        self._meta_author = QLabel("—")
        self._meta_date = QLabel("—")
        self._meta_branch = QLabel("—")
        self._meta_parent = QLabel("—")
        form.addRow("Автор:", self._meta_author)
        form.addRow("Дата:", self._meta_date)
        form.addRow("Гілка:", self._meta_branch)
        form.addRow("Батько:", self._meta_parent)
        right_box_layout.addLayout(form)

        right_box_layout.addWidget(_section_label("ОПИС ЗМІН"))
        self._desc = QLabel("—")
        self._desc.setWordWrap(True)
        self._desc.setStyleSheet(
            "background:white;border:1px solid #C9C0A5;border-radius:6px;padding:8px;"
        )
        right_box_layout.addWidget(self._desc)

        right_box_layout.addWidget(_section_label("ДІЇ"))
        self._a_new_branch = QPushButton("⑂  Створити гілку звідси")
        self._a_new_branch.clicked.connect(self._on_new_branch)
        right_box_layout.addWidget(self._a_new_branch)
        self._a_revert = QPushButton("↩  Відкотити до цієї версії")
        self._a_revert.clicked.connect(self._on_revert)
        right_box_layout.addWidget(self._a_revert)
        self._a_export = QPushButton("⬇  Зберегти копію…")
        self._a_export.clicked.connect(self._on_export_copy)
        right_box_layout.addWidget(self._a_export)
        right_box_layout.addStretch(1)
        right_layout.addWidget(self._right_box)

        splitter.addWidget(right)
        splitter.setSizes([200, 700, 320])
        self._set_actions_enabled(False)

    # -- Public API --

    def set_for_document(self, name: str, nodes: list[VersionNode]) -> None:
        self._title.setText(f"🌲  Дерево версій — {name}")
        self._subtitle.setText(f"{len(nodes)} версій")

        # Branches
        self._branches.clear()
        seen: dict[int, str] = {}
        head_label_per_branch: dict[int, str] = {}
        for n in nodes:
            if n.branch_id not in seen:
                seen[n.branch_id] = n.branch_name
            if n.is_head:
                head_label_per_branch[n.branch_id] = n.label
        for bid, bname in seen.items():
            text = f"⑂ {bname}    {head_label_per_branch.get(bid, '')}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, bid)
            self._branches.addItem(item)

        # Commits
        self._commits.clear()
        self._nodes_by_id = {n.version_id: n for n in nodes}
        for n in nodes:
            marker = "★" if n.is_head else ("●" if n.branch_name == "main" else "○")
            when = n.created_at.strftime("%d.%m %H:%M")
            row = QTreeWidgetItem(
                [marker, n.label, n.message, f"{n.created_by} · {when}"]
            )
            row.setData(0, Qt.ItemDataRole.UserRole, n.version_id)
            self._commits.addTopLevelItem(row)

        self._set_actions_enabled(False)
        self._chosen_version_id = None
        self._chosen_label.setText("—")

    # -- Internals --

    def _on_select(self) -> None:
        item = self._commits.currentItem()
        if not item:
            return
        vid = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(vid, int):
            return
        n = self._nodes_by_id.get(vid)
        if n is None:
            return
        self._chosen_version_id = vid
        self._chosen_label.setText(
            f"{n.label} {'★ HEAD · ' + n.branch_name if n.is_head else '· ' + n.branch_name}"
        )
        self._meta_author.setText(n.created_by)
        self._meta_date.setText(n.created_at.strftime("%d.%m.%Y %H:%M"))
        self._meta_branch.setText(n.branch_name)
        parent = self._nodes_by_id.get(n.parent_version_id) if n.parent_version_id else None
        self._meta_parent.setText(parent.label if parent else "—")
        self._desc.setText(n.message or "Без опису")
        self._set_actions_enabled(True)

    def _set_actions_enabled(self, enabled: bool) -> None:
        self._new_branch.setEnabled(enabled)
        self._revert.setEnabled(enabled)
        self._a_new_branch.setEnabled(enabled)
        self._a_revert.setEnabled(enabled)
        self._a_export.setEnabled(enabled)

    def _on_new_branch(self) -> None:
        if self._chosen_version_id is not None:
            self.new_branch_from_requested.emit(self._chosen_version_id)

    def _on_revert(self) -> None:
        if self._chosen_version_id is not None:
            self.revert_to_requested.emit(self._chosen_version_id)

    def _on_export_copy(self) -> None:
        if self._chosen_version_id is not None:
            self.export_copy_requested.emit(self._chosen_version_id)


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("SidebarSection")
    return lbl
