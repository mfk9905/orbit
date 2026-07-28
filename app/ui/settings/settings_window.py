"""
Orbit Control Center - Unified Professional Settings & Profile Editor (Logitech Options+ Inspired).
Combines Hotkey configuration, Appearance settings, and Live Radial Menu Slice Editor.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QGroupBox, QFormLayout, QFrame, QMessageBox, QLineEdit, QSplitter
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QIcon
from app.services.settings_service import ISettingsService
from app.services.profile_service import ProfileService
from app.ui.theme.design_system import OrbitTheme
from app.ui.widgets.live_radial_preview import LiveRadialPreviewWidget
from app.ui.widgets.action_card_picker import ActionCardPickerWidget
from app.ui.settings.hotkey_recorder_dialog import HotkeyRecorderDialog
from app.models.profile import Profile, SliceItem
from app.models.actions import action_factory
from app.core.logging.logger import get_logger

logger = get_logger("orbit.ui.settings_window")


def format_hotkey_display(hk_str: str) -> str:
    """Formats raw hotkey code string into user-friendly Turkish text."""
    if not hk_str:
        return "ATANMADI"

    raw = hk_str.lower().strip()
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
        elif p in ("button3", "middle"):
            tr_parts.append("ORTA FARE TUŞU (TEKERLEK)")
        elif p == "button4":
            tr_parts.append("FARE YAN TUŞ 4")
        elif p == "button5":
            tr_parts.append("FARE YAN TUŞ 5")
        elif p == "right":
            tr_parts.append("FARE SAĞ TUŞ")
        else:
            tr_parts.append(p.upper())

    return " + ".join(tr_parts)


class SettingsWindow(QMainWindow):
    """Unified Orbit Control Center Dashboard."""

    def __init__(self, settings_service: ISettingsService, profile_service: ProfileService, hotkey_mgr=None) -> None:
        super().__init__()
        self.settings_service = settings_service
        self.profile_service = profile_service
        self.hotkey_mgr = hotkey_mgr

        self.setWindowTitle("Orbit - Kontrol Merkezi & Halkalar Editörü")
        self.resize(1080, 700)
        self.setMinimumSize(920, 620)
        self.setStyleSheet(OrbitTheme.MAIN_STYLESHEET)

        self._active_profile: Optional[Profile] = None
        self._selected_slice_index: int = -1
        self._subring_nav_stack = []

        self._init_ui()
        self._load_active_profile()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # Left Sidebar Navigation
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)

        self.pages = QStackedWidget()

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages)

        # Build Navigation Pages
        self._add_page("🎯  Halka & Dilim Düzenleyici", self._create_editor_page())
        self._add_page("⌨️  Kısayol Tuşları", self._create_hotkeys_page())
        self._add_page("🎨  Görünüm & Efektler", self._create_appearance_page())
        self._add_page("⚙️  Genel Ayarlar", self._create_general_page())
        self._add_page("❓  Kullanım Rehberi", self._create_about_page())

        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

    def _add_page(self, title: str, widget: QWidget) -> None:
        item = QListWidgetItem(title)
        item.setSizeHint(QSize(220, 48))
        self.sidebar.addItem(item)
        self.pages.addWidget(widget)

    def _load_active_profile(self) -> None:
        self._active_profile = self.profile_service.get_active_profile()
        if hasattr(self, "live_preview"):
            self.live_preview.set_profile(self._active_profile, self._selected_slice_index)
        self._refresh_slice_list()

    def _refresh_profile_combo(self) -> None:
        if not hasattr(self, "cmb_profile_select"):
            return
        self.cmb_profile_select.blockSignals(True)
        self.cmb_profile_select.clear()
        profiles = list(self.profile_service._profiles.values())
        for prof in profiles:
            self.cmb_profile_select.addItem(prof.name, prof.name)
        active = self.profile_service.get_active_profile()
        if active:
            idx = self.cmb_profile_select.findData(active.name)
            if idx >= 0:
                self.cmb_profile_select.setCurrentIndex(idx)
        self.cmb_profile_select.blockSignals(False)

    def _on_profile_combo_changed(self, index: int) -> None:
        prof_name = self.cmb_profile_select.itemData(index)
        if prof_name and prof_name in self.profile_service._profiles:
            self.profile_service.set_active_profile(prof_name)
            self._active_profile = self.profile_service.get_active_profile()
            self._subring_nav_stack.clear()
            self._selected_slice_index = -1
            if hasattr(self, "live_preview"):
                self.live_preview.set_profile(self._active_profile, -1)
            self._refresh_slice_list()

    @property
    def _current_items(self) -> list:
        if self._subring_nav_stack:
            return self._subring_nav_stack[-1][1]
        return self._active_profile.items if self._active_profile else []

    def _create_editor_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Left Section: Slice Controls & Card Picker
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Breadcrumb & SubRing Back Navigation Bar
        nav_bar = QHBoxLayout()
        self.lbl_breadcrumb = QLabel("📍 Halka Konumu: Ana Halka")
        self.lbl_breadcrumb.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_breadcrumb.setStyleSheet("color: #2ED573;")

        self.btn_subring_back = QPushButton("← Geri (Ana Halka)")
        self.btn_subring_back.setObjectName("btn_secondary")
        self.btn_subring_back.setVisible(False)
        self.btn_subring_back.clicked.connect(self._on_pop_subring)

        nav_bar.addWidget(self.lbl_breadcrumb, 1)
        nav_bar.addWidget(self.btn_subring_back)
        left_layout.addLayout(nav_bar)

        # Profile Selector Row
        prof_bar = QHBoxLayout()
        lbl_prof_title = QLabel("Aktif Profil:")
        lbl_prof_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.cmb_profile_select = QComboBox()
        self._refresh_profile_combo()
        self.cmb_profile_select.currentIndexChanged.connect(self._on_profile_combo_changed)

        prof_bar.addWidget(lbl_prof_title)
        prof_bar.addWidget(self.cmb_profile_select, 1)
        left_layout.addLayout(prof_bar)

        # Slice List & Action Buttons
        self.slice_list = QListWidget()
        self.slice_list.setObjectName("slice_list")
        self.slice_list.setFixedHeight(140)
        self.slice_list.currentRowChanged.connect(self._on_slice_list_selection_changed)
        left_layout.addWidget(self.slice_list)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("+ Yeni Dilim")
        btn_add.clicked.connect(self._on_add_blank_slice)

        self.btn_enter_subring = QPushButton("📂 Alt Menüyü Düzenle ➔")
        self.btn_enter_subring.setObjectName("btn_secondary")
        self.btn_enter_subring.setVisible(False)
        self.btn_enter_subring.clicked.connect(self._on_enter_selected_subring)

        btn_delete = QPushButton("Sil")
        btn_delete.setObjectName("btn_danger")
        btn_delete.clicked.connect(self._on_delete_slice)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(self.btn_enter_subring)
        btn_row.addWidget(btn_delete)
        left_layout.addLayout(btn_row)

        # Visual Card Picker
        lbl_cards = QLabel("Görsel Eylem Kataloğu (1-Tıkla Atama):")
        lbl_cards.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_cards.setStyleSheet("color: #00F2FE; margin-top: 6px;")
        left_layout.addWidget(lbl_cards)

        self.card_picker = ActionCardPickerWidget()
        self.card_picker.action_preset_selected.connect(self._on_card_preset_selected)
        left_layout.addWidget(self.card_picker, 1)

        # Right Section: Interactive Live Radial Preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        group_preview = QGroupBox("Canlı Etkileşimli Menü Önizlemesi")
        prev_box = QVBoxLayout(group_preview)

        self.live_preview = LiveRadialPreviewWidget()
        self.live_preview.slice_selected.connect(self._on_live_slice_clicked)
        self.live_preview.center_clicked.connect(self._on_pop_subring)
        prev_box.addWidget(self.live_preview, 1)

        # Selected Slice Quick Customization Box
        self.group_quick_edit = QGroupBox("Seçili Dilim Özelleştirme")
        quick_form = QFormLayout(self.group_quick_edit)

        self.txt_slice_label = QLineEdit()
        self.txt_slice_label.setPlaceholderText("Dilim Başlığı")
        self.txt_slice_label.textChanged.connect(self._on_slice_field_edited)
        quick_form.addRow("Başlık:", self.txt_slice_label)

        self.txt_slice_icon = QLineEdit()
        self.txt_slice_icon.setPlaceholderText("Vektör İkon (camera, copy, play, terminal vb.)")
        self.txt_slice_icon.textChanged.connect(self._on_slice_field_edited)
        quick_form.addRow("İkon:", self.txt_slice_icon)

        self.txt_slice_color = QLineEdit("#2ED573")
        self.txt_slice_color.textChanged.connect(self._on_slice_field_edited)
        quick_form.addRow("Vurgu Rengi:", self.txt_slice_color)

        self.txt_slice_param = QLineEdit()
        self.txt_slice_param.setPlaceholderText("Komut / IP Adresi / Kısayol Tuşu (Örn: ping -t -a 8.8.8.8)")
        self.txt_slice_param.textChanged.connect(self._on_slice_field_edited)
        quick_form.addRow("Komut / IP Parametresi:", self.txt_slice_param)

        prev_box.addWidget(self.group_quick_edit)
        right_layout.addWidget(group_preview)

        # Splitter Layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([540, 480])

        layout.addWidget(splitter)
        return page

    def _refresh_slice_list(self) -> None:
        self.slice_list.blockSignals(True)
        self.slice_list.clear()
        items = self._current_items
        for idx, item in enumerate(items, 1):
            t = type(item.action).__name__
            display = f"{idx}. [{item.icon}]  {item.label}  ({t})"
            self.slice_list.addItem(display)
        self.slice_list.blockSignals(False)

        if self._subring_nav_stack:
            path_str = " ➔ ".join([title for title, _ in self._subring_nav_stack])
            self.lbl_breadcrumb.setText(f"📍 Halka Konumu: Ana Halka ➔ {path_str}")
            self.btn_subring_back.setVisible(True)
        else:
            self.lbl_breadcrumb.setText("📍 Halka Konumu: Ana Halka")
            self.btn_subring_back.setVisible(False)

        if hasattr(self, "live_preview"):
            self.live_preview.set_items(items, self._selected_slice_index)

    def _on_slice_list_selection_changed(self, row: int) -> None:
        self._selected_slice_index = row
        self.live_preview.set_selected_index(row)

        items = self._current_items
        if 0 <= row < len(items):
            item = items[row]
            self.txt_slice_label.blockSignals(True)
            self.txt_slice_icon.blockSignals(True)
            self.txt_slice_color.blockSignals(True)
            self.txt_slice_param.blockSignals(True)

            self.txt_slice_label.setText(item.label)
            self.txt_slice_icon.setText(item.icon)
            self.txt_slice_color.setText(item.color)

            # Extract parameter string if applicable
            params = item.action.params if hasattr(item.action, "params") else {}
            param_val = params.get("command") or params.get("url") or params.get("keys") or params.get("mode") or params.get("text") or ""
            self.txt_slice_param.setText(str(param_val))

            from app.models.actions import SubRingAction
            self.btn_enter_subring.setVisible(isinstance(item.action, SubRingAction))

            self.txt_slice_label.blockSignals(False)
            self.txt_slice_icon.blockSignals(False)
            self.txt_slice_color.blockSignals(False)
            self.txt_slice_param.blockSignals(False)
        else:
            self.btn_enter_subring.setVisible(False)

    def _on_enter_selected_subring(self) -> None:
        items = self._current_items
        if 0 <= self._selected_slice_index < len(items):
            item = items[self._selected_slice_index]
            from app.models.actions import SubRingAction
            if isinstance(item.action, SubRingAction):
                self._subring_nav_stack.append((item.label, item.action.sub_items))
                self._selected_slice_index = -1
                self._refresh_slice_list()

    def _on_pop_subring(self) -> None:
        if self._subring_nav_stack:
            self._subring_nav_stack.pop()
            self._selected_slice_index = -1
            self._refresh_slice_list()

    def _on_live_slice_clicked(self, index: int, item: SliceItem) -> None:
        self.slice_list.setCurrentRow(index)

    def _on_slice_field_edited(self) -> None:
        items = self._current_items
        if not (0 <= self._selected_slice_index < len(items)):
            return

        item = items[self._selected_slice_index]
        item.label = self.txt_slice_label.text().strip() or item.label
        item.icon = self.txt_slice_icon.text().strip() or item.icon
        item.color = self.txt_slice_color.text().strip() or item.color

        param_str = self.txt_slice_param.text().strip()
        if param_str and hasattr(item.action, "params"):
            tname = type(item.action).__name__
            pkey = "command"
            if tname == "UrlAction":
                pkey = "url"
            elif tname == "ShortcutAction":
                pkey = "keys"
            elif tname == "WheelAction":
                pkey = "mode"
            elif tname == "TextAction":
                pkey = "text"
            item.action.params[pkey] = param_str

        if self._active_profile:
            self.profile_service.save_profile(self._active_profile.name, self._active_profile)
        self.live_preview.update()
        self._refresh_slice_list()
        self.slice_list.setCurrentRow(self._selected_slice_index)

    def _on_card_preset_selected(self, card_data: dict) -> None:
        items = self._current_items

        label = card_data["title"]
        act_type = card_data["type"]
        param_val = card_data["param"]
        icon = card_data["icon"]
        color = card_data["color"]

        param_key_map = {
            "AppAction": "command",
            "UrlAction": "url",
            "ShellAction": "command",
            "ShortcutAction": "keys",
            "TextAction": "text",
            "SystemToolAction": "command",
            "MediaAction": "command",
            "WindowControlAction": "command",
            "WheelAction": "mode"
        }
        pkey = param_key_map.get(act_type, "command")

        new_action = action_factory({
            "type": act_type,
            "id": f"act_{label.lower()}",
            "label": label,
            "icon": icon,
            "params": {pkey: param_val}
        })

        new_slice = SliceItem(
            slice_id=f"slice_{label.lower()}",
            label=label,
            icon=icon,
            color=color,
            action=new_action,
            tooltip=label
        )

        if 0 <= self._selected_slice_index < len(items):
            items[self._selected_slice_index] = new_slice
        else:
            items.append(new_slice)
            self._selected_slice_index = len(items) - 1

        if self._active_profile:
            self.profile_service.save_profile(self._active_profile.name, self._active_profile)
        self._refresh_slice_list()
        self.slice_list.setCurrentRow(self._selected_slice_index)

    def _on_add_blank_slice(self) -> None:
        items = self._current_items

        idx = len(items) + 1
        new_action = action_factory({"type": "SystemToolAction", "id": f"a_{idx}", "label": f"Yeni Dilim {idx}", "params": {"command": "snipping_tool"}})
        new_item = SliceItem(f"slice_{idx}", f"Dilim {idx}", "camera", "#2ED573", new_action, f"Yeni Dilim {idx}")

        items.append(new_item)
        self._selected_slice_index = len(items) - 1
        if self._active_profile:
            self.profile_service.save_profile(self._active_profile.name, self._active_profile)
        self._refresh_slice_list()
        self.slice_list.setCurrentRow(self._selected_slice_index)

    def _on_delete_slice(self) -> None:
        items = self._current_items
        if not (0 <= self._selected_slice_index < len(items)):
            return

        item = items[self._selected_slice_index]
        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"'{item.label}' dilimini silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            items.pop(self._selected_slice_index)
            self._selected_slice_index = max(0, self._selected_slice_index - 1)
            if self._active_profile:
                self.profile_service.save_profile(self._active_profile.name, self._active_profile)
            self._refresh_slice_list()

    # --- 2. HOTKEYS PAGE ---
    def _create_hotkeys_page(self) -> QWidget:
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 12, 12)
        layout.setSpacing(14)

        desc = QLabel("Orbit menüsünü ekrana getirmek için kullanacağınız tuşları ve aktivasyon yöntemlerini belirleyin:")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(desc)

        # 1. Primary Shortcut Card
        group1 = QGroupBox("🎯  Ana Aktivasyon Kısayolu")
        vbox1 = QVBoxLayout(group1)
        vbox1.setSpacing(10)

        p_hk = format_hotkey_display(self.settings_service.get('primary_hotkey', 'ctrl+space'))
        self.lbl_primary_hk = QLabel(f"Şu Anki Tuşunuz:  [ {p_hk} ]")
        self.lbl_primary_hk.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.lbl_primary_hk.setStyleSheet("color: #2ED573; background-color: #10141D; padding: 12px; border-radius: 8px; border: 1px solid #232D3F;")
        vbox1.addWidget(self.lbl_primary_hk)

        btn_record_primary = QPushButton("Tuşu Değiştir (Yeni Tuş Seç)...")
        btn_record_primary.clicked.connect(self._on_record_primary_hotkey)
        vbox1.addWidget(btn_record_primary)

        layout.addWidget(group1)

        # 2. Secondary Shortcut Card
        group2 = QGroupBox("🖱️  Yedek (Alternatif) Kısayol Tuşu")
        vbox2 = QVBoxLayout(group2)
        vbox2.setSpacing(10)

        s_hk = format_hotkey_display(self.settings_service.get('secondary_hotkey', 'button4'))
        self.lbl_secondary_hk = QLabel(f"Şu Anki Tuşunuz:  [ {s_hk} ]")
        self.lbl_secondary_hk.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.lbl_secondary_hk.setStyleSheet("color: #00F2FE; background-color: #10141D; padding: 12px; border-radius: 8px; border: 1px solid #232D3F;")
        vbox2.addWidget(self.lbl_secondary_hk)

        btn_record_secondary = QPushButton("Yedek Tuşu Değiştir...")
        btn_record_secondary.setObjectName("btn_secondary")
        btn_record_secondary.clicked.connect(self._on_record_secondary_hotkey)
        vbox2.addWidget(btn_record_secondary)

        layout.addWidget(group2)

        # 3. Corner Hotspot (Mouse-only activation without keyboard)
        group_corner = QGroupBox("📐  Ekran Köşesi Sıcak Noktası (Klavyesiz Açma)")
        form_corner = QFormLayout(group_corner)
        form_corner.setSpacing(10)

        self.chk_corner_hotspot = QCheckBox("Fareyi Ekranın Sol Üst Köşesine Yaslayarak Orbit'i Aç")
        self.chk_corner_hotspot.setChecked(self.settings_service.get("enable_corner_hotspot", True))
        self.chk_corner_hotspot.setFont(QFont("Segoe UI", 10, QFont.Bold))

        def _on_corner_toggled(enabled: bool) -> None:
            self.settings_service.set("enable_corner_hotspot", enabled)
            if self.hotkey_mgr:
                self.hotkey_mgr.set_corner_hotspot(enabled)

        self.chk_corner_hotspot.toggled.connect(_on_corner_toggled)
        form_corner.addRow(self.chk_corner_hotspot)

        lbl_corner_info = QLabel("• Fareyi ekranın en sol üst köşesine götürdüğünüzde dairesel menü otomatik açılır.")
        lbl_corner_info.setStyleSheet("color: #94A3B8; font-size: 11px; margin-top: 2px;")
        form_corner.addRow(lbl_corner_info)

        layout.addWidget(group_corner)

        # 4. Optional Hold Duration Settings Group
        group_hold = QGroupBox("⏱️  Basılı Tutarak Açma Ayarları")
        form_hold = QFormLayout(group_hold)
        form_hold.setSpacing(10)

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

        scroll.setWidget(container)
        return scroll

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

    def _publish_config_change(self, key: str, value: any) -> None:
        self.settings_service.set(key, value)
        try:
            from app.core.container import ServiceContainer
            from app.core.events.event_bus import EventBus, ConfigUpdatedEvent
            bus = ServiceContainer.get_instance().resolve(EventBus)
            if bus:
                bus.publish(ConfigUpdatedEvent(key, value))
        except Exception as e:
            logger.debug(f"EventBus publish debug: {e}")

    # --- 3. APPEARANCE PAGE ---
    def _create_appearance_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("Menü Boyutu ve Animasyon Hızı")
        form = QFormLayout(group)

        size_combo = QComboBox()
        size_combo.addItems(["Küçük (140px)", "Standart (180px)", "Büyük (230px)"])
        cur_radius = self.settings_service.get("radius", 180)
        if cur_radius <= 150:
            size_combo.setCurrentIndex(0)
        elif cur_radius >= 210:
            size_combo.setCurrentIndex(2)
        else:
            size_combo.setCurrentIndex(1)

        def _on_size_changed(idx: int) -> None:
            r_map = {0: 140, 1: 180, 2: 230}
            val = r_map.get(idx, 180)
            self._publish_config_change("radius", val)

        size_combo.currentIndexChanged.connect(_on_size_changed)
        form.addRow("Menü Boyutu:", size_combo)

        opacity_spin = QDoubleSpinBox()
        opacity_spin.setRange(0.2, 1.0)
        opacity_spin.setSingleStep(0.05)
        opacity_spin.setValue(self.settings_service.get("opacity", 0.9))
        opacity_spin.valueChanged.connect(lambda v: self._publish_config_change("opacity", v))
        form.addRow("Saydamlık Seviyesi:", opacity_spin)

        anim_combo = QComboBox()
        anim_combo.addItems(["Hızlı (150 ms)", "Normal (240 ms)", "Yavaş (380 ms)"])
        cur_speed = self.settings_service.get("animation_speed", 240)
        if cur_speed <= 180:
            anim_combo.setCurrentIndex(0)
        elif cur_speed >= 300:
            anim_combo.setCurrentIndex(2)
        else:
            anim_combo.setCurrentIndex(1)

        def _on_anim_changed(idx: int) -> None:
            s_map = {0: 150, 1: 240, 2: 380}
            val = s_map.get(idx, 240)
            self._publish_config_change("animation_speed", val)

        anim_combo.currentIndexChanged.connect(_on_anim_changed)
        form.addRow("Açılış Animasyonu Hızı:", anim_combo)

        blur_check = QCheckBox("Arka Planı Bulanıklaştır (Cam Efekti)")
        blur_check.setChecked(self.settings_service.get("blur_effect", True))
        blur_check.toggled.connect(lambda c: self._publish_config_change("blur_effect", c))
        form.addRow(blur_check)

        layout.addWidget(group)
        layout.addStretch()
        return page

    # --- 4. GENERAL SETTINGS PAGE ---
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

        def _on_autostart_toggled(enabled: bool) -> None:
            self.settings_service.set("autostart", enabled)
            try:
                from app.core.container import ServiceContainer
                from app.core.platform.platform_manager import PlatformManager
                platform = ServiceContainer.get_instance().resolve(type(PlatformManager.create_platform()))
                if platform:
                    platform.set_autostart(enabled)
            except Exception as e:
                logger.error(f"Failed to update platform autostart: {e}")

        autostart_check.toggled.connect(_on_autostart_toggled)
        form.addRow(autostart_check)

        layout.addWidget(group)
        layout.addStretch()
        return page

    # --- 5. ABOUT PAGE ---
    def _create_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Orbit Dairesel Menüye Hoş Geldiniz!")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #2ED573;")

        guide = QLabel(
            "<b>Nasıl Kullanılır?</b><br><br>"
            "1. <b>Kısayol Tuşunuza Basın</b>: Belirlediğiniz kısayol tuşuna (örneğin <i>CTRL + BOŞLUK TUŞU</i> veya <i>FARE YAN TUŞ 4</i>) basınız.<br><br>"
            "2. <b>Fareyi Yönlendirin</b>: Fareyi ekranda açılan dairesel menüdeki istediğiniz dilime doğru hareket ettiriniz.<br><br>"
            "3. <b>Çalıştırın</b>: Seçeneğe tıklayabilir veya tuşu bıraktığınızda eylemin otomatik gerçekleşmesini sağlayabilirsiniz.<br><br>"
            "<i>Orbit, günlük bilgisayar kullanımınızı hızlandırmak için tasarlandı.</i>"
        )
        guide.setWordWrap(True)
        guide.setFont(QFont("Segoe UI", 11))

        layout.addWidget(title)
        layout.addWidget(guide)
        layout.addStretch()
        return page
