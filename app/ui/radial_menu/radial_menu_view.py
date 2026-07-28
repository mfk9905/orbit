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
        self._inner_radius: float = 38.0

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

    def set_radius(self, radius: float, inner_radius: float = 38.0) -> None:
        """Dynamically update view rendering radius."""
        self._radius = radius
        self._inner_radius = inner_radius
        self.update()

    def set_animation_speed(self, duration_ms: int) -> None:
        """Dynamically update opening animation duration in milliseconds."""
        self._anim.setDuration(max(50, duration_ms))

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
        """Click to select slice, enter sub-ring spiral layer, open Genel Menü, or go back."""
        pos = event.globalPosition() if hasattr(event, "globalPosition") else self.mapToGlobal(event.pos())
        center = self.viewModel._center
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        distance = math.hypot(dx, dy)

        active_levels = len(self.viewModel._nav_stack)
        _, max_r_out = self.viewModel.get_level_radii(active_levels)

        # 1. Click outside spiral menu area -> dismiss menu immediately!
        if distance > max_r_out + 30.0:
            logger.info("Clicked outside spiral menu -> requesting dismiss")
            self.dismiss_requested.emit()
            return

        if event.button() == Qt.LeftButton:
            item = self.viewModel.hovered_item
            hovered_idx = self.viewModel.hovered_index
            hovered_lvl = self.viewModel.hovered_level

            if item and hovered_idx >= 0:
                from app.models.actions import SubRingAction
                if isinstance(item.action, SubRingAction):
                    logger.info(f"Opening sub-ring spiral layer '{item.label}' from level {hovered_lvl}")
                    self.viewModel.push_sub_ring(item.label, item.action.sub_items, parent_index=hovered_idx)
                    self.show_menu()
                else:
                    self.item_selected.emit(item)
            elif self.viewModel.is_center_hovered:
                if not self.viewModel.is_at_root:
                    logger.info("Center Back clicked -> Returning to parent spiral layer")
                    self.viewModel.pop_sub_ring()
                    self.show_menu()
                elif self.viewModel.is_app_profile and self.viewModel.default_items:
                    logger.info("Center Genel Menü clicked -> Opening General Profile")
                    self.viewModel.push_sub_ring("Genel Menü", self.viewModel.default_items, parent_index=0)
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

        from app.models.actions import SubRingAction
        from app.core.icons.icon_manager import IconManager
        from PySide6.QtGui import QLinearGradient, QFontMetrics

        accent_hex = self.viewModel._profile.accent_color if (self.viewModel._profile and hasattr(self.viewModel._profile, "accent_color")) else "#2ED573"
        accent_qcolor = QColor(accent_hex)

        active_stack_count = len(self.viewModel._nav_stack)

        # 1. Outer Ambient Glow Halo for Nautilus Spiral Menu
        _, max_r_out = self.viewModel.get_level_radii(active_stack_count)
        glow_grad = QRadialGradient(0, 0, max_r_out + 35)
        glow_grad.setColorAt(0.0, QColor(accent_qcolor.red(), accent_qcolor.green(), accent_qcolor.blue(), 45))
        glow_grad.setColorAt(0.6, QColor(0, 242, 254, 20))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow_grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(0, 0), max_r_out + 35, max_r_out + 35)

        # 2. Render Each Level of the Nautilus Spiral Ring
        for lvl in range(active_stack_count + 1):
            items_lvl = self.viewModel.get_items_at_level(lvl)
            count = len(items_lvl)
            if count == 0:
                continue

            r_inner_base, r_outer_base = self.viewModel.get_level_radii(lvl)

            # Determine parent active index for this level if a child level is open
            active_parent_idx = -1
            if lvl < active_stack_count:
                active_parent_idx = self.viewModel._nav_stack[lvl]["parent_index"]

            gap_deg = 3.0 if count > 1 else 0.0

            for i, item in enumerate(items_lvl):
                is_hovered = (lvl == self.viewModel.hovered_level and i == self.viewModel.hovered_index)
                is_active_parent = (i == active_parent_idx)

                r_outer = r_outer_base + (14.0 if is_hovered else 0.0)
                r_inner = r_inner_base

                raw_start, raw_span = self.viewModel.get_slice_angles_for_level(lvl, i)
                start_deg = raw_start + (gap_deg / 2.0)
                span_deg = raw_span - gap_deg

                mid_angle_rad = math.radians(raw_start + raw_span / 2.0)
                pop_offset = 6.0 if is_hovered else (3.0 if is_active_parent else 0.0)
                pop_x = pop_offset * math.cos(mid_angle_rad)
                pop_y = -pop_offset * math.sin(mid_angle_rad)

                painter.save()
                painter.translate(pop_x, pop_y)

                # Build Arc Pod Path
                path = QPainterPath()
                outer_rect = QRectF(-r_outer, -r_outer, r_outer * 2, r_outer * 2)
                inner_rect = QRectF(-r_inner, -r_inner, r_inner * 2, r_inner * 2)

                path.arcMoveTo(outer_rect, start_deg)
                path.arcTo(outer_rect, start_deg, span_deg)
                path.arcTo(inner_rect, start_deg + span_deg, -span_deg)
                path.closeSubpath()

                item_base = QColor(item.color) if item.color else accent_qcolor

                # Actions Ring Shader Logic
                if is_hovered:
                    # Hovered Pod: Vibrant Gradient Fill + White Rim
                    fill_grad = QLinearGradient(0, -r_outer, 0, r_outer)
                    fill_grad.setColorAt(0.0, item_base.lighter(135))
                    fill_grad.setColorAt(1.0, item_base.darker(110))
                    fill_brush = QBrush(fill_grad)
                    border_pen = QPen(QColor("#FFFFFF"), 3.0)

                    # Pod Glow Aura
                    pod_glow = QRadialGradient(0, 0, r_outer + 12)
                    pod_glow.setColorAt(0.7, QColor(item_base.red(), item_base.green(), item_base.blue(), 90))
                    pod_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
                    painter.fillPath(path, QBrush(pod_glow))
                elif is_active_parent:
                    # Active Parent Pod (Nautilus Purple/Lavender Accent as in reference image)
                    fill_grad = QLinearGradient(0, -r_outer, 0, r_outer)
                    fill_grad.setColorAt(0.0, QColor("#A29BFE"))
                    fill_grad.setColorAt(1.0, QColor("#6C5CE7"))
                    fill_brush = QBrush(fill_grad)
                    border_pen = QPen(QColor("#D63031"), 2.2) if item_base == QColor("#D63031") else QPen(QColor("#E056FD"), 2.2)
                else:
                    # Idle Pod: Dark Frosted Glass Metallic
                    fill_grad = QLinearGradient(0, -r_outer, 0, r_outer)
                    fill_grad.setColorAt(0.0, QColor(26, 36, 52, 235))
                    fill_grad.setColorAt(1.0, QColor(12, 18, 28, 245))
                    fill_brush = QBrush(fill_grad)
                    border_pen = QPen(QColor(48, 62, 84, 200), 1.5)

                # Wheel Animation feedback override
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
                        fill_brush = QBrush(QColor(15, 23, 42, 255))
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(30, self.update)

                painter.fillPath(path, fill_brush)
                painter.setPen(border_pen)
                painter.drawPath(path)

                # Icon & Typography Position Calculations
                r_mid = (r_outer + r_inner) / 2.0
                ix = r_mid * math.cos(mid_angle_rad)
                iy = -r_mid * math.sin(mid_angle_rad)

                icon_color = QColor("#0B132B") if (is_hovered or is_active_parent) else QColor("#F8FAFC")

                has_icon = bool(item.icon)
                if has_icon:
                    icon_size = 24 if is_hovered else 20
                    icon_rect = QRectF(ix - icon_size/2, iy - icon_size/2 - 8, icon_size, icon_size)
                    IconManager.render_icon(painter, item.icon, icon_rect, icon_color)

                display_label = item.label + " ▶" if isinstance(item.action, SubRingAction) else item.label

                if anim_active:
                    _, dir = self._vol_anim_states[item.slice_id]
                    display_label = "+ Sesi Aç" if dir > 0 else "- Sesi Kıs"
                    icon_color = anim_color
                font_size = 8.5 if len(display_label) > 12 else 9.5
                lbl_font = QFont("Segoe UI", font_size, QFont.Bold if (is_hovered or is_active_parent) else QFont.DemiBold)
                painter.setFont(lbl_font)

                # Font Metrics & Elision bounds to prevent text overflow out of slice pods
                fm = QFontMetrics(lbl_font)
                max_text_width = max(36.0, (r_outer - r_inner) * 1.4)
                elided_label = fm.elidedText(display_label, Qt.ElideRight, int(max_text_width))

                if has_icon:
                    rect_text = QRectF(ix - max_text_width/2, iy + 5, max_text_width, 22)
                else:
                    rect_text = QRectF(ix - max_text_width/2, iy - 12, max_text_width, 26)

                # Draw high-contrast text shadow for 100% legibility
                if not is_hovered and not is_active_parent:
                    painter.setPen(QColor(0, 0, 0, 180))
                    painter.drawText(rect_text.translated(1, 1), Qt.TextSingleLine | Qt.AlignCenter, elided_label)

                painter.setPen(icon_color)
                painter.drawText(rect_text, Qt.TextSingleLine | Qt.AlignCenter, elided_label)

                painter.restore()

        # 3. Clean White/Metallic Center Core Disc (No busy edit buttons per user request)
        core_path = QPainterPath()
        core_path.addEllipse(QPointF(0, 0), self._inner_radius, self._inner_radius)

        is_center_hovered = self.viewModel.is_center_hovered
        is_sub_ring = not self.viewModel.is_at_root
        is_app_at_root = self.viewModel.is_at_root and self.viewModel.is_app_profile

        if (is_sub_ring or is_app_at_root) and is_center_hovered:
            core_fill = QBrush(QColor("#00F2FE"))
            core_pen = QPen(QColor("#FFFFFF"), 3.5)
            center_color = QColor("#0B132B")
        elif is_center_hovered:
            core_fill = QBrush(QColor(241, 245, 249, 255))
            core_pen = QPen(QColor("#00F2FE"), 3.0)
            center_color = QColor("#0B132B")
        else:
            core_fill = QBrush(QColor(248, 250, 252, 250))
            core_pen = QPen(QColor(203, 213, 225), 2.5)
            center_color = QColor("#1E293B")

        # Inner Lens Shadow
        lens_glow = QRadialGradient(0, 0, self._inner_radius)
        lens_glow.setColorAt(0.0, QColor(0, 0, 0, 30))
        lens_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillPath(core_path, QBrush(lens_glow))

        painter.fillPath(core_path, core_fill)
        painter.setPen(core_pen)
        painter.drawPath(core_path)

        # Render Center Core Icon & Label
        rect_core = QRectF(-self._inner_radius + 4, -self._inner_radius + 4, (self._inner_radius - 4) * 2, (self._inner_radius - 4) * 2)

        if is_sub_ring:
            IconManager.render_icon(painter, "arrow-left", QRectF(-11, -22, 22, 22), center_color)
            painter.setFont(QFont("Segoe UI", 10.0, QFont.Bold))
            painter.setPen(center_color)
            painter.drawText(QRectF(-40, 5, 80, 20), Qt.AlignCenter, "Geri")
        elif is_app_at_root:
            IconManager.render_icon(painter, "home", QRectF(-11, -22, 22, 22), center_color)
            painter.setFont(QFont("Segoe UI", 9.5, QFont.Bold))
            painter.setPen(center_color)
            painter.drawText(QRectF(-45, 5, 90, 20), Qt.AlignCenter, "Genel Menü")
        elif self.viewModel.hovered_item:
            hovered_item = self.viewModel.hovered_item
            if hovered_item.icon:
                IconManager.render_icon(painter, hovered_item.icon, QRectF(-11, -22, 22, 22), center_color)
                rect_tooltip = QRectF(-self._inner_radius + 4, 3, (self._inner_radius - 4) * 2, self._inner_radius - 6)
            else:
                rect_tooltip = rect_core

            tooltip_text = hovered_item.tooltip
            font_size = 8.0 if len(tooltip_text) > 16 else 8.5
            painter.setFont(QFont("Segoe UI", font_size, QFont.Bold))
            painter.setPen(center_color)
            
            # Format tooltip with elision if too long for center core
            fm_core = QFontMetrics(painter.font())
            elided_tooltip = fm_core.elidedText(tooltip_text, Qt.ElideRight, int((self._inner_radius - 6) * 2))
            painter.drawText(rect_tooltip, Qt.TextSingleLine | Qt.AlignCenter, elided_tooltip)

        painter.restore()



