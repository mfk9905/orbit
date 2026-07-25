import subprocess
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.app")


class AppAction(BaseAction):
    """Launches a desktop application executable."""

    def execute(self) -> bool:
        cmd = self.params.get("command", "")
        if not cmd:
            logger.error(f"AppAction '{self.label}' missing 'command' parameter.")
            return False

        try:
            subprocess.Popen(cmd, shell=True)
            logger.info(f"Launched application: {cmd}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch application '{cmd}': {e}")
            return False
