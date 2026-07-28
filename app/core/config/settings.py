"""
Configuration loader and settings manager.
"""

import json
from pathlib import Path
from typing import Any, Dict
from app.core.logging.logger import get_logger

logger = get_logger("orbit.config")


DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "dark",
    "accent_color": "#2ED573",
    "opacity": 0.9,
    "animation_speed": 200,  # milliseconds
    "radius": 150,  # pixels
    "hotkey": "<ctrl>+<space>",
    "mouse_hotkey": "button4",
    "language": "en",
    "slices_count": 8,
    "blur_effect": True,
    "autostart": False,
    "enable_corner_hotspot": True,
    "enable_mouse_gestures": False,
    "gesture_drag_threshold": 45.0,
    "gestures": {
        "up": {
            "type": "WindowControlAction",
            "id": "g_up",
            "label": "Büyüt / Ekranı Kapla",
            "icon": "square",
            "params": {"command": "maximize"}
        },
        "down": {
            "type": "WindowControlAction",
            "id": "g_down",
            "label": "Pencereyi Küçült",
            "icon": "minus",
            "params": {"command": "minimize"}
        },
        "left": {
            "type": "WindowControlAction",
            "id": "g_left",
            "label": "Sola Yasla",
            "icon": "arrow-left",
            "params": {"command": "snap_left"}
        },
        "right": {
            "type": "WindowControlAction",
            "id": "g_right",
            "label": "Sağa Yasla",
            "icon": "arrow-right",
            "params": {"command": "snap_right"}
        }
    }
}


class SettingsManager:
    """Manages reading and persisting application settings to JSON."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self._settings: Dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        """Load settings from JSON file, creating default if missing."""
        if not self.config_path.exists():
            self.save()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._settings.update(data)
        except Exception as e:
            logger.error(f"Failed to load settings from {self.config_path}: {e}")

    def save(self) -> None:
        """Persist current settings to JSON file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings to {self.config_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value and persist."""
        self._settings[key] = value
        self.save()

    def all_settings(self) -> Dict[str, Any]:
        """Return a copy of all settings."""
        return dict(self._settings)
