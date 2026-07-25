"""
Base Plugin contract for Orbit extensions.
"""

from abc import ABC, abstractmethod
from typing import List
from app.models.base_action import BaseAction


class BasePlugin(ABC):
    """Abstract interface for Orbit plugins."""

    def __init__(self, plugin_id: str, name: str, version: str = "1.0.0") -> None:
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.is_enabled = True

    @abstractmethod
    def initialize(self) -> bool:
        """Called when plugin is loaded."""
        pass

    @abstractmethod
    def register_actions(self) -> List[BaseAction]:
        """Returns list of actions exposed by this plugin."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up plugin resources on application exit."""
        pass
