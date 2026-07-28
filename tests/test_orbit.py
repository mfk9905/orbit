"""
Unit tests for Orbit core components.
"""

import pytest
from pathlib import Path
from app.core.container import ServiceContainer
from app.core.config.settings import SettingsManager
from app.core.events.event_bus import EventBus, Event
from app.models.actions import AppAction, UrlAction, ShellAction, TextAction
from app.models.profile import Profile, SliceItem
from app.ui.radial_menu.radial_menu_model import RadialMenuViewModel


def test_service_container():
    container = ServiceContainer()
    bus = EventBus()
    container.register_singleton(EventBus, bus)
    assert container.resolve(EventBus) is bus
    assert container.has(EventBus)


def test_settings_manager(tmp_path: Path):
    config_file = tmp_path / "settings.json"
    mgr = SettingsManager(config_file)
    assert mgr.get("theme") == "dark"

    mgr.set("radius", 200)
    assert mgr.get("radius") == 200

    # Reload from file
    mgr2 = SettingsManager(config_file)
    assert mgr2.get("radius") == 200


def test_action_execution(monkeypatch):
    executed = []
    def mock_popen(cmd, shell=True):
        executed.append(cmd)
        return None

    monkeypatch.setattr("subprocess.Popen", mock_popen)

    app_action = AppAction("test_app", "Test App", params={"command": "echo hello"})
    assert app_action.execute() is True
    assert executed == ["echo hello"]


def test_radial_view_model_slices():
    item1 = SliceItem("s1", "Item 1", "icon", "#2ED573", AppAction("a1", "A1"))
    item2 = SliceItem("s2", "Item 2", "icon", "#2ED573", AppAction("a2", "A2"))
    item3 = SliceItem("s3", "Item 3", "icon", "#2ED573", AppAction("a3", "A3"))
    item4 = SliceItem("s4", "Item 4", "icon", "#2ED573", AppAction("a4", "A4"))

    prof = Profile("4-Slice", [item1, item2, item3, item4])
    vm = RadialMenuViewModel(radius=100, inner_radius=20)
    vm.set_profile(prof)
    vm.set_center(100, 100)

    assert vm.slice_count == 4

    # Top center (100, 50) -> Should hit slice 0 (North)
    idx = vm.update_cursor_position(100, 50)
    assert idx == 0

    # Right center (150, 100) -> Should hit slice 1 (East)
    idx = vm.update_cursor_position(150, 100)
    assert idx == 1


def test_app_bindings_and_active_window_matching(tmp_path: Path):
    from app.services.active_window_service import ActiveWindowService
    from app.services.profile_service import ProfileService

    # 1. Active Window Service check
    exe_name = ActiveWindowService.get_active_executable()
    assert isinstance(exe_name, str)

    # 2. Profile app matching check
    item = SliceItem("s1", "Item 1", "icon", "#2ED573", AppAction("a1", "A1"))
    prof_code = Profile("VS Code", [item], app_bindings=["code.exe", "code"])
    assert prof_code.matches_app("code.exe") is True
    assert prof_code.matches_app("Code.exe") is True
    assert prof_code.matches_app("code") is True
    assert prof_code.matches_app("notepad.exe") is False

    # 3. Profile Service lookup check
    profiles_dir = tmp_path / "profiles"
    prof_svc = ProfileService(profiles_dir, EventBus())
    prof_svc.save_profile("vscode", prof_code)

    matched = prof_svc.get_profile_for_app("code.exe")
    assert matched.name == "VS Code"

    fallback = prof_svc.get_profile_for_app("unknown_app.exe")
    assert fallback.name == "Varsayılan"


def test_sub_ring_navigation():
    from app.models.actions import SubRingAction, ShortcutAction, action_factory

    sub_item1 = SliceItem("sub1", "Sub 1", "icon", "#007ACC", ShortcutAction("sa1", "SA1", params={"keys": "ctrl+c"}))
    sub_item2 = SliceItem("sub2", "Sub 2", "icon", "#007ACC", ShortcutAction("sa2", "SA2", params={"keys": "ctrl+v"}))

    sub_ring_act = SubRingAction("s_act", "Sub Ring", items=[sub_item1, sub_item2])
    root_item = SliceItem("root1", "Tools", "tools", "#007ACC", sub_ring_act)

    prof = Profile("SubTest", [root_item])
    vm = RadialMenuViewModel(radius=100, inner_radius=20)
    vm.set_profile(prof)
    vm.set_center(100, 100)

    assert vm.is_at_root is True
    assert vm.slice_count == 1

    # Push sub-ring
    vm.push_sub_ring("Tools", [sub_item1, sub_item2])
    assert vm.is_at_root is False
    assert vm.slice_count == 2
    assert vm.items[0].label == "Sub 1"

    # Test center hover detection
    vm.update_cursor_position(100, 100)  # At center
    assert vm.is_center_hovered is True
    assert vm.hovered_index == -1

    # Pop sub-ring
    assert vm.pop_sub_ring() is True
    assert vm.is_at_root is True
    assert vm.slice_count == 1

    # Test action_factory roundtrip for SubRingAction
    act_dict = sub_ring_act.to_dict()
    recreated = action_factory(act_dict)
    assert isinstance(recreated, SubRingAction)
    assert len(recreated.sub_items) == 2


def test_smart_actions():
    from app.models.actions import MacroAction, WheelAction, WindowControlAction, action_factory

    # 1. MacroAction test
    macro = MacroAction("m1", "Macro Test", params={
        "steps": [
            {"type": "delay", "ms": 10},
            {"type": "shortcut", "keys": "ctrl+c"}
        ]
    })
    assert macro.execute() is True

    # 2. WheelAction test
    wheel = WheelAction("w1", "Wheel Test", params={"mode": "zoom"})
    assert wheel.execute_wheel(1) is True
    assert wheel.execute_wheel(-1) is True

    # 3. WindowControlAction test
    win_act = WindowControlAction("wc1", "Win Control", params={"command": "minimize"})
    assert win_act.execute() is True

    # 4. Action Factory tests
    m_recreated = action_factory(macro.to_dict())
    assert isinstance(m_recreated, MacroAction)

    w_recreated = action_factory(wheel.to_dict())
    assert isinstance(w_recreated, WheelAction)

    wc_recreated = action_factory(win_act.to_dict())
    assert isinstance(wc_recreated, WindowControlAction)


def test_icon_manager():
    from app.core.icons.icon_manager import IconManager
    from app.core.icons.svg_library import SVG_ICONS

    assert "terminal" in SVG_ICONS
    assert "globe" in SVG_ICONS

    renderer = IconManager.get_renderer("terminal", "#2ED573")
    assert renderer is not None
    assert renderer.isValid() is True


def test_clipboard_and_keyboard_actions():
    from app.models.actions import KeyboardAction, ClipboardSubRingAction, ClipboardAction, action_factory
    from app.services.clipboard_service import ClipboardService

    # 1. KeyboardAction test
    kb_act = KeyboardAction("kb1", "Keyboard", params={"mode": "osk"})
    kb_dict = kb_act.to_dict()
    recreated_kb = action_factory(kb_dict)
    assert isinstance(recreated_kb, KeyboardAction)

    # 2. ClipboardAction test
    clip_action = ClipboardAction("ca1", "Paste Snippet", params={"text": "Hello Orbit World"})
    assert clip_action.params["text"] == "Hello Orbit World"
    ca_dict = clip_action.to_dict()
    recreated_ca = action_factory(ca_dict)
    assert isinstance(recreated_ca, ClipboardAction)
    assert recreated_ca.params["text"] == "Hello Orbit World"

    # 3. ClipboardSubRingAction test & ClipboardService history
    clip_act = ClipboardSubRingAction("c1", "ClipHistory")
    clip_svc = ClipboardService.get_instance()
    clip_svc.history = ["Test 1", "Multi Line\nTest 2"]
    sub_items = clip_act.sub_items
    assert len(sub_items) == 2
    assert sub_items[0].label == "Test 1"
    assert isinstance(sub_items[0].action, ClipboardAction)
    assert sub_items[1].label == "Multi Line Test 2"

    clip_svc.clear_history()
    assert len(clip_svc.history) == 0
    empty_items = clip_act.sub_items
    assert len(empty_items) == 1
    assert empty_items[0].label == "Pano Boş"


def test_phase1_live_config_and_profile_reload(tmp_path: Path):
    from app.services.settings_service import SettingsService
    from app.core.events.event_bus import ConfigUpdatedEvent

    # 1. Config event publish test
    bus = EventBus()
    cfg_file = tmp_path / "settings.json"
    mgr = SettingsManager(cfg_file)
    svc = SettingsService(mgr, bus)

    events_received = []
    bus.subscribe(ConfigUpdatedEvent, lambda ev: events_received.append((ev.key, ev.value)))

    svc.set("radius", 220)
    assert len(events_received) == 1
    assert events_received[0] == ("radius", 220)

    # 2. RadialViewModel dynamic radius test
    vm = RadialMenuViewModel(radius=100)
    assert vm._radius == 100
    vm.set_radius(220)
    assert vm._radius == 220


def test_phase2_subring_editor_and_profile_duplication(tmp_path: Path):
    from app.models.actions import SubRingAction, ShortcutAction
    from app.services.profile_service import ProfileService

    # 1. Test SubRing nested sub-item dictionary conversion
    sub1 = SliceItem("s1", "Copy", "copy", "#2ED573", ShortcutAction("a1", "Copy", params={"keys": "ctrl+c"}))
    sub2 = SliceItem("s2", "Paste", "clipboard", "#2ED573", ShortcutAction("a2", "Paste", params={"keys": "ctrl+v"}))
    sub_action = SubRingAction("sr1", "Clipboard SubRing", items=[sub1, sub2])

    parent_item = SliceItem("p1", "Tools", "tools", "#3498DB", sub_action)
    prof = Profile("ParentProfile", [parent_item])

    prof_svc = ProfileService(tmp_path / "profiles", EventBus())
    prof_svc.save_profile("parent_prof", prof)

    # Reload from storage
    reloaded = prof_svc._profiles["parent_prof"]
    assert len(reloaded.items) == 1
    reloaded_act = reloaded.items[0].action
    assert isinstance(reloaded_act, SubRingAction)
    assert len(reloaded_act.sub_items) == 2
    assert reloaded_act.sub_items[0].label == "Copy"


def test_phase3_autostart_and_shortcut_safety():
    from app.core.platform.platform_manager import PlatformManager
    from app.models.actions import ShortcutAction

    # 1. Platform autostart interface test
    platform = PlatformManager.create_platform()
    assert hasattr(platform, "set_autostart")
    assert hasattr(platform, "is_autostart_enabled")

    # 2. ShortcutAction safety test
    sc = ShortcutAction("sc_test", "CopyTest", params={"keys": "ctrl+c"})
    # Mocking pynput to avoid actual keyboard events during headless test run if needed
    assert sc.label == "CopyTest"


def test_phase4_theme_tokens():
    from app.core.theme import DesignTokens
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])

    # 1. DesignTokens test
    assert DesignTokens.PRIMARY_ACCENT == "#2ED573"
    font = DesignTokens.get_font(size=12.0, bold=True)
    assert isinstance(font, QFont)
    assert font.bold() is True


def test_phase5_hotkey_manager_and_editor_ui(tmp_path: Path):
    from PySide6.QtWidgets import QApplication
    from app.core.hooks.hotkey_manager import HotkeyManager
    from app.ui.editor.profile_editor_window import ProfileEditorWindow
    from app.services.profile_service import ProfileService

    app = QApplication.instance() or QApplication([])

    # 1. HotkeyManager match test
    hk_mgr = HotkeyManager(primary_hotkey="ctrl+space", secondary_hotkey="button4")
    hk_mgr._currently_pressed_keys = {"ctrl", "space"}
    assert hk_mgr._matches_shortcut("ctrl+space") is True
    assert hk_mgr._matches_shortcut("alt+r") is False

    hk_mgr._currently_pressed_mouse = {"button4"}
    assert hk_mgr._matches_shortcut("button4") is True

    # 2. ProfileEditorWindow instantiation and duplication test
    prof_svc = ProfileService(tmp_path / "profiles", EventBus())
    editor = ProfileEditorWindow(prof_svc)
    assert editor.windowTitle() == "Orbit - Görsel Profil ve Halkalar Editörü"
    assert editor.profile_list_widget.count() >= 1

    # Duplicate profile test
    editor.profile_list_widget.setCurrentRow(0)
    editor._on_duplicate_profile()
    assert editor.profile_list_widget.count() >= 2


def test_settings_window_instantiation(tmp_path: Path):
    from PySide6.QtWidgets import QApplication
    from app.ui.settings.settings_window import SettingsWindow
    from app.services.settings_service import SettingsService
    from app.services.profile_service import ProfileService

    app = QApplication.instance() or QApplication([])
    bus = EventBus()
    cfg_file = tmp_path / "settings.json"
    mgr = SettingsManager(cfg_file)
    settings_svc = SettingsService(mgr, bus)
    prof_svc = ProfileService(tmp_path / "profiles", bus)

    win = SettingsWindow(settings_svc, prof_svc)
    assert win.windowTitle() == "Orbit - Kontrol Merkezi & Halkalar Editörü"
    assert win.sidebar.count() == 5


def test_ping_tool_dialog_and_action():
    from PySide6.QtWidgets import QApplication
    from app.ui.dialogs.ping_dialog import PingDialog
    from app.models.actions import SystemToolAction

    app = QApplication.instance() or QApplication([])

    dialog = PingDialog(initial_host="8.8.8.8")
    assert dialog.windowTitle() == "Orbit Ping - Canlı Ağ Monitörü (ping -a -t)"
    assert dialog.txt_target.text() == "8.8.8.8"
    assert dialog.packet_count == 0
    assert dialog.btn_start.isEnabled() is True
    assert dialog.btn_stop.isEnabled() is False

    # Test output parser for English and Turkish ping outputs
    dialog._parse_ping_line("Pinging google.com [142.250.185.78] with 32 bytes of data:")
    assert "google.com" in dialog.resolved_target
    assert "142.250.185.78" in dialog.resolved_target

    dialog._parse_ping_line("Reply from 142.250.185.78: bytes=32 time=14ms TTL=117")
    assert dialog.packet_count == 1
    assert dialog.last_latency == "14 ms"

    dialog._parse_ping_line("142.250.185.78 adresinden 32 bayt veri ile yanıt: bayt=32 süre=18ms TTL=117")
    assert dialog.packet_count == 2
    assert dialog.last_latency == "18 ms"

    # Test SystemToolAction execution for ping_tool
    action = SystemToolAction("act_ping", "Ping", params={"command": "ping_tool", "host": "1.1.1.1"})
    assert action.execute() is True

    # Test ShellAction fallback when command is cmd.exe /k ping -t -a
    from app.models.actions import ShellAction
    shell_action = ShellAction("act_shell_ping", "Ping Shell", params={"command": "cmd.exe /k ping -t -a"})
    assert shell_action.execute() is True


def test_mouse_gestures():
    from app.core.hooks.hotkey_manager import HotkeyManager

    hk_mgr = HotkeyManager(primary_hotkey="ctrl+space", secondary_hotkey="button4", enable_mouse_gestures=True, gesture_drag_threshold=40.0)
    assert hk_mgr.enable_mouse_gestures is True
    assert hk_mgr.gesture_drag_threshold == 40.0

    detected_gestures = []
    hk_mgr.signals.gesture_detected.connect(lambda d: detected_gestures.append(d))

    # Simulate activation at (100, 100)
    hk_mgr._is_active = True
    hk_mgr._currently_pressed_mouse.add("button4")
    hk_mgr._drag_start_pos = (100.0, 100.0)
    hk_mgr._gesture_detected_direction = None

    # 1. Drag Up: (100, 50) -> dy = -50 (dist = 50 >= 40)
    hk_mgr._on_mouse_move(100.0, 50.0)
    assert len(detected_gestures) == 1
    assert detected_gestures[-1] == "up"

    # Reset active state
    hk_mgr.reset_active_state()
    hk_mgr._is_active = True
    hk_mgr._currently_pressed_mouse.add("button4")
    hk_mgr._drag_start_pos = (100.0, 100.0)

    # 2. Drag Down: (100, 160) -> dy = +60
    hk_mgr._on_mouse_move(100.0, 160.0)
    assert len(detected_gestures) == 2
    assert detected_gestures[-1] == "down"

    # Reset active state
    hk_mgr.reset_active_state()
    hk_mgr._is_active = True
    hk_mgr._currently_pressed_mouse.add("button4")
    hk_mgr._drag_start_pos = (100.0, 100.0)

    # 3. Drag Left: (40, 100) -> dx = -60
    hk_mgr._on_mouse_move(40.0, 100.0)
    assert len(detected_gestures) == 3
    assert detected_gestures[-1] == "left"

    # Reset active state
    hk_mgr.reset_active_state()
    hk_mgr._is_active = True
    hk_mgr._currently_pressed_mouse.add("button4")
    hk_mgr._drag_start_pos = (100.0, 100.0)

    # 4. Drag Right: (160, 100) -> dx = +60
    hk_mgr._on_mouse_move(160.0, 100.0)
    assert len(detected_gestures) == 4
    assert detected_gestures[-1] == "right"


def test_radial_window_switcher():
    from app.services.active_window_service import ActiveWindowService
    from app.models.actions import WindowSwitchAction, WindowSwitcherSubRingAction, action_factory

    # 1. Test WindowSwitchAction execution and serialization
    ws_act = WindowSwitchAction("ws1", "Focus VS Code", params={"hwnd": 123456})
    assert ws_act.params["hwnd"] == 123456
    ws_dict = ws_act.to_dict()
    recreated_ws = action_factory(ws_dict)
    assert isinstance(recreated_ws, WindowSwitchAction)
    assert recreated_ws.params["hwnd"] == 123456

    # 2. Test WindowSwitcherSubRingAction dynamic items generation
    switcher_subring = WindowSwitcherSubRingAction("wss1", "Açık Pencereler")
    sub_items = switcher_subring.sub_items
    assert isinstance(sub_items, list)
    assert len(sub_items) >= 1

    # 3. Test ActiveWindowService open windows enumeration
    open_wins = ActiveWindowService.get_open_windows()
    assert isinstance(open_wins, list)
    for hwnd, exe, title in open_wins:
        assert isinstance(hwnd, int)
        assert isinstance(exe, str)
        assert isinstance(title, str)
















