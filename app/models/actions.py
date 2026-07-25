"""
Concrete Action implementations for Orbit V1.
"""

import subprocess
import webbrowser
from typing import Any, Dict, List
from pynput.keyboard import Controller as KeyboardController, Key
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

# Lazy load keyboard window to avoid circular imports / thread issues
_keyboard_window = None

logger = get_logger("orbit.actions")


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


class UrlAction(BaseAction):
    """Opens a web URL in the system's default browser."""

    def execute(self) -> bool:
        url = self.params.get("url", "")
        if not url:
            logger.error(f"UrlAction '{self.label}' missing 'url' parameter.")
            return False

        try:
            webbrowser.open(url)
            logger.info(f"Opened URL: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to open URL '{url}': {e}")
            return False


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


class ShortcutAction(BaseAction):
    """Simulates pressing a keyboard key combination."""

    def execute(self) -> bool:
        keys_str = self.params.get("keys", "")
        if not keys_str:
            logger.error(f"ShortcutAction '{self.label}' missing 'keys' parameter.")
            return False

        try:
            controller = KeyboardController()
            aliases = {
                "plus": "+",
                "minus": "-",
                "equal": "=",
                "cmd": "cmd",
                "win": "cmd"
            }
            key_list = [k.strip().lower() for k in keys_str.split("+") if k.strip()]
            pressed_keys = []
            for k in key_list:
                clean_k = aliases.get(k, k)
                if hasattr(Key, clean_k):
                    pk = getattr(Key, clean_k)
                else:
                    pk = clean_k
                controller.press(pk)
                pressed_keys.append(pk)

            for pk in reversed(pressed_keys):
                controller.release(pk)

            logger.info(f"Simulated shortcut: {keys_str}")
            return True
        except Exception as e:
            logger.error(f"Failed to simulate shortcut '{keys_str}': {e}")
            return False



class TextAction(BaseAction):
    """Types out a text string into the active window."""

    def execute(self) -> bool:
        text = self.params.get("text", "")
        if not text:
            logger.error(f"TextAction '{self.label}' missing 'text' parameter.")
            return False

        try:
            controller = KeyboardController()
            controller.type(text)
            logger.info(f"Typed text string: '{text}'")
            return True
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            return False


class SubRingAction(BaseAction):
    """Action that opens a nested sub-ring radial menu."""

    def __init__(self, action_id: str, label: str, icon: str = "", params: Dict[str, Any] | None = None, items: List[Any] | None = None) -> None:
        super().__init__(action_id, label, icon, params or {})
        self.sub_items = items or []

    def execute(self) -> bool:
        logger.info(f"SubRingAction '{self.label}' triggered ({len(self.sub_items)} sub-items)")
        return True

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["items"] = [item.to_dict() if hasattr(item, "to_dict") else item for item in self.sub_items]
        return d


class ClipboardSubRingAction(SubRingAction):
    """SubRingAction that dynamically populates items from ClipboardService."""

    def __init__(self, action_id: str, label: str, icon: str = "", params: Dict[str, Any] | None = None, items: List[Any] | None = None) -> None:
        super().__init__(action_id, label, icon, params, items)

    @property
    def sub_items(self):
        from app.services.clipboard_service import ClipboardService
        return ClipboardService.get_instance().get_slice_items()

    @sub_items.setter
    def sub_items(self, val):
        pass


class MacroAction(BaseAction):
    """Executes a multi-step sequence of key combinations, text typing, and delays."""

    def execute(self) -> bool:
        import time
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


class WheelAction(BaseAction):
    """Responds to mouse wheel scrolling when hovering over a slice."""

    def execute(self) -> bool:
        # Normal click fallback: execute 'up' step or toggle
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
            # Custom shortcut mapping
            keys = self.params.get("up_keys", "ctrl+up") if delta > 0 else self.params.get("down_keys", "ctrl+down")
            return ShortcutAction("w_sc", "w_sc", params={"keys": keys}).execute()


class WindowControlAction(BaseAction):
    """Executes OS window management commands (Minimize, Maximize, Snap Left/Right, Close)."""

    def execute(self) -> bool:
        command = self.params.get("command", "minimize").lower()
        logger.info(f"Executing WindowControlAction '{command}'")

        if command == "minimize":
            return ShortcutAction("w_min", "min", params={"keys": "cmd+down"}).execute()
        elif command == "maximize":
            return ShortcutAction("w_max", "max", params={"keys": "cmd+up"}).execute()
        elif command == "snap_left":
            return ShortcutAction("w_left", "left", params={"keys": "cmd+left"}).execute()
        elif command == "snap_right":
            return ShortcutAction("w_right", "right", params={"keys": "cmd+right"}).execute()
        elif command == "close":
            return ShortcutAction("w_close", "close", params={"keys": "alt+f4"}).execute()
        return False


class KeyboardAction(BaseAction):
    """Launches Windows On-Screen Keyboard or custom keyboard."""

    def execute(self) -> bool:
        mode = self.params.get("mode", "osk")

        if mode == "osk":
            try:
                subprocess.Popen("osk.exe", shell=True)
                logger.info("Launched Windows On-Screen Keyboard (osk.exe)")
                return True
            except Exception as e:
                logger.error(f"Failed to launch osk.exe: {e}")
                return False
        elif mode == "tabtip":
            try:
                subprocess.Popen("start tabtip.exe", shell=True)
                logger.info("Launched Windows Touch Keyboard (tabtip.exe)")
                return True
            except Exception as e:
                logger.error(f"Failed to launch tabtip.exe: {e}")
                return False
        else:
            global _keyboard_window
            from PySide6.QtWidgets import QApplication
            from app.ui.keyboard.swipe_keyboard import SwipeKeyboardWindow

            app = QApplication.instance()
            if not app:
                logger.error("No QApplication instance found for KeyboardAction.")
                return False

            if _keyboard_window is None:
                _keyboard_window = SwipeKeyboardWindow()
            
            if _keyboard_window.isVisible():
                _keyboard_window.hide_keyboard()
            else:
                _keyboard_window.show_keyboard()

            logger.info("Toggled custom keyboard")
            return True


def action_factory(data: Dict[str, Any]) -> BaseAction:
    """Instantiates concrete BaseAction derived instance from dict definition."""
    action_type = data.get("type", "AppAction")
    action_id = data.get("id", "action_id")
    label = data.get("label", "Action")
    icon = data.get("icon", "")
    params = data.get("params", {})

    if action_type == "SubRingAction":
        from app.models.profile import SliceItem
        raw_items = data.get("items", [])
        sub_items = [SliceItem.from_dict(item_data) for item_data in raw_items]
        return SubRingAction(action_id=action_id, label=label, icon=icon, params=params, items=sub_items)

    if action_type == "ClipboardSubRingAction":
        return ClipboardSubRingAction(action_id=action_id, label=label, icon=icon, params=params)

    mapping = {
        "AppAction": AppAction,
        "UrlAction": UrlAction,
        "ShellAction": ShellAction,
        "ShortcutAction": ShortcutAction,
        "TextAction": TextAction,
        "MacroAction": MacroAction,
        "WheelAction": WheelAction,
        "WindowControlAction": WindowControlAction,
        "KeyboardAction": KeyboardAction,
        "ClipboardSubRingAction": ClipboardSubRingAction,
    }

    cls = mapping.get(action_type, AppAction)
    return cls(action_id=action_id, label=label, icon=icon, params=params)


