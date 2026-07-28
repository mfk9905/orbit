"""
Orbit Sistem Tepsisi (System Tray) Entegrasyonu.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from typing import Callable
from app.core.logging.logger import get_logger

logger = get_logger("orbit.ui.system_tray")


def create_default_tray_icon() -> QIcon:
    """Simge dosyası bulunamadığında programatik yeşil ikon oluşturur."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#2ED573"))
    painter.setPen(QColor("#1e824c"))
    painter.drawEllipse(4, 4, 56, 56)
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawEllipse(20, 20, 24, 24)
    painter.end()
    return QIcon(pixmap)


class SystemTrayService:
    """Sistem tepsi simgesini ve Türkçe sağ tık menüsünü yönetir."""

    def __init__(
        self,
        on_open_settings: Callable[[], None],
        on_reload: Callable[[], None],
        on_restart: Callable[[], None],
        on_quit: Callable[[], None],
        on_open_editor: Callable[[], None] | None = None
    ) -> None:
        self.on_open_settings = on_open_settings
        self.on_reload = on_reload
        self.on_restart = on_restart
        self.on_quit = on_quit

        self._tray_icon = QSystemTrayIcon()
        self._tray_icon.setIcon(create_default_tray_icon())
        self._tray_icon.setToolTip("Orbit - Dairesel Menü")

        self._menu = QMenu()
        self._setup_menu()
        self._tray_icon.setContextMenu(self._menu)
        self._tray_icon.show()

        logger.info("Sistem Tepsi simgesi başlatıldı.")

    def _setup_menu(self) -> None:
        """Türkçe sistem tepsi menüsünü yapılandırır."""
        settings_action = self._menu.addAction("⚙️ Kontrol Merkezi & Editör")
        settings_action.triggered.connect(self.on_open_settings)

        self._menu.addSeparator()

        reload_action = self._menu.addAction("🔄 Profilleri Yeniden Yükle")
        reload_action.triggered.connect(self.on_reload)

        restart_action = self._menu.addAction("⚡ Uygulamayı Yeniden Başlat")
        restart_action.triggered.connect(self.on_restart)

        self._menu.addSeparator()

        quit_action = self._menu.addAction("❌ Çıkış")
        quit_action.triggered.connect(self.on_quit)

    def hide(self) -> None:
        self._tray_icon.hide()

