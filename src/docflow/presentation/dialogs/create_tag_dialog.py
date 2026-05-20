"""Create / edit a tag.

Same dialog covers both "+ Новий тег" and "edit existing tag" — caller
passes ``initial`` when editing.
"""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from docflow.presentation.styles.theme import TAG_COLORS

COLOR_ORDER = ["yellow", "mint", "blue", "pink", "purple", "orange", "gray"]


@dataclass(slots=True)
class TagFormData:
    name: str
    color: str
    description: str


class CreateTagDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        initial: TagFormData | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Редагувати тег" if initial else "Новий тег")
        self.setMinimumSize(420, 280)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._name = QLineEdit(initial.name if initial else "")
        form.addRow("Назва:", self._name)

        # Color picker — row of color swatches
        color_row = QHBoxLayout()
        self._color_group = QButtonGroup(self)
        self._color = initial.color if initial else "yellow"
        for c in COLOR_ORDER:
            bg, fg = TAG_COLORS[c]
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setFixedSize(24, 24)
            border_color = "#2C2C2C" if c == self._color else "#C9C0A5"
            border_style = "dashed" if c == "gray" else "solid"
            btn.setStyleSheet(
                f"QPushButton {{ background: {bg if bg != 'transparent' else 'white'};"
                f" border: 2px {border_style} {border_color}; border-radius: 12px; }}"
            )
            btn.setChecked(c == self._color)
            btn.clicked.connect(lambda _checked, color=c: self._set_color(color))
            self._color_group.addButton(btn)
            color_row.addWidget(btn)
        color_row.addStretch(1)
        form.addRow("Колір:", _wrap_layout(color_row))

        self._description = QTextEdit(initial.description if initial else "")
        self._description.setFixedHeight(70)
        form.addRow("Опис:", self._description)

        layout.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            "✓ Зберегти" if initial else "✓ Створити"
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _set_color(self, color: str) -> None:
        self._color = color
        for i, btn in enumerate(self._color_group.buttons()):
            c = COLOR_ORDER[i]
            bg, _ = TAG_COLORS[c]
            border_color = "#2C2C2C" if c == color else "#C9C0A5"
            border_style = "dashed" if c == "gray" else "solid"
            btn.setStyleSheet(
                f"QPushButton {{ background: {bg if bg != 'transparent' else 'white'};"
                f" border: 2px {border_style} {border_color}; border-radius: 12px; }}"
            )
            btn.setChecked(c == color)

    def _on_accept(self) -> None:
        if not self._name.text().strip():
            QMessageBox.warning(self, "Назва", "Введіть назву тегу.")
            return
        self.accept()

    def data(self) -> TagFormData:
        return TagFormData(
            name=self._name.text().strip(),
            color=self._color,
            description=self._description.toPlainText().strip(),
        )


def _wrap_layout(layout: QHBoxLayout) -> QWidget:
    w = QWidget()
    w.setLayout(layout)
    return w
