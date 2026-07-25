"""
Plugin Service responsible for discovering, initializing, and managing plugins.
"""

from typing import Dict, List
from app.plugins.base_plugin import BasePlugin
from app.models.base_action import BaseAction
from app.core.logging.logger import get_logger

logger = get_logger("orbit.services.plugin")


class PluginService:
    """Manages active Orbit extensions."""

    def __init__(self) -> None:
        self._plugins: Dict[str, BasePlugin] = {}

    def register_plugin(self, plugin: BasePlugin) -> bool:
        """Registers and initializes a plugin."""
        try:
            if plugin.initialize():
                self._plugins[plugin.plugin_id] = plugin
                logger.info(f"Registered plugin '{plugin.name}' (v{plugin.version})")
                return True
        except Exception as e:
            logger.error(f"Failed to initialize plugin '{plugin.name}': {e}")
        return False

    def get_registered_actions(self) -> List[BaseAction]:
        """Gathers all actions provided by active plugins."""
        actions: List[BaseAction] = []
        for plugin in self._plugins.values():
            if plugin.is_enabled:
                actions.extend(plugin.register_actions())
        return actions

    def shutdown(self) -> None:
        """Gracefully shutdown all plugins."""
        for plugin in self._plugins.values():
            try:
                plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin '{plugin.name}': {e}")
