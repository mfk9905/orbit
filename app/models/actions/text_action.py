from pynput.keyboard import Controller as KeyboardController
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.text")


class TextAction(BaseAction):
    """Types out a text string into the active window."""

    def execute(self) -> bool:
        text = self.params.get("text", "")
        if not text:
            logger.error(f"TextAction '{self.label}' missing 'text' parameter.")
            return False

        try:
            controller = KeyboardController()
            controller.type(text)
            logger.info(f"Typed text string: '{text}'")
            return True
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            return False
