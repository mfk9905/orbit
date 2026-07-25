"""
Profile model representing radial menu layout, items, and action mappings.
"""

from typing import List, Dict, Any
from app.models.base_action import BaseAction
from app.models.actions import action_factory


class SliceItem:
    """Represents a single slice segment in the radial menu."""

    def __init__(
        self,
        slice_id: str,
        label: str,
        icon: str,
        color: str,
        action: BaseAction,
        tooltip: str = ""
    ) -> None:
        self.slice_id = slice_id
        self.label = label
        self.icon = icon
        self.color = color
        self.action = action
        self.tooltip = tooltip or label

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.slice_id,
            "label": self.label,
            "icon": self.icon,
            "color": self.color,
            "tooltip": self.tooltip,
            "action": self.action.to_dict()
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SliceItem":
        action_data = data.get("action", {})
        action_inst = action_factory(action_data)
        return SliceItem(
            slice_id=data.get("id", "slice"),
            label=data.get("label", "Item"),
            icon=data.get("icon", "grid"),
            color=data.get("color", "#2ED573"),
            action=action_inst,
            tooltip=data.get("tooltip", "")
        )


class Profile:
    """Contains radial menu configuration, slice items, and active layout."""

    def __init__(
        self,
        name: str,
        items: List[SliceItem],
        accent_color: str = "#2ED573",
        description: str = "",
        app_bindings: List[str] | None = None
    ) -> None:
        self.name = name
        self.items = items
        self.accent_color = accent_color
        self.description = description
        self.app_bindings = [app.lower() for app in (app_bindings or [])]

    @property
    def slice_count(self) -> int:
        return len(self.items)

    def matches_app(self, app_exe: str) -> bool:
        """Returns True if this profile is bound to the given app executable name."""
        if not app_exe:
            return False
        clean_exe = app_exe.lower().strip()
        for bound_app in self.app_bindings:
            if clean_exe == bound_app or clean_exe.replace(".exe", "") == bound_app.replace(".exe", ""):
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "accent_color": self.accent_color,
            "description": self.description,
            "app_bindings": self.app_bindings,
            "items": [item.to_dict() for item in self.items]
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Profile":
        items = [SliceItem.from_dict(item_data) for item_data in data.get("items", [])]
        return Profile(
            name=data.get("name", "Default"),
            items=items,
            accent_color=data.get("accent_color", "#2ED573"),
            description=data.get("description", ""),
            app_bindings=data.get("app_bindings", [])
        )
