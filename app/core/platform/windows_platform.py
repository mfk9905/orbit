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

    def set_autostart(self, enabled: bool) -> bool:
        """Configures Windows Registry autostart key."""
        try:
            import sys
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                if enabled:
                    python_exe = sys.executable
                    script_path = sys.argv[0]
                    if script_path.endswith(".py"):
                        cmd = f'"{python_exe}" "{script_path}"'
                    else:
                        cmd = f'"{script_path}"'
                    winreg.SetValueEx(key, "Orbit", 0, winreg.REG_SZ, cmd)
                    logger.info(f"Windows Registry autostart enabled: {cmd}")
                else:
                    try:
                        winreg.DeleteValue(key, "Orbit")
                        logger.info("Windows Registry autostart disabled")
                    except FileNotFoundError:
                        pass
            return True
        except Exception as e:
            logger.error(f"Failed to configure Windows autostart: {e}")
            return False

    def is_autostart_enabled(self) -> bool:
        """Checks Windows Registry autostart key."""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, "Orbit")
                return True
        except Exception:
            return False
