"""
Factory and facade for system platform abstraction.
"""

import sys
from app.core.platform.base_platform import BasePlatform
from app.core.platform.linux_platform import LinuxPlatform
from app.core.platform.windows_platform import WindowsPlatform
from app.core.platform.mac_platform import MacPlatform
from app.core.logging.logger import get_logger

logger = get_logger("orbit.platform.manager")


class PlatformManager:
    """Detects active operating system and provides platform provider instance."""

    @staticmethod
    def create_platform() -> BasePlatform:
        """Instantiate OS-appropriate platform provider."""
        if sys.platform.startswith("linux"):
            return LinuxPlatform()
        elif sys.platform == "win32":
            return WindowsPlatform()
        elif sys.platform == "darwin":
            return MacPlatform()
        else:
            logger.warning(f"Unsupported OS '{sys.platform}'. Falling back to Linux platform implementation.")
            return LinuxPlatform()
