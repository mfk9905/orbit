"""
Linux platform implementation supporting KDE Plasma (X11 & Wayland).
"""

import os
from typing import Tuple
from PySide6.QtGui import QCursor
from app.core.platform.base_platform import BasePlatform
from app.core.logging.logger import get_logger

logger = get_logger("orbit.platform.linux")


class LinuxPlatform(BasePlatform):
    """Linux platform backend targeting Fedora KDE Plasma."""

    def __init__(self) -> None:
        self._wayland = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        logger.info(f"Initialized LinuxPlatform (Wayland: {self._wayland})")

    def get_cursor_position(self) -> Tuple[int, int]:
        """Gets screen coordinates of mouse cursor using PySide QCursor fallback."""
        pos = QCursor.pos()
        return pos.x(), pos.y()

    def enable_blur(self, window_id: int) -> bool:
        """KDE KWindowSystem blur protocol hint."""
        # On KDE Plasma, Qt translucent window flags + KWindowSystem background blur
        return True

    def is_wayland(self) -> bool:
        return self._wayland

    def get_platform_name(self) -> str:
        return "Linux (KDE Plasma)"
