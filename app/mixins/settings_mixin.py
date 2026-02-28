from __future__ import annotations

from core.app_logging import get_app_logger
from core.config import SETTINGS_FILE
from core.settings_service import SettingsService

logger = get_app_logger()


class SettingsMixin:
    def _settings_service(self) -> SettingsService:
        if not hasattr(self, "_settings_service_instance"):
            self._settings_service_instance = SettingsService(SETTINGS_FILE)
        return self._settings_service_instance

    def _load_app_settings(self) -> dict:
        return self._settings_service().load()

    def _save_app_settings(self) -> None:
        try:
            self._settings_service().save(self._app_settings)
        except Exception as exc:
            logger.warning(f"Failed to save app settings: {exc}")

    def _get_last_backup_dir(self) -> str | None:
        return self._settings_service().get_last_backup_dir(self._app_settings)

    def _set_last_backup_dir(self, file_path: str) -> None:
        try:
            changed = self._settings_service().set_last_backup_dir(self._app_settings, file_path)
        except Exception:
            changed = False
        if changed:
            self._save_app_settings()

    def _get_auto_backup_dir(self) -> str | None:
        return self._settings_service().get_auto_backup_dir(self._app_settings)

    def _set_auto_backup_dir(self, dir_path: str) -> None:
        try:
            changed = self._settings_service().set_auto_backup_dir(self._app_settings, dir_path)
        except Exception:
            changed = False
        if changed:
            self._save_app_settings()
