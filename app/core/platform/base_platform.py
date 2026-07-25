"""
Abstract base platform contract for Orbit.
"""

from abc import ABC, abstractmethod
from typing import Tuple


class BasePlatform(ABC):
    """Abstract platform interface defining OS-dependent behaviors."""

    @abstractmethod
    def get_cursor_position(self) -> Tuple[int, int]:
        """Returns current mouse cursor screen coordinates (x, y)."""
        pass

    @abstractmethod
    def enable_blur(self, window_id: int) -> bool:
        """Applies window background blur (KDE KWindowSystem / DWM)."""
        pass

    @abstractmethod
    def is_wayland(self) -> bool:
        """Returns True if running under Wayland display server."""
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Returns string identifier of the platform."""
        pass

    @abstractmethod
    def set_autostart(self, enabled: bool) -> bool:
        """Configures OS startup entry."""
        pass

    @abstractmethod
    def is_autostart_enabled(self) -> bool:
        """Returns True if autostart is enabled."""
        pass
