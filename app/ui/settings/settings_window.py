"""
Modern KDE Plasma-inspired Settings Window for Orbit (Türkçe - Son Kullanıcı Odaklı).
Features intuitive card layouts, simple controls, hold duration options, and live hotkey binding.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QGroupBox, QFormLayout, QFrame, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QIcon
from app.services.settings_service import ISettingsService
from app.services.profile_service import ProfileService
from app.ui.settings.slice_editor_dialog import SliceEditorDialog
from app.ui.settings.hotkey_recorder_dialog import HotkeyRecorderDialog
from app.core.logging.logger import get_logger

logger = get_logger("orbit.ui.settings")


def format_hotkey_display(hk_str: str) -> str:
    """Formats raw hotkey code string into user-friendly Turkish text."""
    if not hk_str:
        return "ATANMADI"

    raw = hk_str.lower().strip()
    if raw == "button4":
        return "FARE YAN TUŞ 4 (GERİ)"
    if raw == "button5":
        return "FARE YAN TUŞ 5 (İLERİ)"

    parts = raw.split("+")
    tr_parts = []
    for p in parts:
        p = p.strip()
        if p == "ctrl":
            tr_parts.append("CTRL")
        elif p == "alt":
            tr_parts.append("ALT")
        elif p == "shift":
            tr_parts.append("SHIFT")
        elif p in ("super", "cmd", "win"):
            tr_parts.append("SUPER (WINDOWS)")
        elif p == "space":
            tr_parts.append("BOŞLUK TUŞU")
        else:
            tr_parts.append(p.upper())

    return " + ".join(tr_parts)


class SettingsWindow(QMainWindow):
    """KDE-styled Settings Window with end-user friendly card navigation."""

    def __init__(self, settings_service: ISettingsService, profile_service: ProfileService, hotkey_mgr=None) -> None:
        super().__init__()
        self.settings_service = settings_service
        self.profile_service = profile_service
        self.hotkey_mgr = hotkey_mgr

        self.setWindowTitle("Orbit - Kolay Kontrol ve Ayar Merkezi")
        self.resize(860, 580)
        self._apply_dark_theme()

        self._init_ui()

    def _apply_dark_theme(self) -> None:
        """Applies KDE Plasma dark mode stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1b1e23;
                color: #eff0f1;
            }
            QListWidget#sidebar {
                background-color: #232629;
                border: 1px solid #31363b;
                border-radius: 8px;
                outline: none;
                font-size: 14px;
            }
            QListWidget#sidebar::item {
                padding: 14px 16px;
                color: #bdc3c7;
                border-radius: 6px;
                margin: 4px 6px;
            }
            QListWidget#sidebar::item:hover {
                background-color: #2a2e32;
                color: #ffffff;
            }
            QListWidget#sidebar::item:selected {
                background-color: #2ED573;
                color: #0b2214;
                font-weight: bold;
            }
            QListWidget#slice_list {
                background-color: #232629;
                border: 1px solid #31363b;
                border-radius: 8px;
                font-size: 13px;
            }
            QListWidget#slice_list::item {
                padding: 12px 16px;
                color: #ffffff;
                border-bottom: 1px solid #2a2e32;
            }
            QListWidget#slice_list::item:selected {
                background-color: #2ED573;
                color: #0b2214;
                font-weight: bold;
            }
            QLabel {
                color: #eff0f1;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #31363b;
                border-radius: 10px;
                margin-top: 14px;
                padding-top: 18px;
                background-color: #212529;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 6px;
                color: #2ED573;
            }
            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
                background-color: #2a2e32;
                border: 1px solid #31363b;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton {
                background-color: #2ED573;
                color: #0b2214;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 18px;
            }
            QPushButton:hover {
                background-color: #26af5f;
            }
            QPushButton#btn_secondary {
                background-color: #34495e;
                color: #ffffff;
            }
            QPushButton#btn_secondary:hover {
                background-color: #2c3e50;
            }
            QPushButton#btn_danger {
                background-color: #e74c3c;
                color: #ffffff;
            }
            QPushButton#btn_danger:hover {
                background-color: #c0392b;
            }
        """)

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)

        self.pages = QStackedWidget()

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages)

        # Create Pages
        self._add_page("Kısayol Tuşları", self._create_hotkeys_page())
        self._add_page("Menü Düzenleyici", self._create_profiles_page())
        self._add_page("Görünüm & Boyut", self._create_appearance_page())
        self._add_page("Genel Ayarlar", self._create_general_page())
        self._add_page("Nasıl Kullanılır?", self._create_about_page())

        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

    def _add_page(self, title: str, widget: QWidget) -> None:
        item = QListWidgetItem(title)
        item.setSizeHint(QSize(200, 46))
        self.sidebar.addItem(item)
        self.pages.addWidget(widget)

    def _create_hotkeys_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        desc = QLabel("Orbit menüsünü ekrana getirmek için kullanacağınız tuşları aşağıdan kolayca belirleyebilirsiniz:")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Primary Shortcut Card
        group1 = QGroupBox("Ana Aktivasyon Kısayolu")
        vbox1 = QVBoxLayout(group1)

        p_hk = format_hotkey_display(self.settings_service.get('primary_hotkey', 'ctrl+space'))
        self.lbl_primary_hk = QLabel(f"Şu Anki Tuşunuz:  [ {p_hk} ]")
        self.lbl_primary_hk.setFont(QFont("Outfit", 12, QFont.Bold))
        self.lbl_primary_hk.setStyleSheet("color: #2ED573; background-color: #1a231e; padding: 10px; border-radius: 6px;")
        vbox1.addWidget(self.lbl_primary_hk)

        btn_record_primary = QPushButton("Tuşu Değiştir (Yeni Tuş Seç)...")
        btn_record_primary.clicked.connect(self._on_record_primary_hotkey)
        vbox1.addWidget(btn_record_primary)

        layout.addWidget(group1)

        # Secondary Shortcut Card
        group2 = QGroupBox("Yedek (Alternatif) Kısayol Tuşu")
        vbox2 = QVBoxLayout(group2)

        s_hk = format_hotkey_display(self.settings_service.get('secondary_hotkey', 'button4'))

        self.lbl_secondary_hk = QLabel(f"Şu Anki Tuşunuz:  [ {s_hk} ]")
        self.lbl_secondary_hk.setFont(QFont("Outfit", 12, QFont.Bold))
        self.lbl_secondary_hk.setStyleSheet("color: #3498db; background-color: #1a202a; padding: 10px; border-radius: 6px;")
        vbox2.addWidget(self.lbl_secondary_hk)

        btn_record_secondary = QPushButton("Yedek Tuşu Değiştir...")
        btn_record_secondary.setObjectName("btn_secondary")
        btn_record_secondary.clicked.connect(self._on_record_secondary_hotkey)
        vbox2.addWidget(btn_record_secondary)

        layout.addWidget(group2)

        # Optional Hold Duration Settings Group
        group_hold = QGroupBox("İsteğe Bağlı Basılı Tutarak Açma Ayarları")
        form_hold = QFormLayout(group_hold)

        self.chk_enable_hold = QCheckBox("Kısayol Tuşuna Belirli Süre Basılı Tutulduğunda Menüyü Aç")
        self.chk_enable_hold.setChecked(self.settings_service.get("enable_hold_duration", False))
        self.chk_enable_hold.toggled.connect(self._on_hold_option_changed)
        form_hold.addRow(self.chk_enable_hold)

        self.spin_hold_duration = QDoubleSpinBox()
        self.spin_hold_duration.setRange(0.2, 5.0)
        self.spin_hold_duration.setSingleStep(0.2)
        self.spin_hold_duration.setValue(self.settings_service.get("hold_duration_seconds", 1.0))
        self.spin_hold_duration.valueChanged.connect(self._on_hold_option_changed)
        form_hold.addRow("Gerekli Basılı Tutma Süresi (Saniye):", self.spin_hold_duration)

        layout.addWidget(group_hold)

        layout.addStretch()
        return page

    def _on_hold_option_changed(self) -> None:
        enabled = self.chk_enable_hold.isChecked()
        duration = float(self.spin_hold_duration.value())

        self.settings_service.set("enable_hold_duration", enabled)
        self.settings_service.set("hold_duration_seconds", duration)

        if self.hotkey_mgr:
            self.hotkey_mgr.set_hold_options(enabled, duration)

    def _on_record_primary_hotkey(self) -> None:
        dialog = HotkeyRecorderDialog(parent=self)
        if dialog.exec() == HotkeyRecorderDialog.Accepted and dialog.recorded_shortcut:
            new_hk = dialog.recorded_shortcut
            self.settings_service.set("primary_hotkey", new_hk)
            disp = format_hotkey_display(new_hk)
            self.lbl_primary_hk.setText(f"Şu Anki Tuşunuz:  [ {disp} ]")
            if self.hotkey_mgr:
                self.hotkey_mgr.set_hotkeys(new_hk, self.settings_service.get("secondary_hotkey", "button4"))

    def _on_record_secondary_hotkey(self) -> None:
        dialog = HotkeyRecorderDialog(parent=self)
        if dialog.exec() == HotkeyRecorderDialog.Accepted and dialog.recorded_shortcut:
            new_hk = dialog.recorded_shortcut
            self.settings_service.set("secondary_hotkey", new_hk)
            disp = format_hotkey_display(new_hk)
            self.lbl_secondary_hk.setText(f"Şu Anki Tuşunuz:  [ {disp} ]")
            if self.hotkey_mgr:
                self.hotkey_mgr.set_hotkeys(self.settings_service.get("primary_hotkey", "ctrl+space"), new_hk)

    def _create_profiles_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("Dairesel Menü Elemanlarınız")
        vbox = QVBoxLayout(group)

        vbox.addWidget(QLabel("Ekrandaki dairesel menünüzde yer alan hızlı erişim seçenekleri:"))
        self.slice_list = QListWidget()
        self.slice_list.setObjectName("slice_list")
        self.slice_list.setFixedHeight(230)
        vbox.addWidget(self.slice_list)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("+ Yeni Hızlı Erişim Ekle")
        btn_add.clicked.connect(self._on_add_slice)

        btn_edit = QPushButton("Seçileni Düzenle")
        btn_edit.setObjectName("btn_secondary")
        btn_edit.clicked.connect(self._on_edit_slice)

        btn_delete = QPushButton("Sil")
        btn_delete.setObjectName("btn_danger")
        btn_delete.clicked.connect(self._on_delete_slice)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_delete)
        vbox.addLayout(btn_row)

        layout.addWidget(group)
        self._refresh_slice_list()
        return page

    def _refresh_slice_list(self) -> None:
        self.slice_list.clear()
        profile = self.profile_service.get_active_profile()
        for idx, item in enumerate(profile.items, 1):
            display = f"{idx}. {item.label}   ➔   {item.tooltip}"
            list_item = QListWidgetItem(display)
            self.slice_list.addItem(list_item)

    def _on_add_slice(self) -> None:
        dialog = SliceEditorDialog(parent=self)
        if dialog.exec() == SliceEditorDialog.Accepted:
            new_item = dialog.get_slice_item()
            profile = self.profile_service.get_active_profile()
            profile.items.append(new_item)
            self.profile_service.save_profile(profile.name, profile)
            self._refresh_slice_list()

    def _on_edit_slice(self) -> None:
        row = self.slice_list.currentRow()
        profile = self.profile_service.get_active_profile()
        if 0 <= row < len(profile.items):
            current_item = profile.items[row]
            dialog = SliceEditorDialog(slice_item=current_item, parent=self)
            if dialog.exec() == SliceEditorDialog.Accepted:
                updated_item = dialog.get_slice_item()
                profile.items[row] = updated_item
                self.profile_service.save_profile(profile.name, profile)
                self._refresh_slice_list()

    def _on_delete_slice(self) -> None:
        row = self.slice_list.currentRow()
        profile = self.profile_service.get_active_profile()
        if 0 <= row < len(profile.items):
            reply = QMessageBox.question(
                self, "Silme Onayı",
                f"'{profile.items[row].label}' elemanını menüden kaldırmak istediğinize emin misiniz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                profile.items.pop(row)
                self.profile_service.save_profile(profile.name, profile)
                self._refresh_slice_list()

    def _create_appearance_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("Menü Boyutu ve Animasyon Hızı")
        form = QFormLayout(group)

        size_combo = QComboBox()
        size_combo.addItems(["Standart (Orta Boyut)", "Küçük", "Büyük"])
        form.addRow("Menü Boyutu:", size_combo)

        opacity_spin = QDoubleSpinBox()
        opacity_spin.setRange(0.2, 1.0)
        opacity_spin.setSingleStep(0.05)
        opacity_spin.setValue(self.settings_service.get("opacity", 0.9))
        opacity_spin.valueChanged.connect(lambda v: self.settings_service.set("opacity", v))
        form.addRow("Saydamlık Seviyesi:", opacity_spin)

        anim_combo = QComboBox()
        anim_combo.addItems(["Hızlı (Akıcı)", "Normal", "Yavaş"])
        form.addRow("Açılış Animasyonu Hızı:", anim_combo)

        blur_check = QCheckBox("Arka Planı Bulanıklaştır (Cam Efekti)")
        blur_check.setChecked(self.settings_service.get("blur_effect", True))
        blur_check.toggled.connect(lambda c: self.settings_service.set("blur_effect", c))
        form.addRow(blur_check)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _create_general_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("Genel Uygulama Ayarları")
        form = QFormLayout(group)

        lang_combo = QComboBox()
        lang_combo.addItems(["Türkçe", "English", "Deutsch"])
        form.addRow("Uygulama Dili:", lang_combo)

        autostart_check = QCheckBox("Bilgisayar Açıldığında Orbit Otomatik Başlasın")
        autostart_check.setChecked(self.settings_service.get("autostart", False))
        autostart_check.toggled.connect(lambda c: self.settings_service.set("autostart", c))
        form.addRow(autostart_check)

        layout.addWidget(group)
        layout.addStretch()
        return page

    def _create_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Orbit Dairesel Menüye Hoş Geldiniz!")
        title.setFont(QFont("Outfit", 16, QFont.Bold))
        title.setStyleSheet("color: #2ED573;")

        guide = QLabel(
            "<b>Nasıl Kullanılır?</b><br><br>"
            "1. <b>Kısayol Tuşunuza Basın</b>: Belirlediğiniz kısayol tuşuna (örneğin <i>CTRL + BOŞLUK TUŞU</i> veya <i>FARE YAN TUŞ 4</i>) basınız.<br><br>"
            "2. <b>Fareyi Yönlendirin</b>: Fareyi ekranda açılan dairesel menüdeki istediğiniz dilime doğru hareket ettiriniz.<br><br>"
            "3. <b>Çalıştırın</b>: Seçeneğe tıklayabilir veya tuşu bıraktığınızda eylemin otomatik gerçekleşmesini sağlayabilirsiniz.<br><br>"
            "<i>Orbit, günlük bilgisayar kullanımınızı hızlandırmak için tasarlandı.</i>"
        )
        guide.setWordWrap(True)
        guide.setFont(QFont("Outfit", 11))

        layout.addWidget(title)
        layout.addWidget(guide)
        layout.addStretch()
        return page
