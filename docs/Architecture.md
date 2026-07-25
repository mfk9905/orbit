# Orbit System Architecture

Orbit follows strict **SOLID** design principles and the **Model-View-ViewModel (MVVM)** architectural pattern.

## Layer Overview

```
+---------------------------------------------------------+
|                    System Tray & Overlay                |
+---------------------------------------------------------+
|            RadialMenuView (QPainter / Animation)        |
+---------------------------------------------------------+
|           RadialMenuViewModel (Polar Geometry)          |
+---------------------------------------------------------+
|    ProfileService   |   ActionService  |  PluginService |
+---------------------------------------------------------+
| PlatformManager (LinuxPlatform / WindowsPlatform / Mac) |
+---------------------------------------------------------+
|                  ServiceContainer (DI)                  |
+---------------------------------------------------------+
```

### Core Components

1. **ServiceContainer (`app/core/container.py`)**:
   Provides explicit singleton and factory registration for dependency injection without hard coupling.

2. **EventBus (`app/core/events/event_bus.py`)**:
   Decoupled pub-sub mechanism for inter-component communication (`RadialMenuTriggerEvent`, `ActionExecuteEvent`, `ConfigUpdatedEvent`).

3. **Platform Abstraction (`app/core/platform/`)**:
   - `BasePlatform`: Pure interface for platform calls.
   - `LinuxPlatform`: Wayland / X11 KDE Plasma integration.
   - `WindowsPlatform`: Windows DWM blur and cursor hooks.
   - `MacPlatform`: macOS fallback stub.

4. **Action System (`app/models/actions.py`)**:
   All actions derive from `BaseAction`. V1 includes:
   - `AppAction`: Launches applications via subprocess.
   - `UrlAction`: Opens web links.
   - `ShellAction`: Executes shell scripts.
   - `ShortcutAction`: Keypress emulation via `pynput`.
   - `TextAction`: Auto-typing text strings.

5. **Plugin Architecture (`app/plugins/`)**:
   Plugins subclass `BasePlugin` to register custom actions dynamically.
