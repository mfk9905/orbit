import subprocess
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.shell")


class ShellAction(BaseAction):
    """Executes a shell command."""

    def execute(self) -> bool:
        command = self.params.get("command", "")
        if not command:
            logger.error(f"ShellAction '{self.label}' missing 'command' parameter.")
            return False

        try:
            subprocess.Popen(command, shell=True)
            logger.info(f"Executed shell command: {command}")
            return True
        except Exception as e:
            logger.error(f"Failed shell command '{command}': {e}")
            return False
