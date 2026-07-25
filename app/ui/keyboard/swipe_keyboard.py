import sys
from typing import List, Tuple
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QColor, QPen, QMouseEvent, QPolygonF
from PySide6.QtCore import Qt, QPoint, QRectF, Signal
from pynput.keyboard import Controller, Key

from app.core.keyboard_engine import KeyboardEngine
from app.core.logging.logger import get_logger

logger = get_logger("orbit.swipe_keyboard")

class SwipeKeyboardWindow(QWidget):
    # Signal emitted when keyboard is closed
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Dimensions
        self.kb_width = 850
        self.kb_height = 350
        self.resize(self.kb_width, self.kb_height)
        
        # Position at bottom of primary screen
        screen_geo = QApplication.primaryScreen().geometry()
        x = (screen_geo.width() - self.kb_width) // 2
        y = screen_geo.height() - self.kb_height - 50
        self.move(x, y)

        self.engine = KeyboardEngine()
        self.keyboard_controller = Controller()

        # Keyboard layout (QWERTY Turkish + Modifiers)
        self.layout = [
            ["q", "w", "e", "r", "t", "y", "u", "ı", "o", "p", "ğ", "ü"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ş", "i"],
            ["z", "x", "c", "v", "b", "n", "m", "ö", "ç", "SPACE"],
            ["CTRL", "SHIFT", "ALT", "ENTER", "BACKSPACE"]
        ]
        
        self.key_rects = {}  # { "a": QRectF, ... }
        self._calculate_key_rects()

        # Swipe state
        self.is_swiping = False
        self.swipe_path: List[QPoint] = []
        self.current_sequence: List[str] = []
        self.active_modifiers = set()

        # UI Colors
        self.bg_color = QColor(30, 30, 30, 220)
        self.key_bg_color = QColor(60, 60, 60, 255)
        self.text_color = QColor(255, 255, 255, 255)
        self.path_color = QColor(46, 213, 115, 180)  # Orbit accent green

    def _calculate_key_rects(self):
        padding = 10
        row_height = (self.kb_height - padding * 5) / 4
        
        y_offset = padding
        for row in self.layout:
            key_width = (self.kb_width - padding * (len(row) + 1)) / len(row)
            x_offset = padding
            for key in row:
                rect = QRectF(x_offset, y_offset, key_width, row_height)
                self.key_rects[key] = rect
                x_offset += key_width + padding
            y_offset += row_height + padding

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

        # Draw keys
        painter.setPen(self.text_color)
        font = painter.font()
        font.setPointSize(16)
        painter.setFont(font)

        for key, rect in self.key_rects.items():
            if key in self.active_modifiers:
                painter.setBrush(QColor(46, 213, 115, 200)) # Active modifier color
            else:
                painter.setBrush(self.key_bg_color)
                
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 8, 8)
            
            painter.setPen(self.text_color)
            display_text = " " if key == "SPACE" else key.upper()
            painter.drawText(rect, Qt.AlignCenter, display_text)

        # Draw swipe path
        if len(self.swipe_path) > 1:
            pen = QPen(self.path_color)
            pen.setWidth(6)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            
            # Create a polygon for polyline drawing
            poly = QPolygonF()
            for p in self.swipe_path:
                poly.append(p.toPointF())
            painter.drawPolyline(poly)

    def _get_key_at_pos(self, pos: QPoint) -> str:
        for key, rect in self.key_rects.items():
            if rect.contains(pos):
                return key
        return None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_swiping = True
            self.swipe_path = [event.pos()]
            self.current_sequence = []
            
            key = self._get_key_at_pos(event.pos())
            if key:
                self.current_sequence.append(key)
            
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_swiping:
            self.swipe_path.append(event.pos())
            
            key = self._get_key_at_pos(event.pos())
            if key:
                if not self.current_sequence or self.current_sequence[-1] != key:
                    self.current_sequence.append(key)
            
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.is_swiping:
            self.is_swiping = False
            
            if self.current_sequence:
                # Modifiers toggle logic
                first_key = self.current_sequence[0]
                if len(self.current_sequence) == 1 and first_key in ["CTRL", "SHIFT", "ALT"]:
                    if first_key in self.active_modifiers:
                        self.active_modifiers.remove(first_key)
                    else:
                        self.active_modifiers.add(first_key)
                elif len(self.current_sequence) == 1:
                    # Single key press
                    self._type_single_key(first_key)
                else:
                    # Swipe prediction
                    word = self.engine.predict_word(self.current_sequence)
                    if word:
                        self._type_text(word + " ")
            
            self.swipe_path.clear()
            self.current_sequence.clear()
            self.update()

    def _type_single_key(self, key_str: str):
        try:
            # Map special keys
            key_map = {
                "SPACE": Key.space,
                "ENTER": Key.enter,
                "BACKSPACE": Key.backspace
            }
            mod_map = {
                "CTRL": Key.ctrl,
                "SHIFT": Key.shift,
                "ALT": Key.alt
            }
            
            pressed_mods = []
            for mod in self.active_modifiers:
                mod_key = mod_map[mod]
                self.keyboard_controller.press(mod_key)
                pressed_mods.append(mod_key)
                
            k = key_map.get(key_str, key_str)
            if isinstance(k, str) and "SHIFT" in self.active_modifiers:
                k = k.upper()
                
            self.keyboard_controller.press(k)
            self.keyboard_controller.release(k)
            
            for mod_key in reversed(pressed_mods):
                self.keyboard_controller.release(mod_key)
                
            self.active_modifiers.clear() # Reset modifiers after use
            logger.info(f"SwipeKeyboard single tapped: '{key_str}' with modifiers")
            self.update()
        except Exception as e:
            logger.error(f"Failed to type single key from SwipeKeyboard: {e}")

    def _type_text(self, text: str):
        try:
            self.keyboard_controller.type(text)
            logger.info(f"SwipeKeyboard typed: '{text}'")
            self.active_modifiers.clear()
            self.update()
        except Exception as e:
            logger.error(f"Failed to type text from SwipeKeyboard: {e}")

    def keyPressEvent(self, event):
        # Allow closing with ESC
        if event.key() == Qt.Key_Escape:
            self.close()
            self.closed.emit()

    def show_keyboard(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_keyboard(self):
        self.hide()
        self.closed.emit()
