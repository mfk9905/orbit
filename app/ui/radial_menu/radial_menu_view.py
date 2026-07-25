"""
Modern PySide6 Custom QPainter View for Radial Menu.
Provides smooth animations, glowing hover expansion, and modern dark aesthetics.
"""

import math
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF, QPropertyAnimation, Property, QEasingCurve, Signal
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QFont, QPen, QBrush, QRadialGradient, QMouseEvent
)
from app.ui.radial_menu.radial_menu_model import RadialMenuViewModel
from app.models.profile import SliceItem
from app.core.logging.logger import get_logger

logger = get_logger("orbit.ui.radial_view")


class RadialMenuView(QWidget):
    """Custom high-performance animated radial menu widget."""

    item_selected = Signal(SliceItem)
    dismiss_requested = Signal()

    def __init__(self, viewModel: RadialMenuViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.viewModel = viewModel
        self.viewModel.slice_hovered.connect(self._on_slice_hovered)
        self.viewModel.profile_updated.connect(self.update)

        self._scale_factor: float = 0.0
        self._radius: float = 180.0
        self._inner_radius: float = 55.0

        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # Smooth animation for scale with spring physics
        self._anim = QPropertyAnimation(self, b"scaleFactor")
        self._anim.setDuration(240)
        self._anim.setEasingCurve(QEasingCurve.OutBack)

    @Property(float)
    def scaleFactor(self) -> float:
        return self._scale_factor

    @scaleFactor.setter
    def scaleFactor(self, val: float) -> None:
        self._scale_factor = val
        self.update()

    def show_menu(self) -> None:
        """Triggers opening scale animation with spring physics."""
        self._anim.stop()
        self._anim.setStartValue(0.08)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def hide_menu(self) -> None:
        """Resets animation scale factor."""
        self._anim.stop()
        self._scale_factor = 0.0
        self.update()

    def _on_slice_hovered(self, index: int) -> None:
        """Trigger repaint on hover state changes."""
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Track mouse move over widget to update hovered slice."""
        pos = event.globalPosition() if hasattr(event, "globalPosition") else self.mapToGlobal(event.pos())
        self.viewModel.update_cursor_position(pos.x(), pos.y())
        super().mouseMoveEvent(event)

    def wheelEvent(self, event) -> None:
        """Handle mouse wheel scrolling on hovered slice."""
        item = self.viewModel.hovered_item
        if item:
            from app.models.actions import WheelAction
            if isinstance(item.action, WheelAction):
                delta_y = event.angleDelta().y()
                if delta_y != 0:
                    direction = 1 if delta_y > 0 else -1
                    item.action.execute_wheel(direction)
                    
                    # Trigger visual feedback
                    if not hasattr(self, '_vol_anim_states'):
                        self._vol_anim_states = {}
                    import time
                    self._vol_anim_states[item.slice_id] = (time.time(), direction)
                    
                    self.update()
                    event.accept()
                    return
        super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Click to select slice, enter sub-ring, open Genel Menü, or go back."""
        pos = event.globalPosition() if hasattr(event, "globalPosition") else self.mapToGlobal(event.pos())
        center = self.viewModel._center
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        distance = math.hypot(dx, dy)

        # 1. Click outside radial ring circle -> dismiss menu immediately!
        if distance > self._radius + 20:
            logger.info("Clicked outside radial ring -> requesting dismiss")
            self.dismiss_requested.emit()
            return

        if event.button() == Qt.LeftButton:
            item = self.viewModel.hovered_item
            if item:
                from app.models.actions import SubRingAction
                if isinstance(item.action, SubRingAction):
                    logger.info(f"Opening sub-ring '{item.label}'")
                    self.viewModel.push_sub_ring(item.label, item.action.sub_items)
                    self.show_menu()
                else:
                    self.item_selected.emit(item)
            elif self.viewModel.is_center_hovered:
                if not self.viewModel.is_at_root:
                    logger.info("Center Back clicked -> Returning to parent ring")
                    self.viewModel.pop_sub_ring()
                    self.show_menu()
                elif self.viewModel.is_app_profile and self.viewModel.default_items:
                    logger.info("Center Genel Menü clicked -> Opening General Profile")
                    self.viewModel.push_sub_ring("Genel Menü", self.viewModel.default_items)
                    self.show_menu()
                else:
                    self.dismiss_requested.emit()
            else:
                self.dismiss_requested.emit()

    def paintEvent(self, event) -> None:
        if self._scale_factor <= 0.01:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Convert global menu center to local coordinates inside full screen widget
        center_pt = self.mapFromGlobal(self.viewModel._center.toPoint())
        cx, cy = float(center_pt.x()), float(center_pt.y())

        # Save painter state for scale transform centered at (cx, cy)
        painter.save()
        painter.translate(cx, cy)
        painter.scale(self._scale_factor, self._scale_factor)

        items = self.viewModel.items
        count = len(items)
        if count == 0:
            painter.restore()
            return

        hovered_idx = self.viewModel.hovered_index
        from app.models.actions import SubRingAction
        from app.core.icons.icon_manager import IconManager

        # 1. Draw outer subtle glow background ring
        glow_grad = QRadialGradient(0, 0, self._radius + 28)
        glow_grad.setColorAt(0.0, QColor(46, 213, 115, 38))
        glow_grad.setColorAt(0.7, QColor(46, 213, 115, 8))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow_grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(0, 0), self._radius + 28, self._radius + 28)

        # 2. Draw each slice segment with gaps
        gap_deg = 2.0 if count > 1 else 0.0

        for i, item in enumerate(items):
            is_hovered = (i == hovered_idx)
            r_outer = self._radius + (15 if is_hovered else 0)
            r_inner = self._inner_radius + 4.0

            raw_start, raw_span = self.viewModel.get_slice_angles(i)
            start_deg = raw_start + (gap_deg / 2.0)
            span_deg = raw_span - gap_deg

            # Build Pie Arc Path with gap
            path = QPainterPath()
            outer_rect = QRectF(-r_outer, -r_outer, r_outer * 2, r_outer * 2)
            inner_rect = QRectF(-r_inner, -r_inner, r_inner * 2, r_inner * 2)

            path.arcMoveTo(outer_rect, start_deg)
            path.arcTo(outer_rect, start_deg, span_deg)
            path.arcTo(inner_rect, start_deg + span_deg, -span_deg)
            path.closeSubpath()

            # Colors & Glassmorphism Styling
            if is_hovered:
                # Custom accent color if set on item or profile
                item_color = QColor(item.color) if item.color else QColor("#2ED573")
                fill_color = item_color
                border_pen = QPen(QColor("#FFFFFF"), 2.5)
            else:
                fill_color = QColor(20, 26, 34, 235)
                border_pen = QPen(QColor(55, 65, 78, 180), 1.5)

            # Volume animation override
            anim_active = False
            if hasattr(self, '_vol_anim_states') and item.slice_id in self._vol_anim_states:
                import time
                t, dir = self._vol_anim_states[item.slice_id]
                elapsed = time.time() - t
                if elapsed < 0.6:
                    anim_active = True
                    alpha = int(255 * (1.0 - elapsed/0.6))
                    anim_color = QColor(46, 213, 115, alpha) if dir > 0 else QColor(255, 71, 87, alpha)
                    border_pen = QPen(anim_color, 4.0)
                    fill_color = QColor(20, 26, 34, 255) # Opaque background during animation
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(30, self.update)

            painter.fillPath(path, QBrush(fill_color))
            painter.setPen(border_pen)
            painter.drawPath(path)

            # 3. Draw Vector SVG Icon + Label inside Slice
            mid_deg = math.radians(raw_start + raw_span / 2.0)
            r_mid = (r_outer + r_inner) / 2.0
            ix = r_mid * math.cos(mid_deg)
            iy = -r_mid * math.sin(mid_deg)

            icon_color = QColor(10, 20, 15) if is_hovered else QColor(240, 245, 250)

            # Render Vector SVG Icon if available
            has_icon = bool(item.icon)
            if has_icon:
                icon_rect = QRectF(ix - 10, iy - 20, 20, 20)
                IconManager.render_icon(painter, item.icon, icon_rect, icon_color)

            display_label = item.label + " ▶" if isinstance(item.action, SubRingAction) else item.label
            
            if anim_active:
                _, dir = self._vol_anim_states[item.slice_id]
                display_label = "+ Sesi Aç" if dir > 0 else "- Sesi Kıs"
                icon_color = anim_color
                
            font_size = 8.0 if len(display_label) > 12 else 9.0
            painter.setFont(QFont("Outfit", font_size, QFont.Bold if is_hovered else QFont.DemiBold))
            painter.setPen(icon_color)

            if has_icon:
                rect_text = QRectF(ix - 45, iy + 2, 90, 22)
            else:
                rect_text = QRectF(ix - 45, iy - 14, 90, 28)

            painter.drawText(rect_text, Qt.TextWordWrap | Qt.AlignCenter, display_label)

        # 4. Center Core Circle & Active Tooltip / Back / Genel Menü display
        core_path = QPainterPath()
        core_path.addEllipse(QPointF(0, 0), self._inner_radius, self._inner_radius)

        is_center_hovered = self.viewModel.is_center_hovered
        is_sub_ring = not self.viewModel.is_at_root
        is_app_at_root = self.viewModel.is_at_root and self.viewModel.is_app_profile

        if (is_sub_ring or is_app_at_root) and is_center_hovered:
            core_fill = QBrush(QColor("#2ED573"))
            core_pen = QPen(QColor("#FFFFFF"), 2.5)
            center_color = QColor("#0A140F")
        elif is_center_hovered:
            core_fill = QBrush(QColor(35, 45, 55, 240))
            core_pen = QPen(QColor("#FFFFFF"), 2)
            center_color = QColor("#2ED573")
        else:
            core_fill = QBrush(QColor(16, 20, 26, 245))
            core_pen = QPen(QColor("#2ED573"), 2)
            center_color = QColor("#2ED573")

        painter.fillPath(core_path, core_fill)
        painter.setPen(core_pen)
        painter.drawPath(core_path)

        # Render Center Core Vector Icon + Text
        rect_core = QRectF(-self._inner_radius + 4, -self._inner_radius + 4, (self._inner_radius - 4) * 2, (self._inner_radius - 4) * 2)

        if is_sub_ring:
            IconManager.render_icon(painter, "arrow-left", QRectF(-9, -20, 18, 18), center_color)
            painter.setFont(QFont("Outfit", 9.5, QFont.Bold))
            painter.setPen(center_color)
            painter.drawText(QRectF(-40, 2, 80, 20), Qt.AlignCenter, "Geri")
        elif is_app_at_root:
            IconManager.render_icon(painter, "home", QRectF(-9, -20, 18, 18), center_color)
            painter.setFont(QFont("Outfit", 9.0, QFont.Bold))
            painter.setPen(center_color)
            painter.drawText(QRectF(-45, 2, 90, 20), Qt.AlignCenter, "Genel Menü")
        elif hovered_idx != -1 and self.viewModel.hovered_item:
            hovered_item = self.viewModel.hovered_item
            if hovered_item.icon:
                IconManager.render_icon(painter, hovered_item.icon, QRectF(-9, -22, 18, 18), center_color)
                rect_tooltip = QRectF(-self._inner_radius + 4, 0, (self._inner_radius - 4) * 2, self._inner_radius - 4)
            else:
                rect_tooltip = rect_core

            tooltip_text = hovered_item.tooltip
            font_size = 8.0 if len(tooltip_text) > 16 else 8.5
            painter.setFont(QFont("Outfit", font_size, QFont.DemiBold))
            painter.setPen(center_color)
            painter.drawText(rect_tooltip, Qt.TextWordWrap | Qt.AlignCenter, tooltip_text)

        painter.restore()



