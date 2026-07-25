"""
Visual Profile Editor Window for Orbit Radial Menu (PySide6).
Allows creating, editing, and binding profiles to applications with full GUI and nested SubRing support.
"""

import json
from typing import List, Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QComboBox, QTextEdit,
    QDialog, QFormLayout, QSpinBox, QMessageBox, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from app.models.profile import Profile, SliceItem
from app.models.actions import (
    AppAction, UrlAction, ShellAction, ShortcutAction, TextAction,
    MacroAction, WheelAction, WindowControlAction, SubRingAction, action_factory
)
from app.core.icons.svg_library import SVG_ICONS
from app.services.profile_service import ProfileService
from app.core.logging.logger import get_logger

logger = get_logger("orbit.ui.editor")

PRESET_COLORS = [
    ("#2ED573", "Yeşil"),
    ("#3498DB", "Mavi"),
    ("#E74C3C", "Kırmızı"),
    ("#F1C40F", "Sarı"),
    ("#9B59B6", "Mor"),
    ("#E67E22", "Turuncu"),
    ("#1ABC9C", "Turkuaz"),
    ("#FFA502", "Kehribar")
]


class SliceItemDialog(QDialog):
    """Dialog to create or edit a single SliceItem and its Action (supports nested SubRings)."""

    def __init__(self, item: SliceItem | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Dilim / Eylem Düzenleyici")
        self.resize(520, 560)
        self.item = item
        self.sub_items: List[SliceItem] = []
        self._init_ui()
        if item:
            self._load_item_data(item)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Örn: Kopyala, Terminal, Zoom")

        self.icon_input = QComboBox()
        self.icon_input.setEditable(True)
        self.icon_input.addItems(list(SVG_ICONS.keys()))

        # Color input with visual preset buttons
        color_layout = QHBoxLayout()
        self.color_input = QLineEdit("#2ED573")
        color_layout.addWidget(self.color_input)

        for hex_code, color_name in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setToolTip(color_name)
            btn.setStyleSheet(f"background-color: {hex_code}; border: 1px solid #ffffff; border-radius: 4px;")
            btn.clicked.connect(lambda _, c=hex_code: self.color_input.setText(c))
            color_layout.addWidget(btn)

        self.tooltip_input = QLineEdit()

        self.action_type = QComboBox()
        self.action_type.addItems([
            "AppAction", "UrlAction", "ShellAction", "ShortcutAction", "TextAction",
            "MacroAction", "WheelAction", "WindowControlAction", "SubRingAction"
        ])
        self.action_type.currentTextChanged.connect(self._on_action_type_changed)

        self.param1_label = QLabel("Komut / Yol:")
        self.param1_input = QLineEdit()

        self.param2_label = QLabel("Ek Parametre:")
        self.param2_input = QLineEdit()

        form.addRow("Dilim Etiketi:", self.label_input)
        form.addRow("Vektör İkon:", self.icon_input)
        form.addRow("Vurgu Rengi:", color_layout)
        form.addRow("İpucu (Tooltip):", self.tooltip_input)
        form.addRow("Eylem Tipi:", self.action_type)
        form.addRow(self.param1_label, self.param1_input)
        form.addRow(self.param2_label, self.param2_input)

        layout.addLayout(form)

        # --- Nested Sub-Ring Items UI (Visible only when SubRingAction selected) ---
        self.sub_ring_group = QGroupBox("Alt Halka Dilimleri (Sub-Items)")
        sub_layout = QVBoxLayout(self.sub_ring_group)

        self.sub_list_widget = QListWidget()
        sub_layout.addWidget(self.sub_list_widget)

        sub_btn_bar = QHBoxLayout()
        add_sub_btn = QPushButton("+ Alt Dilim Ekle")
        add_sub_btn.clicked.connect(self._on_add_sub_item)
        edit_sub_btn = QPushButton("Düzenle")
        edit_sub_btn.clicked.connect(self._on_edit_sub_item)
        del_sub_btn = QPushButton("Sil")
        del_sub_btn.clicked.connect(self._on_delete_sub_item)

        sub_btn_bar.addWidget(add_sub_btn)
        sub_btn_bar.addWidget(edit_sub_btn)
        sub_btn_bar.addWidget(del_sub_btn)
        sub_layout.addLayout(sub_btn_bar)

        layout.addWidget(self.sub_ring_group)
        self.sub_ring_group.hide()

        # Dialog buttons
        btn_box = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        save_btn.setStyleSheet("background-color: #2ED573; color: #0A140F; font-weight: bold; padding: 6px 16px;")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

        self._on_action_type_changed("AppAction")

    def _on_action_type_changed(self, act_type: str) -> None:
        if act_type == "SubRingAction":
            self.param1_label.hide()
            self.param1_input.hide()
            self.param2_label.hide()
            self.param2_input.hide()
            self.sub_ring_group.show()
        elif act_type == "AppAction":
            self.sub_ring_group.hide()
            self.param1_label.show()
            self.param1_input.show()
            self.param1_label.setText("Uygulama Komutu:")
            self.param1_input.setPlaceholderText("wt || cmd.exe /c start cmd || code")
            self.param2_label.hide()
            self.param2_input.hide()
        elif act_type == "UrlAction":
            self.sub_ring_group.hide()
            self.param1_label.show()
            self.param1_input.show()
            self.param1_label.setText("Web Adresi (URL):")
            self.param1_input.setPlaceholderText("https://google.com")
            self.param2_label.hide()
            self.param2_input.hide()
        elif act_type == "ShortcutAction":
            self.sub_ring_group.hide()
            self.param1_label.show()
            self.param1_input.show()
            self.param1_label.setText("Kısayol Tuşları:")
            self.param1_input.setPlaceholderText("ctrl+c, ctrl+shift+p, alt+f4")
            self.param2_label.hide()
            self.param2_input.hide()
        elif act_type == "TextAction":
            self.sub_ring_group.hide()
            self.param1_label.show()
            self.param1_input.show()
            self.param1_label.setText("Yazdırılacak Metin:")
            self.param1_input.setPlaceholderText("Otomatik yazılacak metin...")
            self.param2_label.hide()
            self.param2_input.hide()
        elif act_type == "WheelAction":
            self.sub_ring_group.hide()
            self.param1_label.show()
            self.param1_input.show()
            self.param1_label.setText("Mod (volume/zoom/shortcut):")
            self.param1_input.setPlaceholderText("volume veya zoom")
            self.param2_label.show()
            self.param2_input.show()
            self.param2_label.setText("Kısayol (Up/Down):")
            self.param2_input.setPlaceholderText("ctrl+up / ctrl+down")
        elif act_type == "WindowControlAction":
            self.sub_ring_group.hide()
            self.param1_label.show()
            self.param1_input.show()
            self.param1_label.setText("Komut (minimize/maximize/snap_left/snap_right):")
            self.param1_input.setPlaceholderText("minimize")
            self.param2_label.hide()
            self.param2_input.hide()
        else:
            self.sub_ring_group.hide()
            self.param1_label.show()
            self.param1_input.show()
            self.param1_label.setText("Komut / Parametre:")
            self.param1_input.setPlaceholderText("")
            self.param2_label.hide()
            self.param2_input.hide()

    def _update_sub_list(self) -> None:
        self.sub_list_widget.clear()
        for sub in self.sub_items:
            t = type(sub.action).__name__
            self.sub_list_widget.addItem(f"[{sub.icon}] {sub.label} ({t})")

    def _on_add_sub_item(self) -> None:
        dlg = SliceItemDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            new_sub = dlg.get_slice_item()
            self.sub_items.append(new_sub)
            self._update_sub_list()

    def _on_edit_sub_item(self) -> None:
        row = self.sub_list_widget.currentRow()
        if 0 <= row < len(self.sub_items):
            old_sub = self.sub_items[row]
            dlg = SliceItemDialog(item=old_sub, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.sub_items[row] = dlg.get_slice_item()
                self._update_sub_list()

    def _on_delete_sub_item(self) -> None:
        row = self.sub_list_widget.currentRow()
        if 0 <= row < len(self.sub_items):
            del self.sub_items[row]
            self._update_sub_list()

    def _load_item_data(self, item: SliceItem) -> None:
        self.label_input.setText(item.label)
        self.icon_input.setCurrentText(item.icon)
        self.color_input.setText(item.color)
        self.tooltip_input.setText(item.tooltip)

        act = item.action
        act_type = type(act).__name__
        self.action_type.setCurrentText(act_type)

        if isinstance(act, SubRingAction):
            self.sub_items = [
                SliceItem.from_dict(sub.to_dict()) if hasattr(sub, "to_dict") else sub
                for sub in getattr(act, "sub_items", [])
            ]
            self._update_sub_list()
        elif isinstance(act, AppAction):
            self.param1_input.setText(act.params.get("command", ""))
        elif isinstance(act, UrlAction):
            self.param1_input.setText(act.params.get("url", ""))
        elif isinstance(act, ShortcutAction):
            self.param1_input.setText(act.params.get("keys", ""))
        elif isinstance(act, TextAction):
            self.param1_input.setText(act.params.get("text", ""))
        elif isinstance(act, WheelAction):
            self.param1_input.setText(act.params.get("mode", "volume"))

    def get_slice_item(self) -> SliceItem:
        label = self.label_input.text().strip() or "Dilim"
        icon = self.icon_input.currentText().strip() or "command"
        color = self.color_input.text().strip() or "#2ED573"
        tooltip = self.tooltip_input.text().strip() or label
        act_type = self.action_type.currentText()
        p1 = self.param1_input.text().strip()

        if act_type == "SubRingAction":
            action = SubRingAction("act", label, icon=icon, params={}, items=self.sub_items)
        elif act_type == "AppAction":
            action = AppAction("act", label, icon=icon, params={"command": p1})
        elif act_type == "UrlAction":
            action = UrlAction("act", label, icon=icon, params={"url": p1})
        elif act_type == "ShortcutAction":
            action = ShortcutAction("act", label, icon=icon, params={"keys": p1})
        elif act_type == "TextAction":
            action = TextAction("act", label, icon=icon, params={"text": p1})
        elif act_type == "WheelAction":
            action = WheelAction("act", label, icon=icon, params={"mode": p1 or "volume"})
        elif act_type == "WindowControlAction":
            action = WindowControlAction("act", label, icon=icon, params={"command": p1 or "minimize"})
        else:
            action = AppAction("act", label, icon=icon, params={"command": p1})

        slice_id = self.item.slice_id if self.item else f"slice_{label.lower()}"
        return SliceItem(slice_id, label, icon, color, action, tooltip)


class ProfileEditorWindow(QMainWindow):
    """GUI Window for visually managing and creating Orbit Radial Profiles."""

    profiles_updated = Signal()

    def __init__(self, profile_service: ProfileService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.profile_service = profile_service
        self.setWindowTitle("Orbit - Görsel Profil ve Halkalar Editörü")
        self.resize(920, 620)
        self.current_profile: Optional[Profile] = None
        self._init_ui()
        self._load_profiles()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)

        # 1. Left Side: Profiles List
        left_box = QGroupBox("Profil Listesi")
        left_layout = QVBoxLayout(left_box)

        self.profile_list_widget = QListWidget()
        self.profile_list_widget.currentTextChanged.connect(self._on_profile_selected)
        left_layout.addWidget(self.profile_list_widget)

        btn_bar = QHBoxLayout()
        new_prof_btn = QPushButton("Yeni Profil")
        new_prof_btn.clicked.connect(self._on_new_profile)

        dup_prof_btn = QPushButton("Kopyala")
        dup_prof_btn.clicked.connect(self._on_duplicate_profile)

        del_prof_btn = QPushButton("Sil")
        del_prof_btn.setStyleSheet("background-color: #E74C3C; color: #ffffff;")
        del_prof_btn.clicked.connect(self._on_delete_profile)

        btn_bar.addWidget(new_prof_btn)
        btn_bar.addWidget(dup_prof_btn)
        btn_bar.addWidget(del_prof_btn)
        left_layout.addLayout(btn_bar)

        splitter.addWidget(left_box)

        # 2. Right Side: Profile Details & Slice Items Editor
        right_box = QGroupBox("Profil Detayları & Dilimler")
        right_layout = QVBoxLayout(right_box)

        form_layout = QFormLayout()
        self.prof_name_input = QLineEdit()
        self.prof_desc_input = QLineEdit()
        self.prof_color_input = QLineEdit("#2ED573")
        self.prof_apps_input = QLineEdit()
        self.prof_apps_input.setPlaceholderText("Örn: code.exe, chrome.exe, photoshop.exe")

        form_layout.addRow("Profil Adı:", self.prof_name_input)
        form_layout.addRow("Açıklama:", self.prof_desc_input)
        form_layout.addRow("Vurgu Rengi:", self.prof_color_input)
        form_layout.addRow("Bağlı Uygulamalar (.exe):", self.prof_apps_input)

        right_layout.addLayout(form_layout)

        # Slices List
        slice_label = QLabel("Halka Dilimleri (Slices):")
        slice_label.setFont(QFont("Outfit", 10, QFont.Bold))
        right_layout.addWidget(slice_label)

        self.slice_list_widget = QListWidget()
        right_layout.addWidget(self.slice_list_widget)

        slice_btn_bar = QHBoxLayout()
        add_slice_btn = QPushButton("Dilim Ekle")
        add_slice_btn.clicked.connect(self._on_add_slice)
        edit_slice_btn = QPushButton("Düzenle")
        edit_slice_btn.clicked.connect(self._on_edit_slice)
        del_slice_btn = QPushButton("Dilim Sil")
        del_slice_btn.clicked.connect(self._on_delete_slice)

        slice_btn_bar.addWidget(add_slice_btn)
        slice_btn_bar.addWidget(edit_slice_btn)
        slice_btn_bar.addWidget(del_slice_btn)
        right_layout.addLayout(slice_btn_bar)

        # Save Button
        save_prof_btn = QPushButton("Profili Kaydet & Uygula")
        save_prof_btn.setStyleSheet("background-color: #2ED573; color: #0A140F; font-weight: bold; padding: 10px;")
        save_prof_btn.clicked.connect(self._on_save_profile)
        right_layout.addWidget(save_prof_btn)

        splitter.addWidget(right_box)
        splitter.setSizes([280, 640])

        main_layout.addWidget(splitter)

    def _load_profiles(self) -> None:
        self.profile_list_widget.clear()
        names = self.profile_service.list_profiles()
        for n in names:
            self.profile_list_widget.addItem(n)

    def _on_profile_selected(self, name: str) -> None:
        if not name:
            return
        key = name.lower()
        if key in self.profile_service._profiles:
            prof = self.profile_service._profiles[key]
            self.current_profile = prof
            self.prof_name_input.setText(prof.name)
            self.prof_desc_input.setText(prof.description)
            self.prof_color_input.setText(prof.accent_color)
            self.prof_apps_input.setText(", ".join(prof.app_bindings))

            self._update_slice_list()

    def _update_slice_list(self) -> None:
        self.slice_list_widget.clear()
        if self.current_profile:
            for item in self.current_profile.items:
                act_type = type(item.action).__name__
                if isinstance(item.action, SubRingAction):
                    count = len(item.action.sub_items)
                    text = f"[{item.icon}] {item.label}  ➔ Alt Halka ({count} eleman)"
                else:
                    text = f"[{item.icon}] {item.label}  ({act_type})"
                self.slice_list_widget.addItem(text)

    def _on_new_profile(self) -> None:
        new_prof = Profile("Yeni Profil", [], accent_color="#2ED573", description="Özel Profil")
        self.profile_service.save_profile("yeni_profil", new_prof)
        self._load_profiles()

    def _on_duplicate_profile(self) -> None:
        if not self.current_profile:
            return
        dup_name = f"{self.current_profile.name} (Kopya)"
        dup_key = f"{self.current_profile.name.lower()}_kopya"
        dup_prof = Profile(
            dup_name,
            [SliceItem.from_dict(it.to_dict()) for it in self.current_profile.items],
            accent_color=self.current_profile.accent_color,
            description=f"{self.current_profile.description} (Kopyalandı)",
            app_bindings=self.current_profile.app_bindings.copy()
        )
        self.profile_service.save_profile(dup_key, dup_prof)
        self._load_profiles()

    def _on_delete_profile(self) -> None:
        if not self.current_profile or self.current_profile.name.lower() in ("varsayılan", "default"):
            QMessageBox.warning(self, "Uyarı", "Varsayılan profil silinemez!")
            return

        reply = QMessageBox.question(
            self, "Profil Silme Onayı",
            f"'{self.current_profile.name}' profilini silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            key = self.current_profile.name.lower()
            filepath = self.profile_service.profiles_dir / f"{key}.json"
            if filepath.exists():
                filepath.unlink()
            if key in self.profile_service._profiles:
                del self.profile_service._profiles[key]
            self.current_profile = None
            self._load_profiles()

    def _on_add_slice(self) -> None:
        if not self.current_profile:
            return
        dlg = SliceItemDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            new_item = dlg.get_slice_item()
            self.current_profile.items.append(new_item)
            self._update_slice_list()

    def _on_edit_slice(self) -> None:
        row = self.slice_list_widget.currentRow()
        if not self.current_profile or row < 0 or row >= len(self.current_profile.items):
            return
        old_item = self.current_profile.items[row]
        dlg = SliceItemDialog(item=old_item, parent=self)
        if dlg.exec() == QDialog.Accepted:
            updated_item = dlg.get_slice_item()
            self.current_profile.items[row] = updated_item
            self._update_slice_list()

    def _on_delete_slice(self) -> None:
        row = self.slice_list_widget.currentRow()
        if not self.current_profile or row < 0 or row >= len(self.current_profile.items):
            return
        del self.current_profile.items[row]
        self._update_slice_list()

    def _on_save_profile(self) -> None:
        if not self.current_profile:
            return

        name = self.prof_name_input.text().strip() or self.current_profile.name
        desc = self.prof_desc_input.text().strip()
        color = self.prof_color_input.text().strip()
        apps_raw = self.prof_apps_input.text().strip()
        apps = [a.strip().lower() for a in apps_raw.split(",") if a.strip()]

        self.current_profile.name = name
        self.current_profile.description = desc
        self.current_profile.accent_color = color
        self.current_profile.app_bindings = apps

        key = name.lower()
        self.profile_service.save_profile(key, self.current_profile)
        self.profile_service.load_all_profiles()

        QMessageBox.information(self, "Başarılı", f"'{name}' profili başarıyla kaydedildi ve uygulandı!")
        self.profiles_updated.emit()
