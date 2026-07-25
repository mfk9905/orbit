from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QColor, QPalette, QGuiApplication, QMouseEvent
from app.core.logging.logger import get_logger

logger = get_logger("orbit.ui.overlay")


class OverlayWindow(QWidget):
    """Transparent desktop overlay window."""

    dismiss_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._init_window_flags()

    def _init_window_flags(self) -> None:
        """Apply Qt window flags for borderless, transparent, topmost display."""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Window |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0, 0))
        self.setPalette(palette)

    def show_at_screen(self) -> None:
        """Pulls geometry to cover virtual screen bounding rect across all monitors."""
        screens = QGuiApplication.screens()
        if screens:
            # Union of all screen geometries (multi-monitor setup)
            vg = screens[0].virtualGeometry()
            for s in screens[1:]:
                vg = vg.united(s.virtualGeometry())
            self.setGeometry(vg)
        else:
            self.showMaximized()
        self.show()
        self.raise_()
        self.activateWindow()

    def changeEvent(self, event: QEvent) -> None:
        """Dismiss menu immediately when overlay loses active window focus."""
        if event.type() == QEvent.ActivationChange and not self.isActiveWindow():
            logger.info("OverlayWindow lost focus -> requesting dismiss")
            self.dismiss_requested.emit()
        super().changeEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Dismiss radial menu when clicking outside radial view on overlay background."""
        logger.info("Clicked outside radial menu -> requesting dismiss")
        self.dismiss_requested.emit()
        super().mousePressEvent(event)

    def set_pass_through(self, pass_through: bool) -> None:
        """Toggle mouse transparency for input events."""
        self.setAttribute(Qt.WA_TransparentForMouseEvents, pass_through)


