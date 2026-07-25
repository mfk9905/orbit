"""
Application Launcher Plugin.
"""

from typing import List
from app.plugins.base_plugin import BasePlugin
from app.models.base_action import BaseAction
from app.models.actions import AppAction


class LauncherPlugin(BasePlugin):
    """Provides application launching actions."""

    def __init__(self) -> None:
        super().__init__("orbit.plugin.launcher", "Launcher Plugin", "1.0.0")

    def initialize(self) -> bool:
        return True

    def register_actions(self) -> List[BaseAction]:
        return [
            AppAction("launcher_terminal", "Open Terminal", icon="terminal", params={"command": "wt || cmd.exe /c start cmd || konsole || gnome-terminal || xterm"}),
            AppAction("launcher_calc", "Calculator", icon="calc", params={"command": "calc.exe || calc || kcalc || gnome-calculator"}),
        ]

    def shutdown(self) -> None:
        pass
