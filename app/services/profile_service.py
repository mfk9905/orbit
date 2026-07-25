"""
Profile Service managing loading, saving, and active profile switching.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from app.models.profile import Profile, SliceItem
from app.models.actions import AppAction, UrlAction, ShellAction, ShortcutAction, TextAction
from app.core.events.event_bus import EventBus, ProfileChangedEvent
from app.core.logging.logger import get_logger

logger = get_logger("orbit.services.profile")


class ProfileService:
    """Manages profile storage and active radial menu profile state."""

    def __init__(self, profiles_dir: Path, event_bus: EventBus) -> None:
        self.profiles_dir = profiles_dir
        self.event_bus = event_bus
        self._profiles: Dict[str, Profile] = {}
        self._active_profile: Optional[Profile] = None

        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.load_all_profiles()

        if not self._profiles:
            self._create_default_profile()

        # Set default active profile
        self.set_active_profile("default")

    def load_all_profiles(self) -> None:
        """Loads all JSON profile files from directory."""
        self._profiles.clear()
        for filepath in self.profiles_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    prof = Profile.from_dict(data)
                    key_name = filepath.stem.lower()
                    self._profiles[key_name] = prof
                    logger.info(f"Loaded profile: {prof.name} ({len(prof.items)} items)")
            except Exception as e:
                logger.error(f"Error loading profile {filepath}: {e}")

    def _create_default_profile(self) -> None:
        """Generate default 8-slice profile for V1 in Turkish."""
        default_items = [
            SliceItem("item_1", "Terminal", "terminal", "#2ED573", AppAction("a1", "Terminal", params={"command": "konsole || gnome-terminal || xterm"}), "Sistem Terminalini Aç"),
            SliceItem("item_2", "Tarayıcı", "globe", "#2ED573", UrlAction("a2", "Tarayıcı", params={"url": "https://google.com"}), "İnternet Tarayıcısını Aç"),
            SliceItem("item_3", "VS Code", "code", "#2ED573", AppAction("a3", "VS Code", params={"command": "code"}), "Visual Studio Code Aç"),
            SliceItem("item_4", "Sistem Bilgisi", "cpu", "#2ED573", ShellAction("a4", "Sistem Bilgisi", params={"command": "kinfocenter || gnome-system-monitor"}), "Sistem İzleyiciyi Göster"),
            SliceItem("item_5", "Kopyala", "copy", "#2ED573", ShortcutAction("a5", "Kopyala", params={"keys": "ctrl+c"}), "Seçili Alanı Kopyala"),
            SliceItem("item_6", "Yapıştır", "clipboard", "#2ED573", ShortcutAction("a6", "Yapıştır", params={"keys": "ctrl+v"}), "Panodan Yapıştır"),
            SliceItem("item_7", "GitHub", "github", "#2ED573", UrlAction("a7", "GitHub", params={"url": "https://github.com"}), "GitHub Sayfasını Aç"),
            SliceItem("item_8", "Metin Yaz", "type", "#2ED573", TextAction("a8", "Metin Yaz", params={"text": "Orbit Dairesel Menüden Merhaba!"}), "Karşılama Metni Yazdır"),
        ]

        def_prof = Profile("Varsayılan", default_items, accent_color="#2ED573", description="Varsayılan 8 dilimli verimlilik çemberi")
        self.save_profile("default", def_prof)
        self._profiles["default"] = def_prof

    def save_profile(self, name: str, profile: Profile) -> None:
        """Saves a profile object to JSON file."""
        filepath = self.profiles_dir / f"{name.lower()}.json"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(profile.to_dict(), f, indent=4)
            self._profiles[name.lower()] = profile
        except Exception as e:
            logger.error(f"Failed to save profile '{name}': {e}")

    def set_active_profile(self, name: str) -> bool:
        """Switch current active profile."""
        key = name.lower()
        if key in self._profiles:
            self._active_profile = self._profiles[key]
            self.event_bus.publish(ProfileChangedEvent(self._active_profile.name))
            logger.info(f"Active profile set to '{self._active_profile.name}'")
            return True
        return False

    def get_active_profile(self) -> Profile:
        """Return currently active profile (or default fallback)."""
        if not self._active_profile:
            if "default" in self._profiles:
                self._active_profile = self._profiles["default"]
            else:
                self._create_default_profile()
                self._active_profile = self._profiles["default"]
        return self._active_profile

    def get_default_profile(self) -> Profile:
        """Return default system profile."""
        if "default" in self._profiles:
            return self._profiles["default"]
        return self.get_active_profile()

    def get_profile_for_app(self, app_exe: str) -> Profile:
        """Find profile bound to the given application executable name, or fallback to default."""
        if app_exe:
            for key, prof in self._profiles.items():
                if key != "default" and prof.matches_app(app_exe):
                    logger.info(f"Matched profile '{prof.name}' for app '{app_exe}'")
                    return prof

        return self.get_default_profile()



    def list_profiles(self) -> List[str]:
        return list(self._profiles.keys())
