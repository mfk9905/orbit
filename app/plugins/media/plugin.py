"""
Media Control Plugin.
"""

from typing import List
from app.plugins.base_plugin import BasePlugin
from app.models.base_action import BaseAction
from app.models.actions import ShortcutAction


class MediaPlugin(BasePlugin):
    """Provides system media playback control actions."""

    def __init__(self) -> None:
        super().__init__("orbit.plugin.media", "Media Control Plugin", "1.0.0")

    def initialize(self) -> bool:
        return True

    def register_actions(self) -> List[BaseAction]:
        return [
            ShortcutAction("media_play_pause", "Play/Pause", icon="play", params={"keys": "media_play_pause"}),
            ShortcutAction("media_next", "Next Track", icon="next", params={"keys": "media_next"}),
            ShortcutAction("media_prev", "Previous Track", icon="prev", params={"keys": "media_previous"}),
        ]

    def shutdown(self) -> None:
        pass
