from __future__ import annotations

import json
from pathlib import Path

from .models import MacroProfile


def default_store_path() -> Path:
    return Path.home() / ".key-macro-studio" / "profiles.json"


class ProfileStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_store_path()

    def load_all(self) -> list[MacroProfile]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return [MacroProfile.from_dict(item) for item in data.get("profiles", [])]

    def save_all(self, profiles: list[MacroProfile]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"profiles": [profile.to_dict() for profile in profiles]}
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    @staticmethod
    def export_profile(profile: MacroProfile, path: Path) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(profile.to_dict(), file, ensure_ascii=False, indent=2)

    @staticmethod
    def import_profile(path: Path) -> MacroProfile:
        with path.open("r", encoding="utf-8") as file:
            return MacroProfile.from_dict(json.load(file))
