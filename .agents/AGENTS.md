# Orbit - Project Guidelines & Architecture for AI Agents

## Overview
Orbit is a high-performance, Windows-native desktop radial menu application (inspired by Logitech Options+ / Actions Ring). It features active application context sensing, multi-tiered sub-rings, vector SVG icons, smooth QPainter spring physics animations, and a visual profile editor.

## Tech Stack & Architecture
- **Language**: Python 3.13+
- **GUI Framework**: PySide6 (Qt 6.x) with custom `QPainter` radial slice rendering, `QtSvg` vector graphics, and translucent overlay windows.
- **Input & Windows API**: `ctypes` Win32 API (`GetForegroundWindow`, `QueryFullProcessImageNameW`) for process sensing; `pynput` for global hotkey and mouse listening.
- **Pattern**: MVVM (Model-View-ViewModel) + Dependency Injection Container + Event Bus.

## Project Structure
```text
orbit/
├── app/
│   ├── core/
│   │   ├── config/            # SettingsManager (JSON config persistence)
│   │   ├── container.py       # Dependency Injection Container
│   │   ├── events/            # EventBus & Event definitions
│   │   ├── icons/             # svg_library.py & icon_manager.py (QSvgRenderer cache & recoloring)
│   │   └── logging/           # Centralized logging setup
│   ├── models/                # Profile, SliceItem, and polymorphic Action models
│   ├── services/              # ActiveWindowService, ProfileService, ActionService
│   └── ui/
│       ├── editor/            # ProfileEditorWindow (Visual Profile & Ring Editor GUI)
│       ├── overlay/           # OverlayWindow (Virtual multi-monitor screen coverage & focus loss dismiss)
│       ├── radial_menu/       # RadialMenuViewModel (Geometry & Nav Stack) & RadialMenuView (QPainter View)
│       ├── settings/          # SettingsWindow (Hotkey & radius config GUI)
│       └── widgets/           # SystemTrayService (System tray context menu)
├── user_data/profiles/        # Profile JSON definitions (default.json, vscode.json, browser.json)
├── tests/                     # Pytest suite (test_orbit.py)
├── main.py                    # Application Entry Point & Event Wiring
└── pyproject.toml             # Dependencies & Setuptools configuration
```

## Key Guidelines & Conventions

### 1. High-DPI & Coordinate Systems
- Always use `PySide6.QtGui.QCursor.pos()` inside Qt thread callbacks to avoid DPI misalignment with raw OS coordinates.
- Radial menu center `(cx, cy)` must be clamped to the active monitor's geometry (`radius + 35` padding) to prevent screen edge overflow.

### 2. Focus & Overlay Dismissal
- `OverlayWindow` covers `QGuiApplication.screens()` virtual geometry.
- `OverlayWindow.changeEvent()` listens for `QEvent.ActivationChange` to dismiss the radial menu immediately when losing active focus or clicking outside Orbit.

### 3. Action Models & Factory
- All actions inherit from `BaseAction` in `app/models/actions.py`.
- Action types (`AppAction`, `UrlAction`, `ShellAction`, `ShortcutAction`, `TextAction`, `MacroAction`, `WheelAction`, `WindowControlAction`, `SubRingAction`) must be registered in `action_factory()`.

### 4. Vector SVG Icons
- Icons are defined in `app/core/icons/svg_library.py` as Feather/Lucide SVG strings.
- Render icons via `IconManager.render_icon(painter, icon_name, target_rect, color)` for dynamic recoloring and `QSvgRenderer` caching.

### 5. Profile & Navigation Logic
- Profiles bind to application executable names (`app_bindings: ["code.exe"]`).
- In app-specific profiles, the center core circle displays `Genel Menü ▶` to access the default profile items.
- In sub-rings, center core circle displays `← Geri` to pop back up the navigation stack.

## Testing & Quality Assurance
- Run unit tests with:
  ```powershell
  pytest
  ```
- All new features should include unit tests in `tests/test_orbit.py`.
