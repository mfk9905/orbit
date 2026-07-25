from typing import Any, Dict, List
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.sub_ring")


class SubRingAction(BaseAction):
    """Action that opens a nested sub-ring radial menu."""

    def __init__(self, action_id: str, label: str, icon: str = "", params: Dict[str, Any] | None = None, items: List[Any] | None = None) -> None:
        super().__init__(action_id, label, icon, params or {})
        self.sub_items = items or []

    def execute(self) -> bool:
        logger.info(f"SubRingAction '{self.label}' triggered ({len(self.sub_items)} sub-items)")
        return True

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["items"] = [item.to_dict() if hasattr(item, "to_dict") else item for item in self.sub_items]
        return d


class ClipboardSubRingAction(SubRingAction):
    """SubRingAction that dynamically populates items from ClipboardService."""

    def __init__(self, action_id: str, label: str, icon: str = "", params: Dict[str, Any] | None = None, items: List[Any] | None = None) -> None:
        super().__init__(action_id, label, icon, params, items)

    @property
    def sub_items(self):
        from app.services.clipboard_service import ClipboardService
        return ClipboardService.get_instance().get_slice_items()

    @sub_items.setter
    def sub_items(self, val):
        pass
