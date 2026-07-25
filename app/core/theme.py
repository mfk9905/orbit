"""
Design Tokens & Theme Constants for Orbit Radial Menu Application.
Centralized color palettes, typography, dimensions, and animation curves.
"""

from PySide6.QtGui import QColor, QFont


class DesignTokens:
    """Centralized UI Design System Tokens."""

    # Color Palette - Modern Glassmorphism & Dark Aesthetic
    PRIMARY_ACCENT = "#2ED573"       # Emerald Green
    PRIMARY_ACCENT_HOVER = "#26AF5F"
    SECONDARY_ACCENT = "#3498DB"     # Bright Blue
    WARNING_ACCENT = "#FFA502"       # Amber
    DANGER_ACCENT = "#E74C3C"        # Crimson Red
    PURPLE_ACCENT = "#9B59B6"        # Amethyst

    # Backgrounds & Glassmorphism
    BG_DARK_OVERLAY = QColor(20, 26, 34, 235)
    BG_DARK_OPAQUE = QColor(20, 26, 34, 255)
    BG_CORE_NORMAL = QColor(16, 20, 26, 245)
    BG_CORE_HOVER = QColor(35, 45, 55, 240)
    BG_GLOW_START = QColor(46, 213, 115, 38)
    BG_GLOW_MID = QColor(46, 213, 115, 8)

    # Borders & Pens
    BORDER_NORMAL = QColor(55, 65, 78, 180)
    BORDER_HOVER = QColor(255, 255, 255, 255)

    # Typography
    FONT_FAMILY = "Outfit"
    FONT_SIZE_LABEL = 9.0
    FONT_SIZE_LABEL_SMALL = 8.0
    FONT_SIZE_TOOLTIP = 8.5
    FONT_SIZE_CENTER = 9.5

    # Geometry Defaults
    RADIUS_SMALL = 140.0
    RADIUS_NORMAL = 180.0
    RADIUS_LARGE = 230.0
    INNER_RADIUS_DEFAULT = 55.0

    # Animation Durations (ms)
    ANIM_SPEED_FAST = 150
    ANIM_SPEED_NORMAL = 240
    ANIM_SPEED_SLOW = 380

    @classmethod
    def get_font(cls, size: float = 9.0, bold: bool = False) -> QFont:
        """Helper to create standard Outfit typography font."""
        font = QFont(cls.FONT_FAMILY, int(size))
        font.setBold(bold)
        return font
