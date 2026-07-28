"""
Radial Menu ViewModel (MVVM Architecture).
Encapsulates state logic, slice geometry calculations, and hover detection.
"""

from app.core.config.settings import logger
import math
from typing import List, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QPointF, QRectF
from app.models.profile import Profile, SliceItem


class RadialMenuViewModel(QObject):
    """ViewModel maintaining state and mathematics for clean single-ring radial slices and sub-rings."""

    slice_hovered = Signal(int)  # Emits hovered slice index of active level (-1 if none)
    profile_updated = Signal()

    def __init__(self, radius: float = 180.0, inner_radius: float = 38.0) -> None:
        super().__init__()
        self._profile: Optional[Profile] = None
        self._default_items: List[SliceItem] = []
        # _nav_stack holds sub-rings: list of dicts {"label": str, "items": List[SliceItem], "parent_index": int}
        self._nav_stack: List[dict] = []
        self._center = QPointF(0, 0)
        self._target_center: Optional[QPointF] = None
        self._screen_geo: Optional[QRectF] = None
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
        self._reclamp_center()
        self.profile_updated.emit()

    def push_sub_ring(self, label: str, items: List[SliceItem], parent_index: int = -1) -> bool:
        """Navigates into a sub-ring layer, replacing active ring items."""
        target_parent = parent_index if parent_index >= 0 else self._hovered_index

        self._nav_stack.append({
            "label": label,
            "items": items,
            "parent_index": target_parent
        })
        self._hovered_level = len(self._nav_stack)
        self._hovered_index = -1
        self._center_hovered = False
        self._reclamp_center()
        self.profile_updated.emit()
        return True

    def pop_sub_ring(self) -> bool:
        """Pops back to parent ring layer. Returns True if navigated back."""
        if self._nav_stack:
            self._nav_stack.pop()
            self._hovered_level = len(self._nav_stack)
            self._hovered_index = -1
            self._center_hovered = False
            self._reclamp_center()
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
            self._reclamp_center()
            self.profile_updated.emit()

    @property
    def is_at_root(self) -> bool:
        return len(self._nav_stack) == 0

    @property
    def is_center_hovered(self) -> bool:
        return self._center_hovered

    def set_center(self, x: float, y: float, screen_geo: Optional[object] = None) -> None:
        """Sets screen coordinates of menu center and clamps to screen bounds."""
        self._target_center = QPointF(x, y)
        if screen_geo is not None:
            if hasattr(screen_geo, "x"):
                self._screen_geo = QRectF(
                    float(screen_geo.x()),
                    float(screen_geo.y()),
                    float(screen_geo.width()),
                    float(screen_geo.height())
                )
            else:
                self._screen_geo = QRectF(screen_geo)
        elif self._screen_geo is None:
            try:
                from PySide6.QtGui import QGuiApplication
                from PySide6.QtCore import QPoint
                scr = QGuiApplication.screenAt(QPoint(int(x), int(y))) or QGuiApplication.primaryScreen()
                if scr:
                    sg = scr.geometry()
                    self._screen_geo = QRectF(float(sg.x()), float(sg.y()), float(sg.width()), float(sg.height()))
            except Exception:
                pass
        self._reclamp_center()

    def _reclamp_center(self) -> None:
        """Re-clamps menu center to screen geometry based on menu radius."""
        if not hasattr(self, "_target_center") or self._target_center is None:
            return
        if not hasattr(self, "_screen_geo") or self._screen_geo is None:
            self._center = QPointF(self._target_center)
            return

        tx = self._target_center.x()
        ty = self._target_center.y()

        padding = self._radius + 35.0

        s_left = float(self._screen_geo.x())
        s_right = s_left + float(self._screen_geo.width())
        s_top = float(self._screen_geo.y())
        s_bottom = s_top + float(self._screen_geo.height())

        min_x = s_left + padding
        max_x = s_right - padding
        if min_x > max_x:
            cx = (s_left + s_right) / 2.0
        else:
            cx = max(min_x, min(tx, max_x))

        min_y = s_top + padding
        max_y = s_bottom - padding
        if min_y > max_y:
            cy = (s_top + s_bottom) / 2.0
        else:
            cy = max(min_y, min(ty, max_y))

        self._center = QPointF(cx, cy)

    def set_radius(self, radius: float, inner_radius: float = 38.0) -> None:
        """Dynamically update menu radius."""
        self._radius = radius
        self._inner_radius = inner_radius
        self._reclamp_center()
        self.profile_updated.emit()

    @property
    def root_items(self) -> List[SliceItem]:
        return self._profile.items if self._profile else []

    @property
    def items(self) -> List[SliceItem]:
        """Returns items of active navigation level."""
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
        active_items = self.items
        if 0 <= self._hovered_index < len(active_items):
            return active_items[self._hovered_index]
        return None

    def get_items_at_level(self, level: int) -> List[SliceItem]:
        if level == 0:
            return self.root_items
        elif 1 <= level <= len(self._nav_stack):
            return self._nav_stack[level - 1]["items"]
        return []

    def get_level_radii(self, level: int = 0) -> Tuple[float, float]:
        """Returns inner and outer radii for single ring display."""
        scale = max(0.5, self._radius / 180.0)
        return self._inner_radius * scale, self._radius * scale

    def update_cursor_position(self, cursor_x: float, cursor_y: float) -> int:
        """Hit tests cursor across active single ring slices."""
        dx = cursor_x - self._center.x()
        dy = cursor_y - self._center.y()
        distance = math.hypot(dx, dy)

        # Center core check
        if distance < self._inner_radius:
            if not self._center_hovered:
                self._center_hovered = True
                self.profile_updated.emit()
            self._set_hovered(len(self._nav_stack), -1)
            return -1
        else:
            if self._center_hovered:
                self._center_hovered = False
                self.profile_updated.emit()

        scale = max(0.5, self._radius / 180.0)
        r_inner = self._inner_radius * scale
        r_outer = self._radius * scale

        if r_inner <= distance <= r_outer + 14.0:
            items_active = self.items
            count = len(items_active)
            if count > 0:
                angle_rad = math.atan2(dy, dx)
                angle_deg = math.degrees(angle_rad)
                norm_angle = (angle_deg + 90) % 360

                slice_angle = 360.0 / count
                index = int(norm_angle // slice_angle) % count
                self._set_hovered(len(self._nav_stack), index)
                return index

        self._set_hovered(len(self._nav_stack), -1)
        return -1

    def get_slice_angles_for_level(self, level: int, index: int) -> Tuple[float, float]:
        """Returns start_angle and span_angle in degrees for QPainter (0 deg is 3 o'clock)."""
        items_lvl = self.items
        count = len(items_lvl)
        if count == 0:
            return 0.0, 0.0

        slice_span = 360.0 / count
        item_start_norm = index * slice_span

        q_start = 90.0 - (item_start_norm + slice_span)
        return q_start, slice_span

    def _set_hovered(self, level: int, index: int) -> None:
        if self._hovered_level != level or self._hovered_index != index:
            self._hovered_level = level
            self._hovered_index = index
            self.slice_hovered.emit(index)


