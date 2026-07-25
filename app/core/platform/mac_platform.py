"""
macOS platform implementation stub for future support.
"""

from typing import Tuple
from PySide6.QtGui import QCursor
from app.core.platform.base_platform import BasePlatform


class MacPlatform(BasePlatform):
    """macOS platform backend stub."""

    def get_cursor_position(self) -> Tuple[int, int]:
        pos = QCursor.pos()
        return pos.x(), pos.y()

    def enable_blur(self, window_id: int) -> bool:
        return True

    def is_wayland(self) -> bool:
        return False

    def get_platform_name(self) -> str:
        return "macOS"

    def set_autostart(self, enabled: bool) -> bool:
        return True

    def is_autostart_enabled(self) -> bool:
        return False
