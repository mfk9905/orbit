"""
Global hotkey listener module using pynput.
Hooks user-defined keyboard shortcuts (e.g. Ctrl+Space, Alt+R) and mouse side buttons (Button 4 / Button 5).
Supports optional hold duration threshold.
"""

import time
import threading
from typing import Callable, Optional, Set
from pynput import keyboard, mouse
from PySide6.QtCore import QObject, Signal
from app.core.logging.logger import get_logger

logger = get_logger("orbit.hooks.hotkey")


class HotkeySignalBridge(QObject):
    """Qt Signal bridge to safely marshal callbacks from pynput threads to Qt main UI thread."""
    menu_triggered = Signal(int, int)
    menu_released = Signal(float)  # Emits duration in seconds
    cursor_moved = Signal(int, int)
    gesture_detected = Signal(str)  # Emits "up", "down", "left", or "right"


class HotkeyManager:
    """Listens for global system input events and emits signals on user hotkey matches."""

    def __init__(
        self,
        primary_hotkey: str = "ctrl+space",
        secondary_hotkey: str = "button4",
        enable_hold_duration: bool = False,
        hold_duration_seconds: float = 1.0,
        enable_corner_hotspot: bool = False,
        enable_mouse_gestures: bool = True,
        gesture_drag_threshold: float = 45.0
    ) -> None:
        self.signals = HotkeySignalBridge()
        self.primary_hotkey = primary_hotkey.lower().strip()
        self.secondary_hotkey = secondary_hotkey.lower().strip()
        self.enable_hold_duration = enable_hold_duration
        self.hold_duration_seconds = hold_duration_seconds
        self.enable_corner_hotspot = enable_corner_hotspot
        self.enable_mouse_gestures = enable_mouse_gestures
        self.gesture_drag_threshold = gesture_drag_threshold

        self._last_corner_trigger: float = 0.0
        self._drag_start_pos = (0.0, 0.0)
        self._gesture_detected_direction: Optional[str] = None

        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None

        self._currently_pressed_keys: Set[str] = set()
        self._currently_pressed_mouse: Set[str] = set()

        self._is_active = False
        self._press_timestamp: float = 0.0

        self._hold_timer_thread: Optional[threading.Thread] = None
        self._cancel_hold_timer = False

    def set_hotkeys(self, primary: str, secondary: str = "") -> None:
        """Dynamically update listening hotkey combinations."""
        self.primary_hotkey = primary.lower().strip()
        self.secondary_hotkey = secondary.lower().strip()
        logger.info(f"Hotkeys updated -> Primary: '{self.primary_hotkey}', Secondary: '{self.secondary_hotkey}'")

    def set_corner_hotspot(self, enabled: bool) -> None:
        """Dynamically enable or disable screen corner hotspot activation."""
        self.enable_corner_hotspot = enabled
        logger.info(f"Screen corner hotspot updated -> Enabled: {enabled}")

    def set_hold_options(self, enabled: bool, duration_seconds: float) -> None:
        """Dynamically update hold duration trigger options."""
        self.enable_hold_duration = enabled
        self.hold_duration_seconds = duration_seconds
        logger.info(f"Hold options updated -> Enabled: {enabled}, Duration: {duration_seconds}s")

    def set_gesture_options(self, enabled: bool, threshold: float = 45.0) -> None:
        """Dynamically update mouse gesture swipe options."""
        self.enable_mouse_gestures = enabled
        self.gesture_drag_threshold = threshold
        logger.info(f"Mouse gesture options updated -> Enabled: {enabled}, Threshold: {threshold}px")

    def start(self) -> None:
        """Start background input listeners."""
        try:
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._keyboard_listener.daemon = True
            self._keyboard_listener.start()

            self._mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_move=self._on_mouse_move
            )
            self._mouse_listener.daemon = True
            self._mouse_listener.start()

            logger.info(
                f"Global input listeners started (Primary: '{self.primary_hotkey}', "
                f"Secondary: '{self.secondary_hotkey}', Hold: {self.enable_hold_duration}@{self.hold_duration_seconds}s)."
            )
        except Exception as e:
            logger.error(f"Failed to start global input listener: {e}")

    def stop(self) -> None:
        """Stop input listeners."""
        self._cancel_hold_timer = True
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()

    def _normalize_key_name(self, key) -> str:
        """Converts pynput Key or KeyCode to standardized string name."""
        if isinstance(key, keyboard.Key):
            name = key.name
            if name.startswith("ctrl"):
                return "ctrl"
            if name.startswith("alt"):
                return "alt"
            if name.startswith("shift"):
                return "shift"
            if name.startswith("cmd") or name.startswith("super"):
                return "super"
            if name == "space":
                return "space"
            return name
        elif hasattr(key, 'char') and key.char:
            return key.char.lower()
        elif hasattr(key, 'vk') and key.vk:
            return f"vk_{key.vk}"
        return str(key).lower().replace("key.", "")

    def _matches_shortcut(self, target_shortcut: str) -> bool:
        """Checks if currently pressed keys match target shortcut string (e.g. 'ctrl+space' or 'ctrl+button3')."""
        if not target_shortcut:
            return False

        parts = set(p.strip().lower() for p in target_shortcut.split("+"))
        mouse_parts = {p for p in parts if p in ("button3", "button4", "button5", "right", "middle")}
        key_parts = parts - mouse_parts

        if mouse_parts:
            if not mouse_parts.issubset(self._currently_pressed_mouse):
                return False

        if key_parts:
            if not key_parts.issubset(self._currently_pressed_keys):
                return False

        return True

    def _on_key_press(self, key) -> None:
        k_name = self._normalize_key_name(key)
        self._currently_pressed_keys.add(k_name)

        if self._matches_shortcut(self.primary_hotkey) or self._matches_shortcut(self.secondary_hotkey):
            self._trigger_press()

    def _on_key_release(self, key) -> None:
        k_name = self._normalize_key_name(key)
        self._currently_pressed_keys.discard(k_name)
        self._trigger_release()

    def _identify_mouse_button(self, button) -> str:
        """Robustly identifies mouse button names including middle button."""
        if button == mouse.Button.x1:
            return "button4"
        if button == mouse.Button.x2:
            return "button5"
        if button == mouse.Button.middle:
            return "button3"
        if button == mouse.Button.right:
            return "right"

        btn_str = str(button).lower()
        if "middle" in btn_str or "button3" in btn_str:
            return "button3"
        if "right" in btn_str:
            return "right"
        if "x1" in btn_str or "button4" in btn_str or "button(8)" in btn_str:
            return "button4"
        if "x2" in btn_str or "button5" in btn_str or "button(9)" in btn_str:
            return "button5"
        return ""

    def _on_mouse_click(self, x: float, y: float, button: mouse.Button, pressed: bool) -> None:
        b_name = self._identify_mouse_button(button)
        if b_name:
            if pressed:
                self._currently_pressed_mouse.add(b_name)
                if self._matches_shortcut(self.primary_hotkey) or self._matches_shortcut(self.secondary_hotkey):
                    self._trigger_press()
            else:
                self._currently_pressed_mouse.discard(b_name)
                self._trigger_release()

    def _trigger_press(self) -> None:
        """Handles initial hotkey press, applying optional hold duration timer."""
        if self._is_active:
            return

        if self.enable_hold_duration and self.hold_duration_seconds > 0.05:
            self._cancel_hold_timer = False
            self._hold_timer_thread = threading.Thread(target=self._wait_hold_duration)
            self._hold_timer_thread.daemon = True
            self._hold_timer_thread.start()
        else:
            self._activate_menu()

    def _wait_hold_duration(self) -> None:
        """Waits for hold duration before firing menu_triggered."""
        start = time.time()
        while time.time() - start < self.hold_duration_seconds:
            if self._cancel_hold_timer or not (
                self._matches_shortcut(self.primary_hotkey) or self._matches_shortcut(self.secondary_hotkey)
            ):
                return
            time.sleep(0.04)

        if not self._cancel_hold_timer and (
            self._matches_shortcut(self.primary_hotkey) or self._matches_shortcut(self.secondary_hotkey)
        ):
            self._activate_menu()

    def _activate_menu(self) -> None:
        if not self._is_active:
            self._is_active = True
            self._press_timestamp = time.time()
            m_controller = mouse.Controller()
            cur_x, cur_y = m_controller.position
            self._drag_start_pos = (float(cur_x), float(cur_y))
            self._gesture_detected_direction = None
            logger.info(f"Hotkey triggered globally at ({cur_x}, {cur_y})")
            self.signals.menu_triggered.emit(int(cur_x), int(cur_y))

    def _trigger_release(self) -> None:
        self._cancel_hold_timer = True

        if self._is_active:
            if not self._matches_shortcut(self.primary_hotkey) and not self._matches_shortcut(self.secondary_hotkey):
                self._is_active = False
                duration = time.time() - self._press_timestamp
                # If a gesture swipe was triggered during drag, skip menu selection
                if self._gesture_detected_direction:
                    logger.info(f"Trigger released after gesture swipe '{self._gesture_detected_direction.upper()}'")
                    self._gesture_detected_direction = None
                else:
                    self.signals.menu_released.emit(duration)

    def reset_active_state(self) -> None:
        """Resets active listening state when radial menu is dismissed or closed."""
        self._is_active = False
        self._gesture_detected_direction = None
        self._last_dismiss_timestamp = time.time()
        self._currently_pressed_keys.clear()
        self._currently_pressed_mouse.clear()

    def _on_mouse_move(self, x: float, y: float) -> None:
        if self.enable_corner_hotspot and not self._is_active:
            now = time.time()
            last_dismiss = getattr(self, "_last_dismiss_timestamp", 0.0)
            if (x <= 30 and y <= 30) and (now - self._last_corner_trigger > 1.2) and (now - last_dismiss > 0.4):
                self._last_corner_trigger = now
                logger.info(f"Screen Corner Hotspot triggered at ({x}, {y})")
                self._activate_menu()

        if self._is_active:
            # Check for Mouse Swipe Gestures (Only when a key or mouse button is actually held down)
            is_holding = bool(self._currently_pressed_keys or self._currently_pressed_mouse)
            if self.enable_mouse_gestures and is_holding and not self._gesture_detected_direction:
                import math
                dx = x - self._drag_start_pos[0]
                dy = y - self._drag_start_pos[1]
                dist = math.hypot(dx, dy)
                if dist >= self.gesture_drag_threshold:
                    if abs(dx) > abs(dy):
                        direction = "right" if dx > 0 else "left"
                    else:
                        direction = "down" if dy > 0 else "up"
                    self._gesture_detected_direction = direction
                    logger.info(f"Mouse gesture swipe detected: {direction.upper()} (dist: {dist:.1f}px)")
                    self.signals.gesture_detected.emit(direction)

            self.signals.cursor_moved.emit(int(x), int(y))

