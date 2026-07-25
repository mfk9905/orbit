"""
Radial Menu ViewModel (MVVM Architecture).
Encapsulates state logic, slice geometry calculations, and hover detection.
"""

import math
from typing import List, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QPointF
from app.models.profile import Profile, SliceItem


class RadialMenuViewModel(QObject):
    """ViewModel maintaining state and mathematics for radial slices and sub-rings."""

    slice_hovered = Signal(int)  # Emits hovered slice index (-1 if none)
    profile_updated = Signal()

    def __init__(self, radius: float = 180.0, inner_radius: float = 55.0) -> None:
        super().__init__()
        self._profile: Optional[Profile] = None
        self._default_items: List[SliceItem] = []
        self._items_override: Optional[List[SliceItem]] = None
        self._nav_stack: List[Tuple[str, List[SliceItem]]] = []
        self._center = QPointF(0, 0)
        self._radius = radius
        self._inner_radius = inner_radius
        self._hovered_index: int = -1
        self._center_hovered: bool = False

    def set_default_items(self, items: List[SliceItem]) -> None:
        """Sets fallback items for default general profile."""
        self._default_items = items

    @property
    def default_items(self) -> List[SliceItem]:
        return self._default_items

    @property
    def is_app_profile(self) -> bool:
        if not self._profile:
            return False
        return self._profile.name.lower() not in ("varsayılan", "default")

    def set_profile(self, profile: Profile) -> None:
        """Sets active profile data and resets navigation stack."""
        self._profile = profile
        self._items_override = None
        self._nav_stack.clear()
        self._hovered_index = -1
        self._center_hovered = False
        self.profile_updated.emit()


    def push_sub_ring(self, label: str, items: List[SliceItem]) -> None:
        """Navigates into a sub-ring."""
        current = self.items.copy()
        self._nav_stack.append((label, current))
        self._items_override = items
        self._hovered_index = -1
        self._center_hovered = False
        self.profile_updated.emit()

    def pop_sub_ring(self) -> bool:
        """Pops back to parent ring. Returns True if navigated back."""
        if self._nav_stack:
            _, parent_items = self._nav_stack.pop()
            self._items_override = parent_items
            self._hovered_index = -1
            self._center_hovered = False
            self.profile_updated.emit()
            return True
        return False

    def reset_navigation(self) -> None:
        """Resets back to root ring."""
        if self._nav_stack:
            self._nav_stack.clear()
            self._items_override = None
            self._hovered_index = -1
            self._center_hovered = False
            self.profile_updated.emit()

    @property
    def is_at_root(self) -> bool:
        return len(self._nav_stack) == 0

    @property
    def is_center_hovered(self) -> bool:
        return self._center_hovered

    def set_center(self, x: float, y: float) -> None:
        """Sets screen coordinates of menu center."""
        self._center = QPointF(x, y)

    def set_radius(self, radius: float, inner_radius: float = 55.0) -> None:
        """Dynamically update menu radius."""
        self._radius = radius
        self._inner_radius = inner_radius
        self.profile_updated.emit()

    @property
    def items(self) -> List[SliceItem]:
        if self._items_override is not None:
            return self._items_override
        return self._profile.items if self._profile else []

    @property
    def slice_count(self) -> int:
        return len(self.items)

    @property
    def hovered_index(self) -> int:
        return self._hovered_index

    @property
    def hovered_item(self) -> Optional[SliceItem]:
        if 0 <= self._hovered_index < len(self.items):
            return self.items[self._hovered_index]
        return None

    def update_cursor_position(self, cursor_x: float, cursor_y: float) -> Optional[int]:
        """Calculates which slice or center core is under cursor."""
        if not self.items:
            self._set_hovered(-1)
            self._center_hovered = False
            return -1

        dx = cursor_x - self._center.x()
        dy = cursor_y - self._center.y()
        distance = math.hypot(dx, dy)

        # Center core hover detection
        if distance < self._inner_radius:
            if not self._center_hovered:
                self._center_hovered = True
                self.profile_updated.emit()
            self._set_hovered(-1)
            return -1
        else:
            if self._center_hovered:
                self._center_hovered = False
                self.profile_updated.emit()

        # Ignore cursor if too far outside
        if distance > self._radius * 1.5:
            self._set_hovered(-1)
            return -1

        # Angle in degrees [0, 360), 0 is Top (12 o'clock), clockwise
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        norm_angle = (angle_deg + 90) % 360

        slice_angle = 360.0 / self.slice_count
        index = int(norm_angle // slice_angle) % self.slice_count

        self._set_hovered(index)
        return index

    def _set_hovered(self, index: int) -> None:
        if self._hovered_index != index:
            self._hovered_index = index
            self.slice_hovered.emit(index)

    def get_slice_angles(self, index: int) -> Tuple[float, float]:
        """Returns start_angle and span_angle in degrees for QPainter (0 deg is 3 o'clock)."""
        count = self.slice_count
        if count == 0:
            return 0.0, 0.0

        span_angle = 360.0 / count
        start_angle = 90.0 - (index * span_angle) - span_angle
        return start_angle, span_angle

