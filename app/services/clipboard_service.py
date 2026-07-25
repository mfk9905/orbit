from typing import List
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication
from app.models.profile import SliceItem
from app.models.actions import TextAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.services.clipboard")


class ClipboardService:
    _instance = None

    def __init__(self) -> None:
        self.history: List[str] = []
        self.max_items = 6
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "ClipboardService":
        if cls._instance is None:
            cls._instance = ClipboardService()
        return cls._instance

    def init_clipboard(self) -> None:
        if self._initialized:
            return
        
        app = QApplication.instance()
        if app:
            cb = QGuiApplication.clipboard()
            cb.dataChanged.connect(self._on_clipboard_changed)
            self._initialized = True
            logger.info("ClipboardService initialized and connected to QClipboard.")

    def _on_clipboard_changed(self) -> None:
        try:
            cb = QGuiApplication.clipboard()
            text = cb.text()
            if text and text.strip():
                # Avoid duplicate if it's already the most recent
                if not self.history or self.history[0] != text:
                    self.history.insert(0, text)
                    if len(self.history) > self.max_items:
                        self.history.pop()
                    logger.info(f"Clipboard captured: '{text[:20]}...'")
        except Exception as e:
            logger.error(f"Error reading clipboard: {e}")

    def get_slice_items(self) -> List[SliceItem]:
        items = []
        if not self.history:
            # Placeholder item if history is empty
            item = SliceItem(
                slice_id="clip_empty",
                label="Pano Boş",
                icon="clipboard",
                color="#747D8C",
                action=TextAction("act_clip_empty", "Boş", params={"text": ""}),
                tooltip="Panoda henüz kopyalanmış öğe yok"
            )
            items.append(item)
            return items

        for i, text in enumerate(self.history):
            short_text = text[:12] + "..." if len(text) > 12 else text
            slice_item = SliceItem(
                slice_id=f"clip_{i}",
                label=short_text,
                icon="copy",
                color="#FFA502",
                action=TextAction(
                    action_id=f"act_clip_{i}",
                    label=short_text,
                    icon="copy",
                    params={"text": text}
                ),
                tooltip=f"Panodan Yazdır: {text[:40]}"
            )
            items.append(slice_item)
        return items
