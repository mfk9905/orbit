"""
Orbit - Modern Cross-Platform Radial Menu Application
Main Entry Point.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer, QProcess

from app.core.container import ServiceContainer
from app.core.logging.logger import setup_logging, get_logger
from app.core.config.settings import SettingsManager
from app.core.platform.platform_manager import PlatformManager
from app.core.events.event_bus import EventBus, ConfigUpdatedEvent
from app.core.hooks.hotkey_manager import HotkeyManager

from app.services.settings_service import SettingsService
from app.services.profile_service import ProfileService
from app.services.action_service import ActionService
from app.services.plugin_service import PluginService
from app.services.active_window_service import ActiveWindowService

from app.plugins.launcher.plugin import LauncherPlugin
from app.plugins.media.plugin import MediaPlugin
from app.plugins.shell.plugin import ShellPlugin

from app.ui.widgets.system_tray import SystemTrayService
from app.ui.overlay.overlay_window import OverlayWindow
from app.ui.radial_menu.radial_menu_model import RadialMenuViewModel
from app.ui.radial_menu.radial_menu_view import RadialMenuView
from app.ui.settings.settings_window import SettingsWindow
from app.ui.editor.profile_editor_window import ProfileEditorWindow
from app.models.profile import SliceItem



from app.services.clipboard_service import ClipboardService

def main() -> int:
    """Orbit Application Entry Point."""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Orbit")
    app.setOrganizationName("Antigravity")

    # Initialize Clipboard monitoring
    ClipboardService.get_instance().init_clipboard()

    base_dir = Path(__file__).resolve().parent
    config_dir = base_dir / "user_data"
    log_file = config_dir / "orbit.log"

    logger = setup_logging(log_file=log_file)
    logger.info("Initializing Orbit Radial Menu Application...")

    container = ServiceContainer.get_instance()

    event_bus = EventBus()
    container.register_singleton(EventBus, event_bus)

    settings_mgr = SettingsManager(config_dir / "settings.json")
    settings_service = SettingsService(settings_mgr, event_bus)
    container.register_singleton(SettingsService, settings_service)

    platform = PlatformManager.create_platform()
    container.register_singleton(type(platform), platform)

    profile_service = ProfileService(config_dir / "profiles", event_bus)
    container.register_singleton(ProfileService, profile_service)

    action_service = ActionService(event_bus)
    container.register_singleton(ActionService, action_service)

    plugin_service = PluginService()
    plugin_service.register_plugin(LauncherPlugin())
    plugin_service.register_plugin(MediaPlugin())
    plugin_service.register_plugin(ShellPlugin())
    container.register_singleton(PluginService, plugin_service)

    overlay_window = OverlayWindow()

    radius = settings_service.get("radius", 180)
    view_model = RadialMenuViewModel(radius=radius)
    default_profile = profile_service.get_default_profile()
    view_model.set_default_items(default_profile.items)
    view_model.set_profile(profile_service.get_active_profile())

    radial_view = RadialMenuView(view_model, parent=overlay_window)
    radial_view.hide()

    def on_config_updated(event: ConfigUpdatedEvent) -> None:
        nonlocal radius
        if event.key == "radius":
            try:
                r = float(event.value)
                radius = r
                view_model.set_radius(r)
                radial_view.set_radius(r)
                logger.info(f"Live updated radial menu radius to {r}")
            except Exception as e:
                logger.error(f"Failed live update radius: {e}")
        elif event.key == "opacity":
            try:
                op = float(event.value)
                radial_view.setWindowOpacity(op)
                logger.info(f"Live updated window opacity to {op}")
            except Exception as e:
                logger.error(f"Failed live update opacity: {e}")
        elif event.key == "animation_speed":
            try:
                sp = int(event.value)
                radial_view.set_animation_speed(sp)
                logger.info(f"Live updated animation speed to {sp}ms")
            except Exception as e:
                logger.error(f"Failed live update animation speed: {e}")

    event_bus.subscribe(ConfigUpdatedEvent, on_config_updated)

    primary_hk = settings_service.get("primary_hotkey", "ctrl+space")
    secondary_hk = settings_service.get("secondary_hotkey", "button4")
    enable_hold = settings_service.get("enable_hold_duration", False)
    hold_sec = float(settings_service.get("hold_duration_seconds", 1.0))
    enable_corner = settings_service.get("enable_corner_hotspot", False)
    hotkey_mgr = HotkeyManager(
        primary_hotkey=primary_hk,
        secondary_hotkey=secondary_hk,
        enable_hold_duration=enable_hold,
        hold_duration_seconds=hold_sec,
        enable_corner_hotspot=enable_corner
    )

    settings_window = SettingsWindow(settings_service, profile_service, hotkey_mgr=hotkey_mgr)

    def dismiss_menu() -> None:
        radial_view.hide_menu()
        radial_view.hide()
        overlay_window.hide()
        hotkey_mgr.reset_active_state()

    def execute_slice(item: SliceItem) -> None:
        logger.info(f"Executing selected slice action: {item.label}")
        dismiss_menu()
        action_service.execute(item.action)

    def on_hotkey_trigger(raw_x: int, raw_y: int) -> None:
        """Called when hotkey is pressed."""
        if overlay_window.isVisible():
            logger.info("Hotkey pressed while active -> dismissing menu.")
            dismiss_menu()
            return

        from PySide6.QtGui import QCursor, QGuiApplication
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
        screen_geo = screen.geometry() if screen else QGuiApplication.primaryScreen().geometry()

        padding = radius + 35
        cx = max(screen_geo.left() + padding, min(cursor_pos.x(), screen_geo.right() - padding))
        cy = max(screen_geo.top() + padding, min(cursor_pos.y(), screen_geo.bottom() - padding))

        active_exe = ActiveWindowService.get_active_executable()
        matched_profile = profile_service.get_profile_for_app(active_exe)
        view_model.set_profile(matched_profile)

        logger.info(f"Hotkey triggered at ({cx}, {cy}) for active app '{active_exe}' using profile '{matched_profile.name}'")
        overlay_window.show_at_screen()

        radial_view.setGeometry(overlay_window.rect())
        view_model.set_center(cx, cy)

        radial_view.show()
        radial_view.show_menu()

    def on_hotkey_release(duration: float) -> None:
        """Called when hotkey is released."""
        logger.info(f"Hotkey released after {duration:.2f}s")
        selected_item = view_model.hovered_item

        if duration >= 0.2 and selected_item:
            execute_slice(selected_item)
        else:
            logger.info("Keeping radial menu open until click or dismiss.")

    def on_cursor_move(cx: int, cy: int) -> None:
        """Cursor tracking update."""
        if radial_view.isVisible():
            from PySide6.QtGui import QCursor
            pos = QCursor.pos()
            view_model.update_cursor_position(pos.x(), pos.y())

    radial_view.item_selected.connect(execute_slice)
    radial_view.dismiss_requested.connect(dismiss_menu)
    overlay_window.dismiss_requested.connect(dismiss_menu)

    hotkey_mgr.signals.menu_triggered.connect(on_hotkey_trigger)
    hotkey_mgr.signals.menu_released.connect(on_hotkey_release)
    hotkey_mgr.signals.cursor_moved.connect(on_cursor_move)
    hotkey_mgr.start()

    def handle_reload() -> None:
        logger.info("Reloading profiles and configuration...")
        profile_service.load_all_profiles()
        view_model.set_profile(profile_service.get_active_profile())

    def handle_restart() -> None:
        logger.info("Restarting Orbit application...")
        hotkey_mgr.stop()
        plugin_service.shutdown()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def handle_quit() -> None:
        logger.info("Quitting Orbit application...")
        hotkey_mgr.stop()
        plugin_service.shutdown()
        tray_service.hide()
        QApplication.quit()

    tray_service = SystemTrayService(
        on_open_settings=lambda: settings_window.show(),
        on_reload=handle_reload,
        on_restart=handle_restart,
        on_quit=handle_quit,
        on_open_editor=lambda: settings_window.show()
    )


    logger.info("Orbit application running in system tray. Press Mouse 4 or Ctrl+Space to activate radial menu.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
