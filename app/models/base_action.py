"""
Abstract Base Action model contract.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAction(ABC):
    """Abstract base class for all executable actions in Orbit."""

    def __init__(self, action_id: str, label: str, icon: str = "", params: Dict[str, Any] | None = None) -> None:
        self.action_id = action_id
        self.label = label
        self.icon = icon
        self.params = params or {}

    @abstractmethod
    def execute(self) -> bool:
        """Executes the action logic. Returns True on success."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serializes action definition to dictionary."""
        return {
            "type": self.__class__.__name__,
            "id": self.action_id,
            "label": self.label,
            "icon": self.icon,
            "params": self.params
        }
