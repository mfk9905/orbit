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
    from app.models.actions import KeyboardAction, ClipboardSubRingAction, action_factory
    from app.services.clipboard_service import ClipboardService

    # 1. KeyboardAction test
    kb_act = KeyboardAction("kb1", "Keyboard", params={"mode": "osk"})
    kb_dict = kb_act.to_dict()
    recreated_kb = action_factory(kb_dict)
    assert isinstance(recreated_kb, KeyboardAction)

    # 2. ClipboardSubRingAction test
    clip_act = ClipboardSubRingAction("c1", "ClipHistory")
    clip_svc = ClipboardService.get_instance()
    clip_svc.history = ["Test 1", "Test 2"]
    sub_items = clip_act.sub_items
    assert len(sub_items) == 2
    assert sub_items[0].label == "Test 1"








