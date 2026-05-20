"""Pill-shaped tag chip rendered with QPainter.

Why custom-painted instead of styled QLabel:
* QSS ``border-radius`` is inconsistent in Qt for narrow widgets — short text
  ("Q4", "ОЗ", "акт") renders as a near-rectangle while long text renders
  correctly as a pill.
* A combined ``border + border-radius`` rule sometimes produces visible
  square corners on the border layer.
* Manually drawing ``QPainter.drawRoundedRect(radius = height / 2)`` gives a
  perfect pill at any width and avoids QSS edge cases entirely.
"""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QWidget

from docflow.presentation.styles.theme import BORDER, TAG_COLORS


class TagChip(QWidget):
    """Pill-shaped tag chip.

    Constructed with either:
    * ``color="gray"|"yellow"|"mint"|...`` — colour name from ``TAG_COLORS``;
    * ``bg`` and ``fg`` overrides — used by the audit-log action chips, where
      we want a specific (bg, fg) pair that isn't in the tag palette.

    The widget computes its own size from the text and a fixed pill height of
    22 px, with 12 px of horizontal padding on each side.
    """

    HEIGHT = 22
    HPADDING = 12

    def __init__(
        self,
        name: str,
        color: str = "gray",
        parent: QWidget | None = None,
        *,
        bg: str | None = None,
        fg: str | None = None,
    ) -> None:
        super().__init__(parent)
        self._name = name
        self._is_dashed = color == "gray" and bg is None
        if bg is not None and fg is not None:
            self._bg = bg
            self._fg = fg
        else:
            self._bg, self._fg = TAG_COLORS.get(color, TAG_COLORS["gray"])

        # Font: matches old QSS (Segoe UI, 9pt, medium weight).
        self._font = QFont()
        self._font.setPointSize(9)
        self._font.setWeight(QFont.Weight.Medium)

        metrics = QFontMetrics(self._font)
        text_w = metrics.horizontalAdvance(name)
        self._size = QSize(text_w + self.HPADDING * 2, self.HEIGHT)
        self.setFixedSize(self._size)

    def sizeHint(self) -> QSize:  # noqa: N802 — Qt API
        return self._size

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 — Qt API
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Inset by 0.5px so the 1px outline sits on integer pixel boundaries and
        # the right/bottom edges aren't clipped.
        rect = self.rect().adjusted(0, 0, -1, -1)
        radius = rect.height() / 2.0

        if self._is_dashed:
            # Draft style: transparent fill, dashed border in the theme border color.
            pen = QPen(QColor(BORDER))
            pen.setWidth(1)
            pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
        else:
            # Solid coloured pill with a thin same-tone outline for contrast on
            # light selection / alternate-row backgrounds.
            outline = QColor(self._fg)
            outline.setAlpha(80)  # subtle, doesn't dominate the fill
            pen = QPen(outline)
            pen.setWidth(1)
            p.setPen(pen)
            p.setBrush(QColor(self._bg))

        p.drawRoundedRect(rect, radius, radius)

        # Text
        p.setPen(QColor(self._fg))
        p.setFont(self._font)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._name)
        p.end()
