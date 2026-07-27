from pynput.keyboard import Controller as KeyboardController, Key
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.media")


class MediaAction(BaseAction):
    """Executes OS media and volume control actions (volume_up, volume_down, mute, play_pause, next, prev)."""

    def execute(self) -> bool:
        command = self.params.get("command", "play_pause").lower()
        logger.info(f"Executing MediaAction '{command}'")

        controller = KeyboardController()
        media_key_map = {
            "volume_up": Key.media_volume_up,
            "volume_down": Key.media_volume_down,
            "volume_mute": Key.media_volume_mute,
            "mute": Key.media_volume_mute,
            "play_pause": Key.media_play_pause,
            "play": Key.media_play_pause,
            "next_track": Key.media_next,
            "next": Key.media_next,
            "prev_track": Key.media_previous,
            "prev": Key.media_previous,
            "previous": Key.media_previous,
        }

        key = media_key_map.get(command)
        if not key:
            logger.error(f"Unknown MediaAction command: '{command}'")
            return False

        try:
            controller.press(key)
            controller.release(key)
            logger.info(f"Successfully triggered media key for '{command}'")
            return True
        except Exception as e:
            logger.error(f"Failed to execute MediaAction '{command}': {e}")
            return False
