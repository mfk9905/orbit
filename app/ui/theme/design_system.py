"""
Orbit Design System & Styling Definitions (Logitech Options+ / Premium Glassmorphism Style).
"""

from PySide6.QtGui import QFont, QColor


class OrbitTheme:
    """Centralized Theme Palette and Custom QSS Stylesheet for Orbit Control Center."""

    # Colors
    BG_DARK = "#0B0E14"
    CARD_BG = "#141923"
    CARD_BORDER = "#232D3F"
    CARD_HOVER = "#1C2433"
    CARD_SELECTED = "#253247"
    
    PRIMARY_ACCENT = "#2ED573"
    SECONDARY_ACCENT = "#00F2FE"
    BLUE_ACCENT = "#4FACFE"
    PURPLE_ACCENT = "#9B59B6"
    RED_ACCENT = "#FF4757"
    AMBER_ACCENT = "#FFA502"

    TEXT_MAIN = "#F1F5F9"
    TEXT_MUTED = "#94A3B8"
    TEXT_DIM = "#64748B"

    @classmethod
    def get_font(cls, size: float = 10.0, bold: bool = False) -> QFont:
        font = QFont("Segoe UI", size)
        font.setBold(bold)
        return font

    MAIN_STYLESHEET = """
        QMainWindow, QDialog {
            background-color: #0B0E14;
            color: #F1F5F9;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        QWidget {
            color: #F1F5F9;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        /* Sidebar Styling */
        QListWidget#sidebar {
            background-color: #10141D;
            border: 1px solid #1C2433;
            border-radius: 12px;
            outline: none;
            padding: 8px;
        }

        QListWidget#sidebar::item {
            padding: 12px 16px;
            color: #94A3B8;
            border-radius: 8px;
            margin-bottom: 6px;
            font-weight: 600;
            font-size: 13px;
        }

        QListWidget#sidebar::item:hover {
            background-color: #1A2231;
            color: #F1F5F9;
        }

        QListWidget#sidebar::item:selected {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ED573, stop:1 #10B981);
            color: #042F1A;
            font-weight: 700;
        }

        /* Cards & GroupBoxes */
        QGroupBox {
            font-size: 13px;
            font-weight: 700;
            border: 1px solid #232D3F;
            border-radius: 12px;
            margin-top: 14px;
            padding: 20px 16px 16px 16px;
            background-color: #141923;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            padding: 2px 10px;
            color: #2ED573;
            background-color: #1A2231;
            border: 1px solid #232D3F;
            border-radius: 6px;
        }

        /* Inputs & Combos */
        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
            background-color: #1C2433;
            border: 1px solid #2A364F;
            border-radius: 8px;
            padding: 8px 12px;
            color: #F1F5F9;
            font-size: 13px;
            selection-background-color: #2ED573;
            selection-color: #0B0E14;
        }

        QComboBox:hover, QLineEdit:hover {
            border: 1px solid #2ED573;
        }

        QComboBox::drop-down {
            border: none;
            width: 24px;
        }

        /* Buttons */
        QPushButton {
            background-color: #2ED573;
            color: #042F1A;
            font-size: 13px;
            font-weight: 700;
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
        }

        QPushButton:hover {
            background-color: #26AF5F;
        }

        QPushButton:pressed {
            background-color: #1E8C4A;
        }

        QPushButton#btn_secondary {
            background-color: #1C2433;
            color: #F1F5F9;
            border: 1px solid #2A364F;
        }

        QPushButton#btn_secondary:hover {
            background-color: #253247;
            border-color: #2ED573;
        }

        QPushButton#btn_danger {
            background-color: #FF4757;
            color: #FFFFFF;
        }

        QPushButton#btn_danger:hover {
            background-color: #D63031;
        }

        /* Scrollbars */
        QScrollBar:vertical {
            background: #10141D;
            width: 8px;
            margin: 0px;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical {
            background: #232D3F;
            min-height: 20px;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical:hover {
            background: #2ED573;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        /* Tooltips */
        QToolTip {
            background-color: #1C2433;
            color: #F1F5F9;
            border: 1px solid #2ED573;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }
    """
