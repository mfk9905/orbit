import time
from typing import Any, Dict
from PySide6.QtGui import QGuiApplication
from pynput.keyboard import Controller, Key
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.clipboard")


class ClipboardAction(BaseAction):
    """Pastes a specific text string from history by setting clipboard and simulating Ctrl+V."""

    def execute(self) -> bool:
        text = self.params.get("text", "")
        if not text:
            logger.error(f"ClipboardAction '{self.label}' missing 'text' parameter.")
            return False

        try:
            # 1. Update clipboard with the target text
            cb = QGuiApplication.clipboard()
            if cb:
                cb.setText(text)
            
            # Brief pause for OS clipboard propagation
            time.sleep(0.04)

            # 2. Simulate Ctrl+V to paste instantly into active application
            keyboard = Controller()
            with keyboard.pressed(Key.ctrl):
                keyboard.press('v')
                keyboard.release('v')

            logger.info(f"ClipboardAction successfully pasted ({len(text)} chars): '{text[:30]}...'")
            return True
        except Exception as e:
            logger.error(f"Failed to paste clipboard text: {e}")
            return False
