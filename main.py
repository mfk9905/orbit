"""
Orbit - Modern Çapraz Platform Dairesel Menü Uygulaması
Ana Giriş Noktası (Application Entry Point).
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QProcess

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
from app.models.profile import SliceItem
from app.services.clipboard_service import ClipboardService


def main() -> int:
    """Orbit Ana Uygulama Başlatma Fonksiyonu."""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Orbit")
    app.setOrganizationName("Antigravity")

    # Pano dinleme servisini başlat
    ClipboardService.get_instance().init_clipboard()

    if getattr(sys, 'frozen', False):
        # PyInstaller EXE ortamı
        base_dir = Path(sys.executable).resolve().parent
        bundle_dir = Path(sys._MEIPASS)
    else:
        # Normal Python çalıştırma ortamı
        base_dir = Path(__file__).resolve().parent
        bundle_dir = base_dir

    config_dir = base_dir / "user_data"
    config_dir.mkdir(parents=True, exist_ok=True)
    profiles_dir = config_dir / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    # Gömülü varsayılan profiller yoksa kopyala
    bundled_profiles = bundle_dir / "user_data" / "profiles"
    if bundled_profiles.exists():
        import shutil
        for prof_file in bundled_profiles.glob("*.json"):
            target_file = profiles_dir / prof_file.name
            if not target_file.exists():
                try:
                    shutil.copy2(prof_file, target_file)
                except Exception:
                    pass

    log_file = config_dir / "orbit.log"

    logger = setup_logging(log_file=log_file)
    logger.info("Orbit Dairesel Menü Uygulaması Başlatılıyor...")

    container = ServiceContainer.get_instance()

    event_bus = EventBus()
    container.register_singleton(EventBus, event_bus)

    settings_mgr = SettingsManager(config_dir / "settings.json")
    settings_service = SettingsService(settings_mgr, event_bus)
    container.register_singleton(SettingsService, settings_service)

    platform = PlatformManager.create_platform()
    container.register_singleton(type(platform), platform)

    profile_service = ProfileService(profiles_dir, event_bus)
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
                logger.info(f"Dairesel menü yarıçapı canlı güncellendi: {r}")
            except Exception as e:
                logger.error(f"Canlı yarıçap güncelleme hatası: {e}")
        elif event.key == "opacity":
            try:
                op = float(event.value)
                radial_view.setWindowOpacity(op)
                logger.info(f"Pencere saydamlığı canlı güncellendi: {op}")
            except Exception as e:
                logger.error(f"Canlı saydamlık güncelleme hatası: {e}")
        elif event.key == "animation_speed":
            try:
                sp = int(event.value)
                radial_view.set_animation_speed(sp)
                logger.info(f"Animasyon hızı canlı güncellendi: {sp}ms")
            except Exception as e:
                logger.error(f"Canlı animasyon hızı güncelleme hatası: {e}")

    event_bus.subscribe(ConfigUpdatedEvent, on_config_updated)

    primary_hk = settings_service.get("primary_hotkey", "ctrl+space")
    secondary_hk = settings_service.get("secondary_hotkey", "button4")
    enable_hold = settings_service.get("enable_hold_duration", False)
    hold_sec = float(settings_service.get("hold_duration_seconds", 1.0))
    enable_corner = settings_service.get("enable_corner_hotspot", False)
    enable_gestures = settings_service.get("enable_mouse_gestures", True)
    gesture_thresh = float(settings_service.get("gesture_drag_threshold", 45.0))
    hotkey_mgr = HotkeyManager(
        primary_hotkey=primary_hk,
        secondary_hotkey=secondary_hk,
        enable_hold_duration=enable_hold,
        hold_duration_seconds=hold_sec,
        enable_corner_hotspot=enable_corner,
        enable_mouse_gestures=enable_gestures,
        gesture_drag_threshold=gesture_thresh
    )

    settings_window = SettingsWindow(settings_service, profile_service, hotkey_mgr=hotkey_mgr)

    def dismiss_menu() -> None:
        radial_view.hide_menu()
        radial_view.hide()
        overlay_window.hide()
        hotkey_mgr.reset_active_state()

    def execute_slice(item: SliceItem) -> None:
        logger.info(f"Seçilen dilim eylemi çalıştırılıyor: {item.label}")
        dismiss_menu()
        action_service.execute(item.action)

    def on_hotkey_trigger(raw_x: int, raw_y: int) -> None:
        """Kısayol tuşuna basıldığında tetiklenir."""
        if overlay_window.isVisible():
            logger.info("Menü açıkken kısayol basıldı -> kapatılıyor.")
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

        logger.info(f"Kısayol tetiklendi ({cx}, {cy}). Aktif uygulama: '{active_exe}', Profil: '{matched_profile.name}'")
        overlay_window.show_at_screen()

        radial_view.setGeometry(overlay_window.rect())
        view_model.set_center(cx, cy)

        radial_view.show()
        radial_view.show_menu()

    def on_hotkey_release(duration: float) -> None:
        """Kısayol tuşu bırakıldığında tetiklenir."""
        logger.info(f"Kısayol tuşu {duration:.2f}s sonra bırakıldı.")
        selected_item = view_model.hovered_item

        if selected_item:
            from app.models.actions import WheelAction
            if isinstance(selected_item.action, WheelAction):
                logger.info("Seçili öğe WheelAction -> Dairesel menü etkileşimli kaydırma için açık tutuluyor.")
                return

        if duration >= 0.2 and selected_item:
            execute_slice(selected_item)
        else:
            logger.info("Menü tıklama veya kapatılana kadar açık tutuluyor.")

    def on_cursor_move(cx: int, cy: int) -> None:
        """İmleç konum güncelemesi."""
        if radial_view.isVisible():
            from PySide6.QtGui import QCursor
            pos = QCursor.pos()
            view_model.update_cursor_position(pos.x(), pos.y())

    def on_gesture_detected(direction: str) -> None:
        """Fare sürükleme kaydırması tespit edildiğinde tetiklenir."""
        logger.info(f"Fare jesti algılandı: {direction.upper()}")
        dismiss_menu()

        gestures_cfg = settings_service.get("gestures", {})
        act_dict = gestures_cfg.get(direction)
        if act_dict:
            from app.models.actions import action_factory
            action = action_factory(act_dict)
            action_service.execute(action)

    radial_view.item_selected.connect(execute_slice)
    radial_view.dismiss_requested.connect(dismiss_menu)
    overlay_window.dismiss_requested.connect(dismiss_menu)

    hotkey_mgr.signals.menu_triggered.connect(on_hotkey_trigger)
    hotkey_mgr.signals.menu_released.connect(on_hotkey_release)
    hotkey_mgr.signals.cursor_moved.connect(on_cursor_move)
    hotkey_mgr.signals.gesture_detected.connect(on_gesture_detected)
    hotkey_mgr.start()

    def handle_config_updated(event: ConfigUpdatedEvent) -> None:
        logger.info(f"Konfigürasyon canlı güncellendi: {event.key} = {event.value}")
        if event.key == "radius":
            new_r = float(event.value)
            view_model.set_radius(new_r)
            radial_view.set_radius(new_r)
        elif event.key == "opacity":
            radial_view.setWindowOpacity(float(event.value))
        elif event.key == "animation_speed":
            radial_view.set_animation_speed(int(event.value))

    event_bus.subscribe(ConfigUpdatedEvent, handle_config_updated)

    def handle_reload() -> None:
        logger.info("Profiller ve konfigürasyon yeniden yükleniyor...")
        profile_service.load_all_profiles()
        view_model.set_profile(profile_service.get_active_profile())

    def handle_restart() -> None:
        logger.info("Orbit uygulaması yeniden başlatılıyor...")
        hotkey_mgr.stop()
        plugin_service.shutdown()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def handle_quit() -> None:
        logger.info("Orbit uygulamasından çıkılıyor...")
        hotkey_mgr.stop()
        plugin_service.shutdown()
        tray_service.hide()
        QApplication.quit()

    tray_service = SystemTrayService(
        on_open_settings=lambda: settings_window.show(),
        on_reload=handle_reload,
        on_restart=handle_restart,
        on_quit=handle_quit
    )

    logger.info("Orbit dairesel menü arka planda çalışıyor. Fare 4 veya Ctrl+Space ile aktif edebilirsiniz.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
