from __future__ import annotations

import json
from pathlib import Path


class SettingsService:
    def __init__(self, settings_path: str):
        self._path = Path(settings_path)

    def load(self) -> dict:
        try:
            with self._path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def save(self, settings: dict) -> None:
        with self._path.open("w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False, indent=2)

    def get_last_backup_dir(self, settings: dict) -> str | None:
        value = settings.get("last_backup_dir")
        return value if isinstance(value, str) and value else None

    def set_last_backup_dir(self, settings: dict, file_path: str) -> bool:
        path = Path(str(file_path))
        parent = str(path.parent) if str(path.parent) not in {"", "."} else None
        if not parent:
            return False
        settings["last_backup_dir"] = parent
        return True
