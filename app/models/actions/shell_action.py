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

        cmd_lower = command.strip().lower()
        if "ping" in cmd_lower and ("-t" in cmd_lower or "-a" in cmd_lower or "cmd.exe" in cmd_lower or cmd_lower.startswith("ping")):
            logger.info(f"ShellAction detected ping command '{command}', delegating to SystemToolAction ping_tool...")
            parts = [p for p in command.split() if not p.startswith("-") and not p.lower().endswith("cmd.exe") and not p.lower().endswith("cmd") and p.lower() != "/k" and p.lower() != "ping"]
            host = parts[-1] if parts else "8.8.8.8"
            from app.models.actions.system_tool_action import SystemToolAction
            return SystemToolAction(self.action_id, self.label, icon=self.icon, params={"command": "ping_tool", "host": host}).execute()



        try:
            subprocess.Popen(command, shell=True)
            logger.info(f"Executed shell command: {command}")
            return True
        except Exception as e:
            logger.error(f"Failed shell command '{command}': {e}")
            return False

