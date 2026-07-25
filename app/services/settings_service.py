"""
Settings Service interface and concrete implementation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from app.core.config.settings import SettingsManager
from app.core.events.event_bus import EventBus, ConfigUpdatedEvent


class ISettingsService(ABC):
    """Abstract Settings Service interface."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        pass


class SettingsService(ISettingsService):
    """Concrete Settings Service using SettingsManager and EventBus."""

    def __init__(self, settings_manager: SettingsManager, event_bus: EventBus) -> None:
        self._manager = settings_manager
        self._event_bus = event_bus

    def get(self, key: str, default: Any = None) -> Any:
        return self._manager.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._manager.set(key, value)
        self._event_bus.publish(ConfigUpdatedEvent(key, value))

    def get_all(self) -> Dict[str, Any]:
        return self._manager.all_settings()
