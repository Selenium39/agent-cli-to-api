"""Modern dark-theme QSS stylesheet for the desktop gateway app."""

from __future__ import annotations

DARK_THEME = """
/* ── Global ─────────────────────────────────────────────── */
QWidget {
    background-color: #1a1b26;
    color: #c0caf5;
    font-size: 13px;
}

/* ── Main Window ────────────────────────────────────────── */
QMainWindow {
    background-color: #1a1b26;
}

/* ── Group Box (cards) ──────────────────────────────────── */
QGroupBox {
    background-color: #24283b;
    border: 1px solid #414868;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
}
QGroupBox::title {
    color: #7aa2f7;
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
}

/* ── Labels ─────────────────────────────────────────────── */
QLabel {
    color: #a9b1d6;
    background: transparent;
}
QLabel#title_label {
    font-size: 18px;
    font-weight: bold;
    color: #c0caf5;
}
QLabel#version_label {
    font-size: 11px;
    color: #565f89;
}
QLabel#status_label {
    font-size: 13px;
    font-weight: bold;
}
QLabel#url_display {
    font-size: 13px;
    color: #9ece6a;
    font-family: monospace;
    padding: 6px 10px;
    background-color: #1a1b26;
    border: 1px solid #414868;
    border-radius: 4px;
}

/* ── Inputs ─────────────────────────────────────────────── */
QLineEdit, QSpinBox {
    background-color: #1a1b26;
    color: #c0caf5;
    border: 1px solid #414868;
    border-radius: 5px;
    padding: 5px 8px;
    selection-background-color: #364a82;
}
QLineEdit:focus, QSpinBox:focus {
    border-color: #7aa2f7;
}
QLineEdit:disabled, QSpinBox:disabled {
    color: #565f89;
    background-color: #1e2030;
}

/* ── Combo Box ──────────────────────────────────────────── */
QComboBox {
    background-color: #1a1b26;
    color: #c0caf5;
    border: 1px solid #414868;
    border-radius: 5px;
    padding: 5px 28px 5px 8px;
    min-width: 110px;
}
QComboBox:focus {
    border-color: #7aa2f7;
}
QComboBox:disabled {
    color: #565f89;
    background-color: #1e2030;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #414868;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #7aa2f7;
    margin-right: 4px;
}
QComboBox QAbstractItemView {
    background-color: #24283b;
    color: #c0caf5;
    border: 1px solid #414868;
    selection-background-color: #364a82;
    selection-color: #c0caf5;
    outline: none;
}

/* ── Buttons ────────────────────────────────────────────── */
QPushButton {
    background-color: #7aa2f7;
    color: #1a1b26;
    border: none;
    border-radius: 6px;
    padding: 7px 20px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #89b4fa;
}
QPushButton:pressed {
    background-color: #6183d6;
}
QPushButton:disabled {
    background-color: #414868;
    color: #565f89;
}
QPushButton#stop_btn {
    background-color: #f7768e;
}
QPushButton#stop_btn:hover {
    background-color: #ff9bae;
}
QPushButton#stop_btn:pressed {
    background-color: #d65d73;
}
QPushButton#copy_btn, QPushButton#clear_btn {
    background-color: #414868;
    color: #a9b1d6;
    padding: 5px 14px;
    font-weight: normal;
}
QPushButton#copy_btn:hover, QPushButton#clear_btn:hover {
    background-color: #565f89;
}

/* ── Log viewer ─────────────────────────────────────────── */
QPlainTextEdit#log_viewer {
    background-color: #16161e;
    color: #a9b1d6;
    border: 1px solid #414868;
    border-radius: 6px;
    padding: 8px;
    font-family: "Cascadia Code", "SF Mono", "Menlo", "Consolas", "DejaVu Sans Mono", monospace;
    font-size: 12px;
    selection-background-color: #364a82;
}

/* ── Scrollbar ──────────────────────────────────────────── */
QScrollBar:vertical {
    background: #1a1b26;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #414868;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #565f89;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

/* ── Menu (system tray) ─────────────────────────────────── */
QMenu {
    background-color: #24283b;
    color: #c0caf5;
    border: 1px solid #414868;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #364a82;
}
QMenu::separator {
    height: 1px;
    background: #414868;
    margin: 4px 8px;
}

/* ── Tooltip ────────────────────────────────────────────── */
QToolTip {
    background-color: #24283b;
    color: #c0caf5;
    border: 1px solid #414868;
    border-radius: 4px;
    padding: 4px 8px;
}
"""
