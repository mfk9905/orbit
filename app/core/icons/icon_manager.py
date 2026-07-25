"""
Icon Manager module for caching and rendering SVG vector icons.
"""

from typing import Dict
from PySide6.QtCore import QByteArray, QRectF
from PySide6.QtGui import QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from app.core.icons.svg_library import SVG_ICONS
from app.core.logging.logger import get_logger

logger = get_logger("orbit.icons")


class IconManager:
    """Manages rendering and caching of SVG vector icons."""

    _cache: Dict[str, QSvgRenderer] = {}

    @classmethod
    def get_renderer(cls, icon_name: str, color_hex: str = "#FFFFFF") -> QSvgRenderer | None:
        """Returns QSvgRenderer for the given icon name and stroke color."""
        key = f"{icon_name}:{color_hex}"
        if key in cls._cache:
            return cls._cache[key]

        raw_svg = SVG_ICONS.get(icon_name)
        if not raw_svg:
            # Fallback to default icon if not found
            raw_svg = SVG_ICONS.get("command", "")

        if not raw_svg:
            return None

        # Replace stroke/fill color dynamically
        colored_svg = raw_svg.replace('stroke="currentColor"', f'stroke="{color_hex}"')
        colored_svg = colored_svg.replace('fill="currentColor"', f'fill="{color_hex}"')

        data = QByteArray(colored_svg.encode("utf-8"))
        renderer = QSvgRenderer(data)
        if renderer.isValid():
            cls._cache[key] = renderer
            return renderer

        return None

    @classmethod
    def render_icon(cls, painter: QPainter, icon_name: str, target_rect: QRectF, color: QColor) -> bool:
        """Renders vector SVG icon centered inside target_rect."""
        renderer = cls.get_renderer(icon_name, color.name())
        if renderer and renderer.isValid():
            renderer.render(painter, target_rect)
            return True
        return False
