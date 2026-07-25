from app.models.base_action import BaseAction
from app.models.actions.shortcut_action import ShortcutAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.window_control")


class WindowControlAction(BaseAction):
    """Executes OS window management commands (Minimize, Maximize, Snap Left/Right, Close)."""

    def execute(self) -> bool:
        command = self.params.get("command", "minimize").lower()
        logger.info(f"Executing WindowControlAction '{command}'")

        if command == "minimize":
            return ShortcutAction("w_min", "min", params={"keys": "cmd+down"}).execute()
        elif command == "maximize":
            return ShortcutAction("w_max", "max", params={"keys": "cmd+up"}).execute()
        elif command == "snap_left":
            return ShortcutAction("w_left", "left", params={"keys": "cmd+left"}).execute()
        elif command == "snap_right":
            return ShortcutAction("w_right", "right", params={"keys": "cmd+right"}).execute()
        elif command == "close":
            return ShortcutAction("w_close", "close", params={"keys": "alt+f4"}).execute()
        return False
