"""
Shell Execution Plugin.
"""

from typing import List
from app.plugins.base_plugin import BasePlugin
from app.models.base_action import BaseAction
from app.models.actions import ShellAction


class ShellPlugin(BasePlugin):
    """Provides shell command actions."""

    def __init__(self) -> None:
        super().__init__("orbit.plugin.shell", "Shell Command Plugin", "1.0.0")

    def initialize(self) -> bool:
        return True

    def register_actions(self) -> List[BaseAction]:
        return [
            ShellAction("shell_top", "Open System Monitor", icon="activity", params={"command": "taskmgr || htop || top"}),
        ]

    def shutdown(self) -> None:
        pass
