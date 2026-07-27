"""
Visual Action Preset Card Selector Widget for Orbit Control Center.
Presents end-user friendly cards instead of technical raw text parameter fields.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea,
    QPushButton, QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from app.core.icons.icon_manager import IconManager
from app.models.actions import action_factory


class ActionCard(QFrame):
    """Clickable preset card representing a Logitech-style productivity action."""

    card_clicked = Signal(dict)  # Emits action config dict

    def __init__(self, title: str, category: str, action_type: str, param_val: str, icon_name: str, color: str, desc: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.config_data = {
            "title": title,
            "type": action_type,
            "param": param_val,
            "icon": icon_name,
            "color": color,
            "desc": desc
        }

        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1C2433;
                border: 1px solid #2A364F;
                border-radius: 10px;
                padding: 10px;
            }}
            QFrame:hover {{
                background-color: #253247;
                border-color: {color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header Row (Icon + Title)
        hdr = QHBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_title.setStyleSheet(f"color: {color};")
        hdr.addWidget(lbl_title)
        hdr.addStretch()

        layout.addLayout(hdr)

        # Description
        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setFont(QFont("Segoe UI", 8.5))
        lbl_desc.setStyleSheet("color: #94A3B8;")
        layout.addWidget(lbl_desc)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.card_clicked.emit(self.config_data)


class ActionCardPickerWidget(QWidget):
    """Categorized visual preset card selector container."""

    action_preset_selected = Signal(dict)

    CATEGORIES = {
        "🛠️ Sistem": [
            ("Ekran Alıntısı Aracı", "SystemToolAction", "snipping_tool", "camera", "#FF4757", "Win+Shift+S ile ekran alıntısı alır."),
            ("Yapay Zeka Asistanı", "UrlAction", "https://chatgpt.com", "cpu", "#00F2FE", "ChatGPT / Yapay Zeka asistanını tarayıcıda açar."),
            ("Otomatik IP Ping Aracı", "ShellAction", "cmd.exe /k ping -t -a 8.8.8.8", "terminal", "#2ED573", "Yazılan IP adresine kesintisiz ping atar (ping -t -a)."),
            ("Görev Yöneticisi", "SystemToolAction", "task_manager", "cpu", "#3498DB", "Ctrl+Shift+Esc ile sistem takibini açar."),
            ("Dosya Gezgini", "SystemToolAction", "file_explorer", "folder", "#FFA502", "Win+E ile dosya gezginini açar."),
            ("Bilgisayarı Kilitle", "SystemToolAction", "lock_screen", "lock", "#E74C3C", "Win+L ile oturumu güvenle kilitler."),
            ("Masaüstünü Göster", "SystemToolAction", "show_desktop", "monitor", "#2ED573", "Win+D ile tüm pencereleri simge durumuna küçültür."),
            ("Emoji Paneli", "SystemToolAction", "emoji_panel", "smile", "#F1C40F", "Win+. ile emoji & sembol penceresini açar.")
        ],
        "🎵 Ses & Medya": [
            ("Oynat / Duraklat", "MediaAction", "play_pause", "play", "#2ED573", "Aktif medya oynatıcıyı duraklatır veya sürdürür."),
            ("Sonraki Parça", "MediaAction", "next_track", "skip-forward", "#1ABC9C", "Müzik veya videoda sonraki parçaya geçer."),
            ("Önceki Parça", "MediaAction", "prev_track", "skip-back", "#1ABC9C", "Müzik veya videoda önceki parçaya döner."),
            ("Sesi Kapat / Aç (Mute)", "MediaAction", "volume_mute", "volume-x", "#FF4757", "Sistemin genel sesini anında kapatır veya açar."),
            ("Sesi Arttır", "MediaAction", "volume_up", "volume-2", "#3498DB", "Sistem sesini kademeli olarak yükseltir."),
            ("Sesi Azalt", "MediaAction", "volume_down", "volume-2", "#3498DB", "Sistem sesini kademeli olarak düşürür."),
            ("Fare Tekerleği Ses Modu", "WheelAction", "volume", "mouse", "#9B59B6", "Fare tekerleğini çevirerek ses ayarı yapar.")
        ],
        "🪟 Pencere Hizalama": [
            ("Pencereyi Küçült", "WindowControlAction", "minimize", "minus", "#9B59B6", "Aktif pencereyi simge durumuna küçültür."),
            ("Ekranı Kapla (Büyüt)", "WindowControlAction", "maximize", "square", "#2ED573", "Aktif pencereyi tüm ekrana kaplar."),
            ("Pencereyi Sola Yasla", "WindowControlAction", "snap_left", "arrow-left", "#3498DB", "Pencereyi ekranın sol yarısına hizalar."),
            ("Pencereyi Sağa Yasla", "WindowControlAction", "snap_right", "arrow-right", "#3498DB", "Pencereyi ekranın sağ yarısına hizalar."),
            ("Görev Görünümü", "WindowControlAction", "task_view", "layers", "#FFA502", "Win+Tab ile açık tüm pencereleri listeler."),
            ("Sonraki Sanal Masaüstü", "WindowControlAction", "next_desktop", "chevron-right", "#00F2FE", "Sağdaki sanal masaüstüne geçiş yapar."),
            ("Önceki Sanal Masaüstü", "WindowControlAction", "prev_desktop", "chevron-left", "#00F2FE", "Soldaki sanal masaüstüne geçiş yapar.")
        ],
        "📋 Pano & Metin": [
            ("Metin Kopyala", "ShortcutAction", "ctrl+c", "copy", "#FFA502", "Ctrl+C kisayolu ile seçili metni kopyalar."),
            ("Metin Yapıştır", "ShortcutAction", "ctrl+v", "clipboard", "#2ED573", "Ctrl+V kısayolu ile panoyu yapıştırır."),
            ("Düz Metin Yapıştır", "ShortcutAction", "ctrl+shift+v", "clipboard", "#1ABC9C", "Biçimlendirmesiz düz metin yapıştırır."),
            ("Pano Geçmişi Paneli", "ShortcutAction", "cmd+v", "clipboard", "#3498DB", "Win+V ile Windows pano geçmişini açar."),
            ("İşlemi Geri Al", "ShortcutAction", "ctrl+z", "rotate-ccw", "#FF4757", "Son yapılan işlemi geri alır."),
            ("İşlemi Yinele", "ShortcutAction", "ctrl+y", "refresh-cw", "#9B59B6", "Geri alınan işlemi tekrar uygular.")
        ],
        "🚀 Uygulama & Web": [
            ("VS Code Editörü", "AppAction", "code", "code", "#00F2FE", "Visual Studio Code uygulamasını başlatır."),
            ("Sistem Terminali", "AppAction", "wt || cmd.exe /c start cmd || konsole", "terminal", "#2ED573", "Windows Terminal / CMD komut satırını açar."),
            ("Google Arama", "UrlAction", "https://google.com", "globe", "#3498DB", "Google arama sayfasını varsayılan tarayıcıda açar."),
            ("Google Chrome Tarayıcı", "AppAction", "google-chrome || chrome", "globe", "#FFA502", "Chrome internet tarayıcısını başlatır.")
        ]
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #232D3F;
                border-radius: 8px;
                background-color: #141923;
            }
            QTabBar::tab {
                background-color: #10141D;
                color: #94A3B8;
                padding: 8px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #141923;
                color: #2ED573;
                border-bottom: 2px solid #2ED573;
            }
        """)

        for cat_name, cards_list in self.CATEGORIES.items():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("background-color: #141923; border: none;")

            container = QWidget()
            grid = QGridLayout(container)
            grid.setSpacing(10)
            grid.setContentsMargins(10, 10, 10, 10)

            for idx, item_tuple in enumerate(cards_list):
                title, act_type, param, icon_name, color, desc = item_tuple
                card = ActionCard(title, cat_name, act_type, param, icon_name, color, desc)
                card.card_clicked.connect(self.action_preset_selected.emit)

                row = idx // 2
                col = idx % 2
                grid.addWidget(card, row, col)

            scroll.setWidget(container)
            self.tab_widget.addTab(scroll, cat_name)

        layout.addWidget(self.tab_widget)
