# Orbit - Modern Radial Menu Application

Orbit is a high-performance, cross-platform open-source radial menu application designed for productivity enthusiasts. It brings quick application launching, custom shortcut execution, and system controls under global hotkeys (Mouse Button 4 or Ctrl+Space).

Primary platform support: **Fedora KDE Plasma**, **Windows 11**, and **macOS**.

---

## Key Features

- **Global Hotkey Activation**: Opens instantly at the cursor location via Mouse Side Button (Button 4) or `Ctrl+Space`.
- **Dynamic Slices**: Supports 4, 6, 8, or 12-segment radial rings with smooth Qt animations.
- **Glassmorphism & Neon Glow**: Modern dark UI design with glowing `#2ED573` accent highlights and KDE Plasma desktop integration.
- **MVVM & SOLID Architecture**: Decoupled presentation, data models, and platform abstractions.
- **Action Engine**: Execute shell commands, launch desktop apps, open URLs, trigger key combinations, or type text strings.
- **System Tray Core**: Runs unobtrusively in the background.

---

## Installation & Running

### Requirements
- Python 3.11+
- Qt6 / PySide6

### Setup

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

**Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .[dev]
```

### Running Orbit

```bash
python main.py
```

Press `Ctrl+Space` or click Mouse Button 4 to bring up the radial ring at your cursor!

---

## Documentation

- [Architecture Guide](docs/Architecture.md)
- [Contributing Guidelines](docs/Contributing.md)

---

## License

MIT License.
