"""
Slice & Action Editor Modal Dialog for Orbit (Türkçe - Son Kullanıcı Dostu).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QColorDialog,
    QPushButton, QHBoxLayout, QLabel, QDialogButtonBox, QWidget, QGroupBox
)
from PySide6.QtGui import QColor, QFont
from typing import Optional, Dict, Any
from app.models.profile import SliceItem
from app.models.actions import (
    AppAction, UrlAction, ShellAction, ShortcutAction, TextAction, action_factory
)


class SliceEditorDialog(QDialog):
    """Modal dialog for creating or editing a radial slice item in simple end-user language."""

    PRESET_TEMPLATES = [
        ("Özel Ayar Yap", "", "", ""),
        ("Google'da Ara / Web Sayfası Aç", "UrlAction", "https://google.com", "globe"),
        ("İnternet Tarayıcısı Başlat", "AppAction", "google-chrome || firefox || firefox-esr", "globe"),
        ("VS Code Düzenleyici Aç", "AppAction", "code", "code"),
        ("Sistem Terminalini Aç", "AppAction", "konsole || gnome-terminal || xterm", "terminal"),
        ("Metin Kopyala (Ctrl+C)", "ShortcutAction", "ctrl+c", "copy"),
        ("Metin Yapıştır (Ctrl+V)", "ShortcutAction", "ctrl+v", "clipboard"),
        ("Sistem İzleyici / Görev Yöneticisi", "ShellAction", "kinfocenter || gnome-system-monitor || htop", "cpu"),
        ("Otomatik Metin Yazdır", "TextAction", "Orbit Menüden Selamlar!", "type"),
    ]

    def __init__(self, slice_item: Optional[SliceItem] = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Dilim ve Eylem Düzenleyici")
        self.setMinimumWidth(500)

        self.slice_item = slice_item
        self._selected_color = slice_item.color if slice_item else "#2ED573"

        self._init_ui()
        if slice_item:
            self._populate_fields(slice_item)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Template Selection Row
        tpl_group = QGroupBox("Hazır Eylem Şablonları (İsteğe Bağlı)")
        tpl_layout = QVBoxLayout(tpl_group)
        self.cmb_template = QComboBox()
        self.cmb_template.addItems([t[0] for t in self.PRESET_TEMPLATES])
        self.cmb_template.currentIndexChanged.connect(self._on_template_selected)
        tpl_layout.addWidget(self.cmb_template)
        layout.addWidget(tpl_group)

        form = QFormLayout()

        self.txt_label = QLineEdit()
        self.txt_label.setPlaceholderText("Örn: İnternet, Kopyala, Kod Editörü")
        form.addRow("Dilim Adı (Başlık):", self.txt_label)

        self.txt_tooltip = QLineEdit()
        self.txt_tooltip.setPlaceholderText("Fare üstüne geldiğinde görünen kısa açıklama")
        form.addRow("Açıklama (İpucu):", self.txt_tooltip)

        self.txt_icon = QLineEdit()
        self.txt_icon.setPlaceholderText("Örn: globe, terminal, code, copy")
        form.addRow("Simge (İkon) Adı:", self.txt_icon)

        # Color Picker Row
        color_layout = QHBoxLayout()
        self.lbl_color_preview = QLabel("   ")
        self.lbl_color_preview.setStyleSheet(f"background-color: {self._selected_color}; border-radius: 4px; border: 1px solid #555;")
        self.btn_choose_color = QPushButton("Renk Seç")
        self.btn_choose_color.clicked.connect(self._choose_color)
        color_layout.addWidget(self.lbl_color_preview)
        color_layout.addWidget(self.btn_choose_color)
        color_layout.addStretch()
        form.addRow("Dilim Vurgu Rengi:", color_layout)

        # Action Type Selector
        self.cmb_action_type = QComboBox()
        self.cmb_action_type.addItems([
            "Uygulama / Program Başlat",
            "İnternet Sayfası (Web Bağlantısı) Aç",
            "Sistem Komutu Çalıştır",
            "Klavye Kısayolu Gönder (Örn: Ctrl+C)",
            "Otomatik Metin Yazdır"
        ])
        self.cmb_action_type.currentIndexChanged.connect(self._on_action_type_changed)
        form.addRow("Eylem Türü:", self.cmb_action_type)

        # Dynamic Action Parameter
        self.lbl_param = QLabel("Hedef Adres / Komut:")
        self.txt_param = QLineEdit()
        form.addRow(self.lbl_param, self.txt_param)

        layout.addLayout(form)

        # Dialog Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Kaydet")
        button_box.button(QDialogButtonBox.Cancel).setText("Vazgeç")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._on_action_type_changed(0)

    def _on_template_selected(self, index: int) -> None:
        if index > 0 and index < len(self.PRESET_TEMPLATES):
            name, act_type, param_val, icon_val = self.PRESET_TEMPLATES[index]
            self.txt_label.setText(name.split(" (")[0])
            self.txt_tooltip.setText(name)
            self.txt_icon.setText(icon_val)

            type_map = {
                "AppAction": 0,
                "UrlAction": 1,
                "ShellAction": 2,
                "ShortcutAction": 3,
                "TextAction": 4
            }
            if act_type in type_map:
                self.cmb_action_type.setCurrentIndex(type_map[act_type])
            self.txt_param.setText(param_val)

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._selected_color), self, "Dilim Rengi Seçin")
        if color.isValid():
            self._selected_color = color.name()
            self.lbl_color_preview.setStyleSheet(f"background-color: {self._selected_color}; border-radius: 4px; border: 1px solid #555;")

    def _on_action_type_changed(self, index: int) -> None:
        labels = [
            ("Uygulama Adı / Komut:", "google-chrome veya code"),
            ("İnternet Adresi (URL):", "https://google.com"),
            ("Sistem Komutu:", "htop veya top"),
            ("Tuş Kombinasyonu:", "ctrl+c veya alt+tab"),
            ("Yazılacak Metin:", "Merhaba Orbit!")
        ]
        if 0 <= index < len(labels):
            lbl, ph = labels[index]
            self.lbl_param.setText(lbl)
            self.txt_param.setPlaceholderText(ph)

    def _populate_fields(self, item: SliceItem) -> None:
        self.txt_label.setText(item.label)
        self.txt_tooltip.setText(item.tooltip)
        self.txt_icon.setText(item.icon)
        self._selected_color = item.color
        self.lbl_color_preview.setStyleSheet(f"background-color: {self._selected_color}; border-radius: 4px; border: 1px solid #555;")

        action_type = item.action.__class__.__name__
        type_mapping = {
            "AppAction": 0,
            "UrlAction": 1,
            "ShellAction": 2,
            "ShortcutAction": 3,
            "TextAction": 4
        }
        idx = type_mapping.get(action_type, 0)
        self.cmb_action_type.setCurrentIndex(idx)

        param_mapping = {
            "AppAction": "command",
            "UrlAction": "url",
            "ShellAction": "command",
            "ShortcutAction": "keys",
            "TextAction": "text"
        }
        param_key = param_mapping.get(action_type, "command")
        self.txt_param.setText(str(item.action.params.get(param_key, "")))

    def get_slice_item(self) -> SliceItem:
        """Constructs SliceItem object from dialog field values."""
        label = self.txt_label.text().strip() or "Dilim"
        tooltip = self.txt_tooltip.text().strip() or label
        icon = self.txt_icon.text().strip() or "grid"
        color = self._selected_color

        idx = self.cmb_action_type.currentIndex()
        type_str_map = ["AppAction", "UrlAction", "ShellAction", "ShortcutAction", "TextAction"]
        param_key_map = ["command", "url", "command", "keys", "text"]

        action_type = type_str_map[idx]
        param_key = param_key_map[idx]
        param_val = self.txt_param.text().strip()

        action_id = self.slice_item.action.action_id if self.slice_item else f"action_{label.lower()}"
        slice_id = self.slice_item.slice_id if self.slice_item else f"slice_{label.lower()}"

        action_inst = action_factory({
            "type": action_type,
            "id": action_id,
            "label": label,
            "icon": icon,
            "params": {param_key: param_val}
        })

        return SliceItem(
            slice_id=slice_id,
            label=label,
            icon=icon,
            color=color,
            action=action_inst,
            tooltip=tooltip
        )
