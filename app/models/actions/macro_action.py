import time
from app.models.base_action import BaseAction
from app.models.actions.app_action import AppAction
from app.models.actions.shell_action import ShellAction
from app.models.actions.shortcut_action import ShortcutAction
from app.models.actions.text_action import TextAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.macro")


class MacroAction(BaseAction):
    """Executes a multi-step sequence of key combinations, text typing, and delays."""

    def execute(self) -> bool:
        steps = self.params.get("steps", [])
        if not steps:
            logger.error(f"MacroAction '{self.label}' missing 'steps' parameter.")
            return False

        logger.info(f"Executing MacroAction '{self.label}' with {len(steps)} steps...")
        for step in steps:
            step_type = step.get("type", "")
            if step_type == "shortcut":
                ShortcutAction("s", "s", params={"keys": step.get("keys", "")}).execute()
            elif step_type == "text":
                TextAction("t", "t", params={"text": step.get("text", "")}).execute()
            elif step_type == "delay":
                ms = float(step.get("ms", 100))
                time.sleep(ms / 1000.0)
            elif step_type == "app":
                AppAction("a", "a", params={"command": step.get("command", "")}).execute()
            elif step_type == "shell":
                ShellAction("sh", "sh", params={"command": step.get("command", "")}).execute()

        return True
