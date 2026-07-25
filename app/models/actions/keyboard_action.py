import subprocess
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

_keyboard_window = None
logger = get_logger("orbit.actions.keyboard")


class KeyboardAction(BaseAction):
    """Launches Windows On-Screen Keyboard or custom keyboard."""

    def execute(self) -> bool:
        mode = self.params.get("mode", "osk")

        if mode == "osk":
            try:
                subprocess.Popen("osk.exe", shell=True)
                logger.info("Launched Windows On-Screen Keyboard (osk.exe)")
                return True
            except Exception as e:
                logger.error(f"Failed to launch osk.exe: {e}")
                return False
        elif mode == "tabtip":
            try:
                subprocess.Popen("start tabtip.exe", shell=True)
                logger.info("Launched Windows Touch Keyboard (tabtip.exe)")
                return True
            except Exception as e:
                logger.error(f"Failed to launch tabtip.exe: {e}")
                return False
        else:
            global _keyboard_window
            from PySide6.QtWidgets import QApplication
            from app.ui.keyboard.swipe_keyboard import SwipeKeyboardWindow

            app = QApplication.instance()
            if not app:
                logger.error("No QApplication instance found for KeyboardAction.")
                return False

            if _keyboard_window is None:
                _keyboard_window = SwipeKeyboardWindow()
            
            if _keyboard_window.isVisible():
                _keyboard_window.hide_keyboard()
            else:
                _keyboard_window.show_keyboard()

            logger.info("Toggled custom keyboard")
            return True
