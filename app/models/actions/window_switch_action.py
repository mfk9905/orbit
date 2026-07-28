from typing import Any, Dict, List
from app.models.base_action import BaseAction
from app.models.actions.sub_ring_action import SubRingAction
from app.services.active_window_service import ActiveWindowService
from app.core.logging.logger import get_logger

logger = get_logger("orbit.actions.window_switch")


class WindowSwitchAction(BaseAction):
    """Brings a specific open desktop window (by hwnd) to the foreground."""

    def execute(self) -> bool:
        hwnd = self.params.get("hwnd", 0)
        if not hwnd:
            logger.error(f"WindowSwitchAction '{self.label}' missing 'hwnd' parameter.")
            return False

        logger.info(f"Switching focus to window: '{self.label}' (hwnd={hwnd})")
        return ActiveWindowService.activate_window(int(hwnd))


class WindowSwitcherSubRingAction(SubRingAction):
    """SubRingAction that dynamically populates open desktop windows as radial slices."""

    def __init__(self, action_id: str, label: str = "Açık Pencereler", icon: str = "layers", params: Dict[str, Any] | None = None, items: List[Any] | None = None) -> None:
        super().__init__(action_id, label, icon, params, items)

    @property
    def sub_items(self):
        from app.models.profile import SliceItem

        windows = ActiveWindowService.get_open_windows()
        if not windows:
            # Placeholder item if no open window detected
            return [
                SliceItem(
                    slice_id="win_empty",
                    label="Pencere Bulunamadı",
                    icon="layout",
                    color="#747D8C",
                    action=WindowSwitchAction("act_win_empty", "Boş", params={"hwnd": 0}),
                    tooltip="Açık pencere tespit edilemedi"
                )
            ]

        # Icon and color mapping table based on process executable name
        icon_map = {
            "code.exe": ("code", "#007ACC"),
            "chrome.exe": ("globe", "#4285F4"),
            "msedge.exe": ("globe", "#0078D7"),
            "firefox.exe": ("globe", "#FF7139"),
            "spotify.exe": ("music", "#1DB954"),
            "cmd.exe": ("terminal", "#2ED573"),
            "powershell.exe": ("terminal", "#5352ED"),
            "windowsterminal.exe": ("terminal", "#2ED573"),
            "wt.exe": ("terminal", "#2ED573"),
            "explorer.exe": ("folder", "#FFA502"),
            "notepad.exe": ("copy", "#FF4757"),
        }

        slice_items = []
        # Limit to max 8 open windows for optimal radial menu layout
        for i, (hwnd, exe_name, title) in enumerate(windows[:8]):
            icon_name, color = icon_map.get(exe_name, ("layout", "#9B59B6"))

            clean_title = " ".join(title.split())
            short_label = clean_title[:16] + "..." if len(clean_title) > 16 else clean_title

            slice_item = SliceItem(
                slice_id=f"win_slice_{i}",
                label=short_label,
                icon=icon_name,
                color=color,
                action=WindowSwitchAction(
                    action_id=f"act_win_switch_{i}",
                    label=short_label,
                    icon=icon_name,
                    params={"hwnd": hwnd}
                ),
                tooltip=f"Pencereye Odaklan: {clean_title}"
            )
            slice_items.append(slice_item)

        return slice_items

    @sub_items.setter
    def sub_items(self, val):
        pass
