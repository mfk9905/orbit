"""
Interactive Hotkey Recorder Dialog for Orbit (Türkçe).
Captures user keyboard shortcuts and mouse button presses with quick presets.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QDialogButtonBox, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QMouseEvent
from pynput import keyboard, mouse
from typing import Set


class HotkeyRecorderDialog(QDialog):
    """Modal dialog to capture custom shortcut keys or mouse buttons with quick presets."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Kısayol Tuşu Seçici")
        self.setFixedSize(460, 280)

        self.recorded_shortcut: str = ""
        self._pressed_keys: Set[str] = set()

        self._init_ui()

        # pynput listeners for live recording
        self._key_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._mouse_listener = mouse.Listener(on_click=self._on_click)

        self._key_listener.start()
        self._mouse_listener.start()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        info_lbl = QLabel("Klavyenizden bir tuşa basınız veya aşağıdaki hazır fare/klavye tuşlarından birini seçiniz:")
        info_lbl.setWordWrap(True)
        info_lbl.setAlignment(Qt.AlignCenter)

        self.lbl_shortcut_display = QLabel("Tuş Bekleniyor...")
        self.lbl_shortcut_display.setFont(QFont("Outfit", 13, QFont.Bold))
        self.lbl_shortcut_display.setAlignment(Qt.AlignCenter)
        self.lbl_shortcut_display.setStyleSheet("color: #2ED573; background-color: #2a2e32; padding: 12px; border-radius: 6px;")

        layout.addWidget(info_lbl)
        layout.addWidget(self.lbl_shortcut_display)

        # Quick Presets Group Box
        preset_group = QGroupBox("Hazır Popüler Seçenekler")
        preset_layout = QHBoxLayout(preset_group)

        btn_mouse4 = QPushButton("Fare Yan Tuş 4 (Geri)")
        btn_mouse4.clicked.connect(lambda: self._set_preset("button4", "Fare Yan Tuş 4 (Geri)"))

        btn_mouse5 = QPushButton("Fare Yan Tuş 5 (İleri)")
        btn_mouse5.clicked.connect(lambda: self._set_preset("button5", "Fare Yan Tuş 5 (İleri)"))

        btn_ctrl_space = QPushButton("Ctrl + Space")
        btn_ctrl_space.clicked.connect(lambda: self._set_preset("ctrl+space", "CTRL + SPACE"))

        preset_layout.addWidget(btn_mouse4)
        preset_layout.addWidget(btn_mouse5)
        preset_layout.addWidget(btn_ctrl_space)
        layout.addWidget(preset_group)

        # Dialog Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Tamam")
        button_box.button(QDialogButtonBox.Cancel).setText("İptal")

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def _set_preset(self, shortcut: str, display_text: str) -> None:
        """Sets shortcut from quick preset button."""
        self.recorded_shortcut = shortcut
        self.lbl_shortcut_display.setText(display_text.upper())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Intercept Qt mouse press events for side mouse buttons."""
        button = event.button()
        if button in (Qt.BackButton, Qt.XButton1, Qt.ExtraButton1):
            self._set_preset("button4", "Fare Yan Tuş 4 (Geri)")
        elif button in (Qt.ForwardButton, Qt.XButton2, Qt.ExtraButton2):
            self._set_preset("button5", "Fare Yan Tuş 5 (İleri)")
        super().mousePressEvent(event)

    def _normalize(self, key) -> str:
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
            return name
        elif hasattr(key, 'char') and key.char:
            return key.char.lower()
        return str(key).lower().replace("key.", "")

    def _on_press(self, key) -> None:
        k = self._normalize(key)
        self._pressed_keys.add(k)

        order = ["ctrl", "super", "alt", "shift"]
        combo = [p for p in order if p in self._pressed_keys]
        combo.extend([p for p in self._pressed_keys if p not in order])

        self.recorded_shortcut = "+".join(combo)
        self.lbl_shortcut_display.setText(self.recorded_shortcut.upper().replace("+", " + "))

    def _on_release(self, key) -> None:
        pass

    def _on_click(self, x: float, y: float, button: mouse.Button, pressed: bool) -> None:
        if pressed and button in (mouse.Button.x1, mouse.Button.x2):
            b_name = "button4" if button == mouse.Button.x1 else "button5"
            display_name = "Fare Yan Tuş 4 (Geri)" if button == mouse.Button.x1 else "Fare Yan Tuş 5 (İleri)"
            self.recorded_shortcut = b_name
            self.lbl_shortcut_display.setText(display_name.upper())

    def closeEvent(self, event) -> None:
        self._key_listener.stop()
        self._mouse_listener.stop()
        super().closeEvent(event)

    def accept(self) -> None:
        self._key_listener.stop()
        self._mouse_listener.stop()
        super().accept()

    def reject(self) -> None:
        self._key_listener.stop()
        self._mouse_listener.stop()
        super().reject()
