from pynput.keyboard import Controller as KeyboardController, Key
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.shortcut")


class ShortcutAction(BaseAction):
    """Simulates pressing a keyboard key combination."""

    def execute(self) -> bool:
        keys_str = self.params.get("keys", "")
        if not keys_str:
            logger.error(f"ShortcutAction '{self.label}' missing 'keys' parameter.")
            return False

        try:
            controller = KeyboardController()
            # Reset stuck modifier keys prior to shortcut simulation
            for mod in (Key.ctrl, Key.ctrl_l, Key.ctrl_r, Key.alt, Key.alt_l, Key.alt_r, Key.shift, Key.cmd):
                try:
                    controller.release(mod)
                except Exception:
                    pass

            aliases = {
                "plus": "+",
                "minus": "-",
                "equal": "=",
                "cmd": "cmd",
                "win": "cmd"
            }
            key_list = [k.strip().lower() for k in keys_str.split("+") if k.strip()]
            pressed_keys = []
            try:
                for k in key_list:
                    clean_k = aliases.get(k, k)
                    if hasattr(Key, clean_k):
                        pk = getattr(Key, clean_k)
                    else:
                        pk = clean_k
                    controller.press(pk)
                    pressed_keys.append(pk)
                logger.info(f"Simulated shortcut: {keys_str}")
                return True
            finally:
                for pk in reversed(pressed_keys):
                    try:
                        controller.release(pk)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Failed to simulate shortcut '{keys_str}': {e}")
            return False
