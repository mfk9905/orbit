from typing import Any, Dict
from app.models.base_action import BaseAction
from app.models.actions.app_action import AppAction
from app.models.actions.url_action import UrlAction
from app.models.actions.shell_action import ShellAction
from app.models.actions.shortcut_action import ShortcutAction
from app.models.actions.text_action import TextAction
from app.models.actions.sub_ring_action import SubRingAction, ClipboardSubRingAction
from app.models.actions.macro_action import MacroAction
from app.models.actions.wheel_action import WheelAction
from app.models.actions.window_control_action import WindowControlAction
from app.models.actions.keyboard_action import KeyboardAction


def action_factory(data: Dict[str, Any]) -> BaseAction:
    """Instantiates concrete BaseAction derived instance from dict definition."""
    action_type = data.get("type", "AppAction")
    action_id = data.get("id", "action_id")
    label = data.get("label", "Action")
    icon = data.get("icon", "")
    params = data.get("params", {})

    if action_type == "SubRingAction":
        from app.models.profile import SliceItem
        raw_items = data.get("items", [])
        sub_items = [SliceItem.from_dict(item_data) for item_data in raw_items]
        return SubRingAction(action_id=action_id, label=label, icon=icon, params=params, items=sub_items)

    if action_type == "ClipboardSubRingAction":
        return ClipboardSubRingAction(action_id=action_id, label=label, icon=icon, params=params)

    mapping = {
        "AppAction": AppAction,
        "UrlAction": UrlAction,
        "ShellAction": ShellAction,
        "ShortcutAction": ShortcutAction,
        "TextAction": TextAction,
        "MacroAction": MacroAction,
        "WheelAction": WheelAction,
        "WindowControlAction": WindowControlAction,
        "KeyboardAction": KeyboardAction,
        "ClipboardSubRingAction": ClipboardSubRingAction,
    }

    cls = mapping.get(action_type, AppAction)
    return cls(action_id=action_id, label=label, icon=icon, params=params)
