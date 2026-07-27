import ctypes
from app.models.base_action import BaseAction
from app.models.actions.shortcut_action import ShortcutAction
from app.models.actions.app_action import AppAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.system_tool")


class SystemToolAction(BaseAction):
    """Executes Windows system productivity tools (Snipping Tool, Color Picker, Lock, Explorer, etc.)."""

    def execute(self) -> bool:
        command = self.params.get("command", "snipping_tool").lower()
        logger.info(f"Executing SystemToolAction '{command}'")

        if command in ("snipping_tool", "screenshot", "snip"):
            return ShortcutAction("act", "Snip", params={"keys": "cmd+shift+s"}).execute()
        elif command in ("color_picker", "eyedropper"):
            return ShortcutAction("act", "ColorPicker", params={"keys": "cmd+shift+c"}).execute()
        elif command in ("task_manager", "taskmgr"):
            return ShortcutAction("act", "TaskMgr", params={"keys": "ctrl+shift+esc"}).execute()
        elif command in ("file_explorer", "explorer"):
            return ShortcutAction("act", "Explorer", params={"keys": "cmd+e"}).execute()
        elif command in ("lock_screen", "lock"):
            try:
                if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "user32"):
                    ctypes.windll.user32.LockWorkStation()
                    return True
            except Exception:
                pass
            return ShortcutAction("act", "Lock", params={"keys": "cmd+l"}).execute()
        elif command in ("show_desktop", "desktop"):
            return ShortcutAction("act", "Desktop", params={"keys": "cmd+d"}).execute()
        elif command in ("emoji_panel", "emoji"):
            return ShortcutAction("act", "Emoji", params={"keys": "cmd+."}).execute()
        elif command in ("calculator", "calc"):
            return AppAction("act", "Calc", params={"command": "calc.exe || calc"}).execute()
        elif command in ("ping", "ping_tool", "ping_dialog"):
            try:
                from PySide6.QtWidgets import QApplication
                from app.ui.dialogs.ping_dialog import PingDialog

                initial_host = self.params.get("host") or self.params.get("target") or "8.8.8.8"
                # Keep reference on QApplication if available
                app_inst = QApplication.instance()
                dialog = PingDialog(initial_host=initial_host)
                if app_inst:
                    if not hasattr(app_inst, "_active_dialogs"):
                        app_inst._active_dialogs = []
                    app_inst._active_dialogs.append(dialog)
                    dialog.finished.connect(lambda: app_inst._active_dialogs.remove(dialog) if dialog in getattr(app_inst, "_active_dialogs", []) else None)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()
                return True

            except Exception as e:
                logger.error(f"Failed to open PingDialog: {e}", exc_info=True)
                return False
        else:
            logger.error(f"Unknown SystemToolAction command: '{command}'")
            return False

