"""
Publish-Subscribe Event Bus for decoupled inter-component communication.
"""

from typing import Callable, Dict, List, Any, Type
from app.core.logging.logger import get_logger

logger = get_logger("orbit.event_bus")


class Event:
    """Base Event class."""
    pass


class EventBus:
    """Central event bus for sub-system decoupling."""

    def __init__(self) -> None:
        self._subscribers: Dict[Type[Event], List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: Type[Event], callback: Callable[[Any], None]) -> None:
        """Register a callback for a specific Event class."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: Type[Event], callback: Callable[[Any], None]) -> None:
        """Unregister a callback."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [cb for cb in self._subscribers[event_type] if cb != callback]

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribed listeners."""
        event_type = type(event)
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error handling event {event_type.__name__}: {e}", exc_info=True)


# Domain Events
class RadialMenuTriggerEvent(Event):
    """Fired when hotkey requests radial menu at coordinates."""
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class RadialMenuDismissEvent(Event):
    """Fired when radial menu should close."""
    pass


class ActionExecuteEvent(Event):
    """Fired when an action is selected for execution."""
    def __init__(self, action_id: str, payload: Dict[str, Any]) -> None:
        self.action_id = action_id
        self.payload = payload


class ProfileChangedEvent(Event):
    """Fired when active profile changes."""
    def __init__(self, profile_name: str) -> None:
        self.profile_name = profile_name


class ConfigUpdatedEvent(Event):
    """Fired when settings configuration changes."""
    def __init__(self, key: str, value: Any) -> None:
        self.key = key
        self.value = value
