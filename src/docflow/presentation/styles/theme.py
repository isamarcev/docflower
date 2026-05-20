"""Visual theme — colors, tag palette and the global QSS stylesheet.

The look targets the warm beige Notion-style palette from the wireframes.
Kept as plain strings so it stays editable without touching widget code.
"""

from __future__ import annotations

# -------- Brand palette --------

BG_PRIMARY = "#EFEAD8"  # main background (warm beige)
BG_SIDEBAR = "#E8E0C9"  # slightly darker sidebar
BG_CONTENT = "#F5F0DD"  # content panes
BG_ELEVATED = "#FFFFFF"
BORDER = "#C9C0A5"
TEXT_PRIMARY = "#2C2C2C"
TEXT_SECONDARY = "#7A7257"
TEXT_MUTED = "#A39A7B"
SELECTED = "#F8E89B"  # selected row highlight
ACCENT = "#2C2C2C"  # primary button
DANGER_BG = "#F2C8C8"
DANGER_FG = "#7A2C2C"

# -------- Tag chip palette --------

TAG_COLORS: dict[str, tuple[str, str]] = {
    # name -> (background, text)
    "yellow": ("#F4D87A", "#5A4A1A"),
    "mint": ("#A8DBC1", "#1F4D3A"),
    "blue": ("#B5D4E8", "#1F3F5A"),
    "pink": ("#F4A8B5", "#5A1F2C"),
    "purple": ("#C7B4D9", "#3F2C5A"),
    "orange": ("#E8A87C", "#5A2F1F"),
    "gray": ("transparent", TEXT_SECONDARY),  # draft style (dashed border)
}

DOC_TYPE_BADGE: dict[str, tuple[str, str]] = {
    # extension -> (background, text)
    "docx": ("#B5D4E8", "#1F3F5A"),
    "xlsx": ("#A8DBC1", "#1F4D3A"),
    "xls": ("#A8DBC1", "#1F4D3A"),
    "pdf": ("#F4A8B5", "#5A1F2C"),
}


# -------- Global QSS --------

QSS = f"""
QMainWindow, QDialog, QWidget {{
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}

QMenuBar {{
    background-color: {BG_PRIMARY};
    padding: 4px;
    border-bottom: 1px solid {BORDER};
}}
QMenuBar::item {{
    padding: 4px 10px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background-color: {SELECTED};
    border-radius: 4px;
}}
QMenu {{
    background-color: {BG_CONTENT};
    border: 1px solid {BORDER};
}}
QMenu::item:selected {{
    background-color: {SELECTED};
}}

QToolBar {{
    background-color: {BG_PRIMARY};
    border: none;
    spacing: 6px;
    padding: 6px;
}}

/* --- Sidebar --- */
QFrame#Sidebar {{
    background-color: {BG_SIDEBAR};
    border-right: 1px solid {BORDER};
}}
QLabel#SidebarSection {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    padding: 12px 14px 4px;
}}
QListWidget#SidebarList {{
    background: transparent;
    border: none;
    padding: 2px 6px;
}}
QListWidget#SidebarList::item {{
    padding: 6px 10px;
    border-radius: 6px;
    margin: 1px 4px;
}}
QListWidget#SidebarList::item:selected {{
    background-color: {ACCENT};
    color: white;
}}
QListWidget#SidebarList::item:hover:!selected {{
    background-color: rgba(0,0,0,0.05);
}}

/* --- Content --- */
QFrame#ContentArea {{
    background-color: {BG_CONTENT};
}}
QLabel#PageTitle {{
    font-size: 20px;
    font-weight: 700;
    padding: 8px 16px;
}}
QLabel#PageSubtitle {{
    color: {TEXT_SECONDARY};
    padding: 0 16px 8px;
}}

/* --- Buttons --- */
QPushButton {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 12px;
}}
QPushButton:hover {{
    background-color: {SELECTED};
}}
QPushButton#Primary {{
    background-color: {ACCENT};
    color: white;
    border: none;
}}
QPushButton#Primary:hover {{
    background-color: #1F1F1F;
}}
QPushButton#Danger {{
    background-color: {DANGER_BG};
    color: {DANGER_FG};
    border: 1px solid {DANGER_FG};
}}

/* --- Inputs --- */
QLineEdit, QTextEdit, QComboBox {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 8px;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}

/* --- Tables --- */
QTableWidget, QTableView {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: {BORDER};
    selection-background-color: {SELECTED};
    selection-color: {TEXT_PRIMARY};
    alternate-background-color: #FBF7E8;
}}
QHeaderView::section {{
    background-color: {BG_SIDEBAR};
    color: {TEXT_SECONDARY};
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
}}

/* --- Status bar --- */
QStatusBar {{
    background-color: {BG_SIDEBAR};
    border-top: 1px solid {BORDER};
    color: {TEXT_SECONDARY};
}}

/* --- Splitter --- */
QSplitter::handle {{
    background-color: {BORDER};
}}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical   {{ height: 1px; }}

/* --- ScrollBars (soft) --- */
QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 4px; min-height: 30px;
}}
QScrollBar:horizontal {{
    background: transparent; height: 10px; margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER}; border-radius: 4px; min-width: 30px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
"""


def doc_type_badge_style(doc_type: str) -> str:
    bg, fg = DOC_TYPE_BADGE.get(doc_type, ("#DDD", TEXT_PRIMARY))
    return (
        f"background: {bg}; color: {fg}; "
        f"border-radius: 3px; padding: 1px 6px; "
        f"font-family: monospace; font-size: 11px; font-weight: 600;"
    )
