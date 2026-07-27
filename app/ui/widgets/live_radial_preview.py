"""
Interactive Live Radial Menu Preview Widget for Orbit Control Center.
Renders real-time radial slices using QPainter and handles mouse interactions.
"""

import math
from typing import Optional, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QRadialGradient
from app.models.profile import Profile, SliceItem
from app.core.icons.icon_manager import IconManager
from app.core.logging.logger import get_logger

logger = get_logger("orbit.ui.widgets.live_preview")


class LiveRadialPreviewWidget(QWidget):
    """Interactive live-rendering widget for visual profile editing."""

    slice_selected = Signal(int, object)  # (index, SliceItem)
    center_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(320, 320)
        self.setMouseTracking(True)

        self._profile: Optional[Profile] = None
        self._items: List[SliceItem] = []
        self._hovered_index: int = -1
        self._selected_index: int = -1
        self._center_hovered: bool = False

    def set_profile(self, profile: Profile, selected_index: int = -1) -> None:
        """Loads profile and updates widget rendering."""
        self._profile = profile
        self._items = profile.items if profile else []
        self._selected_index = selected_index
        self.update()

    def set_items(self, items: List[SliceItem], selected_index: int = -1) -> None:
        """Loads specific items list (e.g. SubRing items) into preview widget."""
        self._items = items
        self._selected_index = selected_index
        self.update()

    def set_selected_index(self, index: int) -> None:
        """Sets active selected slice index."""
        self._selected_index = index
        self.update()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        cx, cy = self.width() / 2, self.height() / 2
        dx, dy = pos.x() - cx, pos.y() - cy
        dist = math.hypot(dx, dy)

        inner_radius = 45
        outer_radius = min(cx, cy) - 20

        new_hover = -1
        new_center = False

        if dist <= inner_radius:
            new_center = True
        elif dist <= outer_radius and self._items:
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad) % 360.0

            n = len(self._items)
            slice_angle = 360.0 / n
            start_offset = -90.0 - (slice_angle / 2.0)
            rel_angle = (angle_deg - start_offset) % 360.0
            new_hover = int(rel_angle // slice_angle)
            if new_hover >= n:
                new_hover = n - 1

        if new_hover != self._hovered_index or new_center != self._center_hovered:
            self._hovered_index = new_hover
            self._center_hovered = new_center
            self.setCursor(Qt.PointingHandCursor if (new_hover != -1 or new_center) else Qt.ArrowCursor)
            self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self._center_hovered:
                self.center_clicked.emit()
            elif 0 <= self._hovered_index < len(self._items):
                self._selected_index = self._hovered_index
                self.slice_selected.emit(self._selected_index, self._items[self._selected_index])
                self.update()

    def leaveEvent(self, event) -> None:
        self._hovered_index = -1
        self._center_hovered = False
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        inner_r = 45
        outer_r = min(cx, cy) - 20

        # Background Actions Ring subtle glow circle
        glow_grad = QRadialGradient(QPointF(cx, cy), outer_r + 16)
        glow_grad.setColorAt(0.0, QColor(0, 242, 254, 30))
        glow_grad.setColorAt(0.6, QColor(46, 213, 115, 15))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow_grad)
        painter.drawEllipse(QPointF(cx, cy), outer_r + 16, outer_r + 16)

        if not self._items:
            painter.setPen(QPen(QColor("#64748B"), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), outer_r, outer_r)
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Menüde Dilim Yok\n(+ Yeni Dilim Ekle)")
            painter.end()
            return

        n = len(self._items)
        angle_step = 360.0 / n
        gap_deg = 3.5 if n > 1 else 0.0

        for i, item in enumerate(self._items):
            start_angle = -90.0 - (angle_step / 2.0) + (i * angle_step) + (gap_deg / 2.0)
            span_deg = angle_step - gap_deg
            
            # Floating Pod Arc Path
            path = QPainterPath()
            outer_rect = QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
            inner_rect = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)

            path.arcMoveTo(outer_rect, -start_angle)
            path.arcTo(outer_rect, -start_angle, -span_deg)
            path.arcTo(inner_rect, -start_angle - span_deg, span_deg)
            path.closeSubpath()

            # Actions Ring Color Scheme
            base_color = QColor(item.color if item.color else "#2ED573")
            is_selected = (i == self._selected_index)
            is_hovered = (i == self._hovered_index)

            if is_selected:
                fill_color = base_color.lighter(125)
                pen = QPen(QColor("#FFFFFF"), 2.8)
            elif is_hovered:
                fill_color = base_color.lighter(115)
                pen = QPen(QColor("#00F2FE"), 2.5)
            else:
                fill_color = QColor(18, 24, 34, 235)
                pen = QPen(QColor(42, 54, 79, 200), 1.5)

            painter.setPen(pen)
            painter.setBrush(QBrush(fill_color))
            painter.drawPath(path)

            # Render Icon & Label inside slice
            mid_angle_deg = start_angle + (span_deg / 2.0)
            mid_rad = math.radians(mid_angle_deg)
            r_mid = (inner_r + outer_r) / 2.0
            ix = cx + r_mid * math.cos(mid_rad)
            iy = cy + r_mid * math.sin(mid_rad)

            icon_color = QColor("#0A140F") if (is_selected or is_hovered) else QColor("#F1F5F9")

            icon_size = 22
            target_rect = QRectF(ix - icon_size / 2, iy - icon_size / 2 - 6, icon_size, icon_size)
            IconManager.render_icon(painter, item.icon, target_rect, color=icon_color)

            # Slice Text Label below Icon
            painter.setPen(icon_color)
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            text_rect = QRectF(ix - 45, iy + 6, 90, 18)
            painter.drawText(text_rect, Qt.AlignCenter, item.label)

        # Center Core Circle
        core_color = QColor("#00F2FE") if self._center_hovered else QColor("#101520")
        painter.setPen(QPen(QColor("#2ED573"), 2.5))
        painter.setBrush(QBrush(core_color))
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        painter.setPen(QColor("#042F1A") if self._center_hovered else QColor("#2ED573"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        prof_name = self._profile.name if self._profile else "Orbit"
        painter.drawText(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2), Qt.AlignCenter, prof_name)
        painter.end()
