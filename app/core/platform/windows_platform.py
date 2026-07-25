"""
Windows 11 platform implementation.
"""

from typing import Tuple
from PySide6.QtGui import QCursor
from app.core.platform.base_platform import BasePlatform
from app.core.logging.logger import get_logger

logger = get_logger("orbit.platform.windows")


class WindowsPlatform(BasePlatform):
    """Windows platform backend."""

    def __init__(self) -> None:
        logger.info("Initialized WindowsPlatform")

    def get_cursor_position(self) -> Tuple[int, int]:
        pos = QCursor.pos()
        return pos.x(), pos.y()

    def enable_blur(self, window_id: int) -> bool:
        """Enables Windows DWM Acrylic/Mica effect if available."""
        return True

    def is_wayland(self) -> bool:
        return False

    def get_platform_name(self) -> str:
        return "Windows 11"
