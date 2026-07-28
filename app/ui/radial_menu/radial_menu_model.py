"""
Radial Menu ViewModel (MVVM Architecture).
Encapsulates state logic, slice geometry calculations, and hover detection.
"""

from app.core.config.settings import logger
import math
from typing import List, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QPointF
from app.models.profile import Profile, SliceItem


class RadialMenuViewModel(QObject):
    """ViewModel maintaining state and mathematics for nautilus spiral radial slices and sub-rings."""

    slice_hovered = Signal(int)  # Emits hovered slice index of active level (-1 if none)
    profile_updated = Signal()

    def __init__(self, radius: float = 180.0, inner_radius: float = 38.0) -> None:
        super().__init__()
        self._profile: Optional[Profile] = None
        self._default_items: List[SliceItem] = []
        # _nav_stack holds sub-rings: list of dicts {"label": str, "items": List[SliceItem], "parent_index": int}
        self._nav_stack: List[dict] = []
        self._center = QPointF(0, 0)
        self._radius = radius
        self._inner_radius = inner_radius
        self._hovered_level: int = 0
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
        self._nav_stack.clear()
        self._hovered_level = 0
        self._hovered_index = -1
        self._center_hovered = False
        self.profile_updated.emit()

    def push_sub_ring(self, label: str, items: List[SliceItem], parent_index: int = -1) -> bool:
        """Navigates into a sub-ring, opening a new outer arc layer."""
        target_parent = parent_index if parent_index >= 0 else self._hovered_index
        
        # Check if clicking on an already open parent slice -> toggle/close sub-ring
        if self._nav_stack:
            last_sub = self._nav_stack[-1]
            if last_sub.get("parent_index") == target_parent and len(self._nav_stack) == self._hovered_level:
                logger.info(f"Sub-ring '{label}' is already open. Toggling back.")
                return self.pop_sub_ring()

        # Truncate any sub-rings deeper than current hovered level
        if self._hovered_level < len(self._nav_stack):
            self._nav_stack = self._nav_stack[:self._hovered_level]

        self._nav_stack.append({
            "label": label,
            "items": items,
            "parent_index": target_parent
        })
        self._hovered_level = len(self._nav_stack)
        self._hovered_index = -1
        self._center_hovered = False
        self.profile_updated.emit()
        return True

    def pop_sub_ring(self) -> bool:
        """Pops back to parent ring layer. Returns True if navigated back."""
        if self._nav_stack:
            self._nav_stack.pop()
            self._hovered_level = len(self._nav_stack)
            self._hovered_index = -1
            self._center_hovered = False
            self.profile_updated.emit()
            return True
        return False

    def reset_navigation(self) -> None:
        """Resets back to root ring layer."""
        if self._nav_stack:
            self._nav_stack.clear()
            self._hovered_level = 0
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

    def set_radius(self, radius: float, inner_radius: float = 38.0) -> None:
        """Dynamically update menu radius."""
        self._radius = radius
        self._inner_radius = inner_radius
        self.profile_updated.emit()

    @property
    def root_items(self) -> List[SliceItem]:
        return self._profile.items if self._profile else []

    @property
    def items(self) -> List[SliceItem]:
        """Returns items of active top-most navigation level."""
        if self._nav_stack:
            return self._nav_stack[-1]["items"]
        return self.root_items

    @property
    def slice_count(self) -> int:
        return len(self.items)

    @property
    def hovered_level(self) -> int:
        return self._hovered_level

    @property
    def hovered_index(self) -> int:
        return self._hovered_index

    @property
    def hovered_item(self) -> Optional[SliceItem]:
        items_at_level = self.get_items_at_level(self._hovered_level)
        if 0 <= self._hovered_index < len(items_at_level):
            return items_at_level[self._hovered_index]
        return None

    def get_items_at_level(self, level: int) -> List[SliceItem]:
        if level == 0:
            return self.root_items
        elif 1 <= level <= len(self._nav_stack):
            return self._nav_stack[level - 1]["items"]
        return []

    def get_level_radii(self, level: int) -> Tuple[float, float]:
        """Calculates inner and outer radii for concentric spiral ring levels proportionally to self._radius."""
        scale = max(0.5, self._radius / 180.0)
        r_inner_base = self._inner_radius * scale
        if level == 0:
            return r_inner_base, r_inner_base + (87.0 * scale)
        elif level == 1:
            return 132.0 * scale, 205.0 * scale
        else:
            r_in = (205.0 + ((level - 1) * 75.0) + 7.0) * scale
            r_out = r_in + (68.0 * scale)
            return r_in, r_out

    def update_cursor_position(self, cursor_x: float, cursor_y: float) -> int:
        """
        Hit tests cursor across all active spiral ring levels.
        Returns hovered_index (-1 if none or center).
        """
        dx = cursor_x - self._center.x()
        dy = cursor_y - self._center.y()
        distance = math.hypot(dx, dy)

        # Center core check
        if distance < self._inner_radius:
            if not self._center_hovered:
                self._center_hovered = True
                self.profile_updated.emit()
            self._set_hovered(self._hovered_level, -1)
            return -1
        else:
            if self._center_hovered:
                self._center_hovered = False
                self.profile_updated.emit()

        active_levels = len(self._nav_stack)

        # Hit test from outer-most level inward
        for lvl in range(active_levels, -1, -1):
            r_in, r_out = self.get_level_radii(lvl)
            if r_in <= distance <= r_out + 12.0:
                items_lvl = self.get_items_at_level(lvl)
                count = len(items_lvl)
                if count > 0:
                    start_angle, total_span = self.get_level_arc_bounds(lvl)
                    angle_rad = math.atan2(dy, dx)
                    angle_deg = math.degrees(angle_rad)
                    norm_angle = (angle_deg + 90) % 360

                    if lvl == 0:
                        slice_angle = 360.0 / count
                        index = int(norm_angle // slice_angle) % count
                        self._set_hovered(0, index)
                        return index
                    else:
                        # Arc span for sub-ring level
                        rel_angle = (norm_angle - start_angle) % 360
                        if rel_angle <= total_span:
                            slice_angle = total_span / count
                            index = int(rel_angle // slice_angle)
                            if 0 <= index < count:
                                self._set_hovered(lvl, index)
                                return index

        self._set_hovered(self._hovered_level, -1)
        return -1

    def get_level_arc_bounds(self, level: int) -> Tuple[float, float]:
        """Returns (start_angle_deg, total_span_deg) for a given spiral ring level."""
        if level == 0:
            return 0.0, 360.0

        if 1 <= level <= len(self._nav_stack):
            p_idx = self._nav_stack[level - 1]["parent_index"]
            p_level = level - 1
            p_start, p_span = self.get_level_arc_bounds(p_level)
            p_count = len(self.get_items_at_level(p_level))
            if p_count > 0:
                p_item_span = p_span / p_count
                p_mid_angle = p_start + (p_idx * p_item_span) + (p_item_span / 2.0)
            else:
                p_mid_angle = 180.0

            # Sub-ring outer arc span: 220 degrees centered around parent item
            arc_span = 220.0
            arc_start = (p_mid_angle - arc_span / 2.0) % 360
            return arc_start, arc_span

        return 0.0, 360.0

    def get_slice_angles_for_level(self, level: int, index: int) -> Tuple[float, float]:
        """Returns start_angle and span_angle in degrees for QPainter (0 deg is 3 o'clock)."""
        items_lvl = self.get_items_at_level(level)
        count = len(items_lvl)
        if count == 0:
            return 0.0, 0.0

        start_angle, total_span = self.get_level_arc_bounds(level)
        span_angle = total_span / count
        item_start_norm = start_angle + (index * span_angle)

        # Convert top-clockwise degrees to QPainter counter-clockwise degrees (0 deg = 3 o'clock)
        q_start = 90.0 - (item_start_norm + span_angle)
        return q_start, span_angle

    def _set_hovered(self, level: int, index: int) -> None:
        if self._hovered_level != level or self._hovered_index != index:
            self._hovered_level = level
            self._hovered_index = index
            self.slice_hovered.emit(index)

