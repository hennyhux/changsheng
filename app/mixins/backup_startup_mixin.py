from __future__ import annotations

from datetime import date, datetime
from tkinter import messagebox

from core.app_logging import get_app_logger
from core.config import HISTORY_LOG_FILE
from utils.billing_date_utils import today


logger = get_app_logger()


class BackupStartupMixin:
    def _ensure_history_log_exists(self) -> None:
        try:
            with open(HISTORY_LOG_FILE, "a+", encoding="utf-8") as file_handle:
                file_handle.seek(0, 2)
                if file_handle.tell() == 0:
                    file_handle.write("# Truck Lot History Log (auto-created)\n")
        except Exception as exc:
            logger.warning(f"Failed to ensure history log exists: {exc}")

    def _get_last_backup_date(self) -> date | None:
        self._ensure_history_log_exists()
        try:
            with open(HISTORY_LOG_FILE, "r", encoding="utf-8") as file_handle:
                lines = file_handle.read().splitlines()
        except Exception as exc:
            logger.warning(f"Failed to read history log for backup check: {exc}")
            return None

        for line in reversed(lines):
            if "BACKUP_DB" not in line:
                continue
            try:
                timestamp_str = line.split("]", 1)[0].lstrip("[")
                backup_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                backup_date = backup_dt.date()
                logger.info(f"Last backup date parsed: {backup_date.isoformat()}")
                return backup_date
            except Exception:
                continue
        return None

    def _prompt_backup_on_startup(self):
        last_backup = self._get_last_backup_date()
        if last_backup:
            days_since = (today() - last_backup).days
            msg = f"距离上次备份已经过去 {days_since} 天。\n现在备份数据库吗？"
            logger.info(f"Startup backup reminder: {days_since} days since last backup.")
        else:
            msg = "还没有备份记录。\n现在备份数据库吗？"
            logger.info("Startup backup reminder: no previous backup found.")

        do_backup = messagebox.askyesno("备份提示", msg)
        logger.info(f"Startup backup prompt response: {'yes' if do_backup else 'no'}")
        if do_backup:
            self.backup_database()
