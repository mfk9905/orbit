import time
import json
from typing import Any, Dict, List
from PySide6.QtGui import QGuiApplication
from pynput.keyboard import Controller, Key
from app.models.base_action import BaseAction
from app.models.actions.sub_ring_action import SubRingAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.smart_text")


class SmartTextAction(BaseAction):
    """
    Copies active text selection (Ctrl+C), transforms it based on mode 
    (UPPERCASE, lowercase, Title Case, JSON format, Strip), and pastes it back (Ctrl+V).
    """

    def execute(self) -> bool:
        mode = self.params.get("mode", "uppercase").lower()
        logger.info(f"Executing SmartTextAction with mode: '{mode}'")

        try:
            keyboard = Controller()
            cb = QGuiApplication.clipboard()

            # 1. Simulate Ctrl+C to grab selected text into clipboard
            with keyboard.pressed(Key.ctrl):
                keyboard.press('c')
                keyboard.release('c')

            time.sleep(0.06)

            text = cb.text() if cb else ""
            if not text:
                logger.warning("No text selection or clipboard content found.")
                return False

            # 2. Transform text based on mode
            transformed = text
            if mode == "uppercase":
                transformed = text.upper()
            elif mode == "lowercase":
                transformed = text.lower()
            elif mode == "titlecase":
                transformed = text.title()
            elif mode == "strip":
                transformed = "\n".join(line.strip() for line in text.splitlines() if line.strip())
            elif mode in ("json", "json_format"):
                try:
                    obj = json.loads(text)
                    transformed = json.dumps(obj, indent=2, ensure_ascii=False)
                except Exception as je:
                    logger.warning(f"Could not parse text as JSON: {je}")
                    transformed = text
            elif mode == "summarize":
                transformed = f"[Özet Talebi]: {text}"

            # 3. Put transformed text into clipboard
            if cb:
                cb.setText(transformed)

            time.sleep(0.04)

            # 4. Simulate Ctrl+V to paste back transformed text
            with keyboard.pressed(Key.ctrl):
                keyboard.press('v')
                keyboard.release('v')

            logger.info(f"SmartTextAction '{mode}' executed successfully ({len(transformed)} chars)")
            return True
        except Exception as e:
            logger.error(f"Failed to execute SmartTextAction '{mode}': {e}")
            return False


class SmartTextSubRingAction(SubRingAction):
    """SubRingAction offering preset smart text manipulation tools."""

    def __init__(self, action_id: str, label: str = "Akıllı Metin İşlemleri", icon: str = "edit", params: Dict[str, Any] | None = None, items: List[Any] | None = None) -> None:
        super().__init__(action_id, label, icon, params, items)

    @property
    def sub_items(self):
        from app.models.profile import SliceItem

        return [
            SliceItem(
                slice_id="st_upper",
                label="BÜYÜK HARF",
                icon="type",
                color="#2ED573",
                action=SmartTextAction("act_st_upper", "BÜYÜK HARF", icon="type", params={"mode": "uppercase"}),
                tooltip="Seçili metni tamamen BÜYÜK HARFE çevirir"
            ),
            SliceItem(
                slice_id="st_lower",
                label="küçük harf",
                icon="type",
                color="#2ED573",
                action=SmartTextAction("act_st_lower", "küçük harf", icon="type", params={"mode": "lowercase"}),
                tooltip="Seçili metni tamamen küçük harfe çevirir"
            ),
            SliceItem(
                slice_id="st_title",
                label="Baş Harfler Büyük",
                icon="type",
                color="#2ED573",
                action=SmartTextAction("act_st_title", "Baş Harfler Büyük", icon="type", params={"mode": "titlecase"}),
                tooltip="Kelime baş harflerini Büyük Harf Yapar"
            ),
            SliceItem(
                slice_id="st_strip",
                label="Metni Temizle",
                icon="scissors",
                color="#FFA502",
                action=SmartTextAction("act_st_strip", "Metni Temizle", icon="scissors", params={"mode": "strip"}),
                tooltip="Gereksiz girinti ve boş satırları temizler"
            ),
            SliceItem(
                slice_id="st_json",
                label="JSON Düzenle",
                icon="code",
                color="#00F2FE",
                action=SmartTextAction("act_st_json", "JSON Düzenle", icon="code", params={"mode": "json_format"}),
                tooltip="Karışık JSON metnini girintili düzenli hale getirir"
            )
        ]

    @sub_items.setter
    def sub_items(self, val):
        pass
