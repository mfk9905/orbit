from pynput.keyboard import Controller as KeyboardController, Key
from app.models.base_action import BaseAction
from app.models.actions.shortcut_action import ShortcutAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.wheel")


class WheelAction(BaseAction):
    """Responds to mouse wheel scrolling when hovering over a slice."""

    def execute(self) -> bool:
        return self.execute_wheel(1)

    def execute_wheel(self, delta: int) -> bool:
        """delta > 0 for scroll UP, delta < 0 for scroll DOWN."""
        mode = self.params.get("mode", "shortcut")
        logger.info(f"WheelAction '{self.label}' scrolled {'UP' if delta > 0 else 'DOWN'} (mode={mode})")

        if mode == "volume":
            key_name = "media_volume_up" if delta > 0 else "media_volume_down"
            try:
                controller = KeyboardController()
                key_obj = getattr(Key, key_name)
                controller.press(key_obj)
                controller.release(key_obj)
                return True
            except Exception as e:
                logger.error(f"Volume wheel adjustment failed: {e}")
                return False
        elif mode == "zoom":
            keys = "ctrl+plus" if delta > 0 else "ctrl+minus"
            return ShortcutAction("z", "z", params={"keys": keys}).execute()
        else:
            keys = self.params.get("up_keys", "ctrl+up") if delta > 0 else self.params.get("down_keys", "ctrl+down")
            return ShortcutAction("w_sc", "w_sc", params={"keys": keys}).execute()
