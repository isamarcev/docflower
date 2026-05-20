"""Application main window.

The window owns the use-case bundle and routes user actions across the four
content pages (list / card / version tree / audit) and the modal dialogs.
Everything UI-specific lives here; business rules live in application/.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QWidget,
)

from docflow.application.dto import (
    CreateBranchInput,
    CreateVersionInput,
    ImportDocumentInput,
)
from docflow.domain.exceptions import DomainError
from docflow.presentation.dialogs.add_document_dialog import AddDocumentDialog
from docflow.presentation.dialogs.confirm_delete_dialog import ConfirmDeleteDialog
from docflow.presentation.dialogs.create_tag_dialog import CreateTagDialog
from docflow.presentation.dialogs.edit_metadata_dialog import EditMetadataDialog
from docflow.presentation.dialogs.new_version_dialog import NewVersionDialog
from docflow.presentation.dialogs.tag_manager_dialog import TagManagerDialog
from docflow.presentation.dialogs.tag_picker_dialog import TagPickerDialog
from docflow.presentation.styles.theme import QSS
from docflow.presentation.widgets.audit_page import AuditPage
from docflow.presentation.widgets.doc_card_page import DocumentCardPage
from docflow.presentation.widgets.doc_list_page import DocumentListPage
from docflow.presentation.widgets.sidebar import Sidebar
from docflow.presentation.widgets.version_tree_page import VersionTreePage

if TYPE_CHECKING:
    from docflow.main.container import UseCases


PAGE_LIST = 0
PAGE_CARD = 1
PAGE_TREE = 2
PAGE_AUDIT = 3


class MainWindow(QMainWindow):
    def __init__(self, use_cases: "UseCases", *, current_user: str) -> None:
        super().__init__()
        self._use_cases = use_cases
        self._current_user = current_user
        self._current_doc_id: int | None = None
        self._filter_tag_id: int | None = None
        self._search_text: str = ""

        self.setWindowTitle("DocFlow — Документообіг служби списання")
        self.resize(1320, 820)
        self.setStyleSheet(QSS)

        self._build_menu()
        self._build_toolbar()
        self._build_central()
        self._build_status_bar()

        self.refresh_all()

    # ---------- UI construction ----------

    def _build_menu(self) -> None:
        menu = self.menuBar()

        m_file = menu.addMenu("&Файл")
        act_add = QAction("Додати документ…", self)
        act_add.setShortcut(QKeySequence("Ctrl+N"))
        act_add.triggered.connect(self._on_add_document)
        m_file.addAction(act_add)
        m_file.addSeparator()
        act_export = QAction("Експортувати документ…", self)
        act_export.triggered.connect(self._on_export_current)
        m_file.addAction(act_export)
        m_file.addSeparator()
        act_quit = QAction("Вийти", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self.close)
        m_file.addAction(act_quit)

        menu.addMenu("&Правка")
        menu.addMenu("&Вигляд")

        m_doc = menu.addMenu("&Документ")
        m_doc.addAction("Нова версія…").triggered.connect(self._on_new_version)
        m_doc.addAction("Створити гілку…").triggered.connect(self._on_new_branch)
        m_doc.addAction("Дерево версій").triggered.connect(self._on_show_tree)
        m_doc.addSeparator()
        m_doc.addAction("Видалити…").triggered.connect(self._on_delete_document)

        m_tools = menu.addMenu("&Інструменти")
        m_tools.addAction("Керування тегами…").triggered.connect(self._on_manage_tags)
        m_tools.addAction("Журнал дій").triggered.connect(lambda: self._goto(PAGE_AUDIT))

        menu.addMenu("&Довідка")

    def _build_toolbar(self) -> None:
        tb = QToolBar()
        tb.setMovable(False)
        self.addToolBar(tb)

        btn_add = QPushButton("+ Додати документ")
        btn_add.setObjectName("Primary")
        btn_add.clicked.connect(self._on_add_document)
        tb.addWidget(btn_add)

        btn_version = QPushButton("⨁ Нова версія")
        btn_version.clicked.connect(self._on_new_version)
        tb.addWidget(btn_version)

        btn_branch = QPushButton("⑂ Гілка")
        btn_branch.clicked.connect(self._on_new_branch)
        tb.addWidget(btn_branch)

        btn_delete = QPushButton("🗑 Видалити")
        btn_delete.setObjectName("Danger")
        btn_delete.clicked.connect(self._on_delete_document)
        tb.addWidget(btn_delete)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔎  пошук за назвою…")
        self._search.setMinimumWidth(280)
        self._search.textChanged.connect(self._on_search_changed)
        tb.addWidget(self._search)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        btn_export = QPushButton("⬇ Експорт документа")
        btn_export.clicked.connect(self._on_export_current)
        tb.addWidget(btn_export)

    def _build_central(self) -> None:
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.navigation_changed.connect(self._on_navigate)
        layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._page_list = DocumentListPage()
        self._page_list.document_activated.connect(self._on_document_activated)
        self._page_card = DocumentCardPage()
        self._page_tree = VersionTreePage()
        self._page_audit = AuditPage()

        # Wire card signals
        self._page_card.back_requested.connect(lambda: self._goto(PAGE_LIST))
        self._page_card.open_externally_requested.connect(self._on_open_externally)
        self._page_card.edit_metadata_requested.connect(self._on_edit_metadata)
        self._page_card.new_version_requested.connect(lambda _doc: self._on_new_version())
        self._page_card.new_branch_requested.connect(lambda _doc: self._on_new_branch())
        self._page_card.show_tree_requested.connect(lambda _doc: self._on_show_tree())
        self._page_card.delete_requested.connect(lambda _doc: self._on_delete_document())
        self._page_card.export_requested.connect(lambda _doc: self._on_export_current())
        self._page_card.add_tag_requested.connect(self._on_add_tag_to_current)
        self._page_card.detach_tag_requested.connect(self._on_detach_tag)

        # Wire tree signals
        self._page_tree.back_requested.connect(lambda: self._goto(PAGE_CARD))
        self._page_tree.new_version_requested.connect(self._on_new_version)
        self._page_tree.new_branch_from_requested.connect(self._on_new_branch_from_version)
        self._page_tree.revert_to_requested.connect(self._on_revert_to_version)
        self._page_tree.export_copy_requested.connect(self._on_export_version_copy)

        self._stack.addWidget(self._page_list)
        self._stack.addWidget(self._page_card)
        self._stack.addWidget(self._page_tree)
        self._stack.addWidget(self._page_audit)
        layout.addWidget(self._stack, stretch=1)

        self.setCentralWidget(central)

    def _build_status_bar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_label = QLabel("Готово")
        sb.addPermanentWidget(self._status_label)

    # ---------- Refresh ----------

    def refresh_all(self) -> None:
        self._refresh_list()
        self._sidebar.set_tags(self._use_cases.list_tags())
        self._page_audit.set_rows(self._use_cases.list_audit(limit=200))

    def _refresh_list(self) -> None:
        rows = self._use_cases.list_documents(
            name_query=self._search_text or None,
            tag_id=self._filter_tag_id,
        )
        self._page_list.set_rows(rows)
        self._status_label.setText(f"{len(rows)} документ(ів)")

    # ---------- Navigation ----------

    def _on_navigate(self, key: str) -> None:
        if key == "audit":
            self._goto(PAGE_AUDIT)
            return
        if key in ("archive", "settings"):
            QMessageBox.information(
                self,
                "Скоро",
                "Цей розділ буде доступний у наступній ітерації.",
            )
            return
        if key.startswith("tag:"):
            try:
                self._filter_tag_id = int(key.split(":", 1)[1])
            except ValueError:
                self._filter_tag_id = None
            self._page_list.set_title("📄  Фільтр за тегом", "")
        else:
            self._filter_tag_id = None
            self._page_list.set_title("📄  Усі документи", "")
        self._refresh_list()
        self._goto(PAGE_LIST)

    def _on_search_changed(self, text: str) -> None:
        self._search_text = text
        self._refresh_list()

    def _on_document_activated(self, doc_id: int) -> None:
        self._current_doc_id = doc_id
        self._show_card(doc_id)

    def _show_card(self, doc_id: int) -> None:
        try:
            details = self._use_cases.get_document_details(doc_id)
        except DomainError as e:
            QMessageBox.critical(self, "Помилка", e.message)
            return
        self._page_card.set_document(details)
        self._goto(PAGE_CARD)

    def _on_show_tree(self) -> None:
        if self._current_doc_id is None:
            return
        try:
            details = self._use_cases.get_document_details(self._current_doc_id)
        except DomainError as e:
            QMessageBox.critical(self, "Помилка", e.message)
            return
        nodes = self._use_cases.get_version_tree(self._current_doc_id)
        self._page_tree.set_for_document(details.name, nodes)
        self._goto(PAGE_TREE)

    def _goto(self, page: int) -> None:
        self._stack.setCurrentIndex(page)

    # ---------- Document actions ----------

    def _on_add_document(self) -> None:
        dlg = AddDocumentDialog(self)
        if not dlg.exec():
            return
        for path in dlg.selected_files():
            try:
                self._use_cases.import_document(
                    ImportDocumentInput(
                        name=Path(path).name,
                        source_path=Path(path),
                        actor=self._current_user,
                    )
                )
            except DomainError as e:
                QMessageBox.critical(self, "Помилка імпорту", e.message)
                return
            except Exception as e:  # noqa: BLE001
                QMessageBox.critical(self, "Помилка імпорту", str(e))
                return
        self.refresh_all()

    def _on_delete_document(self) -> None:
        if self._current_doc_id is None:
            QMessageBox.information(self, "Видалення", "Спершу оберіть документ зі списку.")
            return
        dlg = ConfirmDeleteDialog(self)
        if not dlg.exec():
            return
        try:
            self._use_cases.delete_document(self._current_doc_id, actor=self._current_user)
        except DomainError as e:
            QMessageBox.critical(self, "Помилка видалення", e.message)
            return
        self._current_doc_id = None
        self._goto(PAGE_LIST)
        self.refresh_all()

    def _on_edit_metadata(self, doc_id: int) -> None:
        try:
            details = self._use_cases.get_document_details(doc_id)
        except DomainError as e:
            QMessageBox.critical(self, "Помилка", e.message)
            return
        dlg = EditMetadataDialog(
            name=details.name, description=details.description, parent=self
        )
        if not dlg.exec():
            return
        self._use_cases.update_document(
            document_id=doc_id,
            name=dlg.chosen_name(),
            description=dlg.chosen_description(),
            actor=self._current_user,
        )
        self.refresh_all()
        self._show_card(doc_id)

    def _on_open_externally(self, doc_id: int) -> None:
        try:
            details = self._use_cases.get_document_details(doc_id)
        except DomainError as e:
            QMessageBox.critical(self, "Помилка", e.message)
            return
        if not details.file_path:
            QMessageBox.information(self, "Файл відсутній", "У документа немає версій.")
            return
        abs_path = self._use_cases.resolve_path(details.file_path)
        if not abs_path.exists():
            QMessageBox.warning(
                self, "Файл не знайдено", f"Не знайдено файл: {abs_path}"
            )
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(abs_path)))

    # ---------- Versioning ----------

    def _on_new_version(self) -> None:
        self._open_new_version_dialog(mode="version")

    def _on_new_branch(self) -> None:
        self._open_new_version_dialog(mode="branch")

    def _open_new_version_dialog(self, *, mode: str) -> None:
        if self._current_doc_id is None:
            QMessageBox.information(self, "Документ не обрано", "Спершу оберіть документ зі списку.")
            return
        try:
            details = self._use_cases.get_document_details(self._current_doc_id)
        except DomainError as e:
            QMessageBox.critical(self, "Помилка", e.message)
            return
        dlg = NewVersionDialog(details, parent=self, mode=mode)  # type: ignore[arg-type]
        if not dlg.exec():
            return
        self._apply_new_version(details, dlg)

    def _apply_new_version(self, details, dlg: NewVersionDialog) -> None:  # noqa: ANN001
        try:
            if dlg.is_branch_mode():
                # 1) create branch off current HEAD
                head_node = next(
                    (v for v in details.recent_versions if v.is_head), None
                ) or details.recent_versions[0]
                branch = self._use_cases.create_branch(
                    CreateBranchInput(
                        document_id=details.id,
                        parent_version_id=head_node.version_id,
                        name=dlg.chosen_branch_name(),
                        actor=self._current_user,
                    )
                )
                # 2) put the first version inside it
                self._use_cases.create_version(
                    CreateVersionInput(
                        document_id=details.id,
                        branch_id=branch.id or 0,
                        parent_version_id=head_node.version_id,
                        source_path=dlg.chosen_source(),
                        message=dlg.chosen_message(),
                        actor=self._current_user,
                    )
                )
            else:
                head_node = next(
                    (v for v in details.recent_versions if v.is_head), None
                ) or details.recent_versions[0]
                self._use_cases.create_version(
                    CreateVersionInput(
                        document_id=details.id,
                        branch_id=head_node.branch_id,
                        parent_version_id=head_node.version_id,
                        source_path=dlg.chosen_source(),
                        message=dlg.chosen_message(),
                        actor=self._current_user,
                    )
                )
        except DomainError as e:
            QMessageBox.critical(self, "Помилка", e.message)
            return
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Помилка", str(e))
            return
        self.refresh_all()
        self._show_card(details.id)

    def _on_new_branch_from_version(self, version_id: int) -> None:
        # Triggered from version tree: creates a branch off the chosen version
        if self._current_doc_id is None:
            return
        try:
            details = self._use_cases.get_document_details(self._current_doc_id)
        except DomainError as e:
            QMessageBox.critical(self, "Помилка", e.message)
            return
        dlg = NewVersionDialog(details, parent=self, mode="branch")
        if not dlg.exec():
            return
        try:
            branch = self._use_cases.create_branch(
                CreateBranchInput(
                    document_id=details.id,
                    parent_version_id=version_id,
                    name=dlg.chosen_branch_name(),
                    actor=self._current_user,
                )
            )
            self._use_cases.create_version(
                CreateVersionInput(
                    document_id=details.id,
                    branch_id=branch.id or 0,
                    parent_version_id=version_id,
                    source_path=dlg.chosen_source(),
                    message=dlg.chosen_message(),
                    actor=self._current_user,
                )
            )
        except DomainError as e:
            QMessageBox.critical(self, "Помилка", e.message)
            return
        self.refresh_all()
        self._on_show_tree()

    def _on_revert_to_version(self, version_id: int) -> None:
        if self._current_doc_id is None:
            return
        confirm = QMessageBox.question(
            self,
            "Відкат версії",
            "Створити нову версію з вмістом обраної (в історії все збережеться)?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        # Resolve branch_id from the version tree (find chosen node)
        nodes = self._use_cases.get_version_tree(self._current_doc_id)
        node = next((n for n in nodes if n.version_id == version_id), None)
        if node is None:
            return
        try:
            self._use_cases.revert_to_version(
                version_id=version_id, branch_id=node.branch_id, actor=self._current_user
            )
        except DomainError as e:
            QMessageBox.critical(self, "Помилка відкату", e.message)
            return
        self.refresh_all()
        self._on_show_tree()

    # ---------- Tags ----------

    def _on_manage_tags(self) -> None:
        dlg = TagManagerDialog(
            list_tags=self._use_cases.list_tags,
            create_tag=self._use_cases.create_tag,
            update_tag=self._use_cases.update_tag,
            delete_tag=self._use_cases.delete_tag,
            parent=self,
        )
        dlg.exec()
        self.refresh_all()
        if self._current_doc_id is not None:
            self._show_card(self._current_doc_id)

    def _on_add_tag_to_current(self, doc_id: int) -> None:
        try:
            details = self._use_cases.get_document_details(doc_id)
        except DomainError as e:
            QMessageBox.critical(self, "Помилка", e.message)
            return
        all_tags = self._use_cases.list_tags()
        attached_ids = [t.id for t in details.tags]
        picker = TagPickerDialog(all_tags, parent=self, exclude_tag_ids=attached_ids)
        if not picker.exec():
            return
        if picker.wants_create_new():
            cdlg = CreateTagDialog(self)
            if not cdlg.exec():
                return
            data = cdlg.data()
            try:
                tag = self._use_cases.create_tag(
                    name=data.name, color=data.color, description=data.description
                )
            except DomainError as e:
                QMessageBox.warning(self, "Не вдалося створити тег", e.message)
                return
            tag_id = tag.id or 0
        else:
            tag_id = picker.chosen_id() or 0
            if tag_id == 0:
                return
        self._use_cases.attach_tag(document_id=doc_id, tag_id=tag_id, actor=self._current_user)
        self.refresh_all()
        self._show_card(doc_id)

    def _on_detach_tag(self, doc_id: int, tag_id: int) -> None:
        self._use_cases.detach_tag(document_id=doc_id, tag_id=tag_id, actor=self._current_user)
        self.refresh_all()
        self._show_card(doc_id)

    # ---------- Export ----------

    def _on_export_current(self) -> None:
        if self._current_doc_id is None:
            QMessageBox.information(self, "Експорт", "Спершу оберіть документ.")
            return
        try:
            details = self._use_cases.get_document_details(self._current_doc_id)
        except DomainError as e:
            QMessageBox.critical(self, "Помилка", e.message)
            return
        default_name = f"{details.name}.zip"
        path, _ = QFileDialog.getSaveFileName(
            self, "Експортувати документ", default_name, "ZIP архів (*.zip)"
        )
        if not path:
            return
        try:
            self._use_cases.export_document(
                self._current_doc_id, destination=Path(path), actor=self._current_user
            )
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Помилка експорту", str(e))
            return
        QMessageBox.information(self, "Експорт", f"Збережено: {path}")
        self.refresh_all()

    def _on_export_version_copy(self, version_id: int) -> None:
        # Export a single-version blob into a chosen folder, with its original-style filename.
        nodes = self._use_cases.get_version_tree(self._current_doc_id or 0)
        node = next((n for n in nodes if n.version_id == version_id), None)
        if node is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти копію версії", f"{node.label}.bin", "Файли (*.*)"
        )
        if not path:
            return
        try:
            self._use_cases.export_version_copy(version_id=version_id, destination=Path(path))
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Помилка експорту", str(e))
            return
