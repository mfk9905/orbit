"""
Action Service responsible for dispatching and executing BaseAction instances.
"""

from app.models.base_action import BaseAction
from app.core.events.event_bus import EventBus, ActionExecuteEvent
from app.core.logging.logger import get_logger

logger = get_logger("orbit.services.action")


class ActionService:
    """Dispatches and executes actions."""

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    def execute(self, action: BaseAction) -> bool:
        """Executes action and broadcasts event."""
        logger.info(f"Executing action '{action.label}' (ID: {action.action_id})")
        success = action.execute()
        self.event_bus.publish(ActionExecuteEvent(action.action_id, {"success": success, "label": action.label}))
        return success
