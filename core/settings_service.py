from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

_logger = logging.getLogger("changsheng_app")


class SettingsService:
    def __init__(self, settings_path: str):
        self._path = Path(settings_path)

    def load(self) -> dict:
        try:
            with self._path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return {}
        except (json.JSONDecodeError, ValueError) as exc:
            # Settings file is corrupted — back it up before returning defaults
            _logger.warning("Settings file corrupted (%s), backing up and using defaults", exc)
            try:
                backup = self._path.with_suffix(".json.corrupt")
                self._path.rename(backup)
            except Exception:
                pass
            return {}
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def save(self, settings: dict) -> None:
        # Atomic write: write to temp file then replace
        dir_path = self._path.parent
        dir_path.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(settings, file, ensure_ascii=False, indent=2)
            os.replace(tmp_path, str(self._path))
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

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

    def get_auto_backup_dir(self, settings: dict) -> str | None:
        value = settings.get("auto_backup_dir")
        return value if isinstance(value, str) and value else None

    def set_auto_backup_dir(self, settings: dict, dir_path: str) -> bool:
        if not dir_path:
            return False
        settings["auto_backup_dir"] = str(dir_path)
        return True
