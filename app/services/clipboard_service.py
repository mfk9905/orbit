from typing import List
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication
from app.models.profile import SliceItem
from app.models.actions import ClipboardAction, TextAction
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

    def clear_history(self) -> None:
        """Clears captured clipboard history."""
        self.history.clear()
        logger.info("Clipboard history cleared.")

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
            # Clean up single line summary for slice label
            clean_text = " ".join(text.split())
            short_label = clean_text[:18] + "..." if len(clean_text) > 18 else clean_text
            slice_item = SliceItem(
                slice_id=f"clip_{i}",
                label=short_label,
                icon="copy",
                color="#FFA502",
                action=ClipboardAction(
                    action_id=f"act_clip_{i}",
                    label=short_label,
                    icon="copy",
                    params={"text": text}
                ),
                tooltip=f"Panodan Yapıştır: {clean_text[:50]}"
            )
            items.append(slice_item)
        return items

