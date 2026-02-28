from __future__ import annotations

import glob
import os
import shutil
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox

from core.app_logging import get_app_logger
from core.config import AUTO_BACKUP_MAX_COPIES, HISTORY_LOG_FILE
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

    # ── First-run: ask user to choose an auto-backup directory ──────

    def _prompt_auto_backup_dir(self) -> None:
        """On first launch (no auto_backup_dir in settings) ask the user to
        pick a folder for automatic database backups."""
        existing = self._get_auto_backup_dir()
        if existing and Path(existing).is_dir():
            return  # already configured

        zh = getattr(self, "current_language", "en") == "zh"
        title = "设置自动备份目录" if zh else "Set Auto-Backup Directory"
        msg = (
            "请选择一个文件夹用于自动备份数据库。\n程序每次启动时会自动备份，最多保留20份。"
            if zh else
            "Please choose a folder for automatic database backups.\n"
            "The database will be backed up every time the program starts (up to 20 copies kept)."
        )
        messagebox.showinfo(title, msg)

        chosen = filedialog.askdirectory(title=title)
        if chosen:
            self._set_auto_backup_dir(chosen)
            logger.info(f"Auto-backup directory set to: {chosen}")
        else:
            logger.info("User declined to set auto-backup directory.")

    # ── Automatic backup on startup with rotation ───────────────────

    def _auto_backup_on_startup(self) -> None:
        """Copy the database into the auto-backup directory, keeping at most
        ``AUTO_BACKUP_MAX_COPIES`` backups.  Oldest files are removed first."""
        backup_dir = self._get_auto_backup_dir()
        if not backup_dir or not Path(backup_dir).is_dir():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"monthly_lot_auto_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_name)

        try:
            self.db.backup_to(backup_path)
            logger.info(f"Auto-backup saved: {backup_path}")
            self._log_action("AUTO_BACKUP", f"Automatic backup saved to {backup_path}")
        except Exception as exc:
            logger.warning(f"Auto-backup failed: {exc}")
            return

        # Rotate: keep only the newest AUTO_BACKUP_MAX_COPIES files
        self._rotate_auto_backups(backup_dir)

    @staticmethod
    def _rotate_auto_backups(backup_dir: str,
                             max_copies: int = AUTO_BACKUP_MAX_COPIES) -> None:
        pattern = os.path.join(backup_dir, "monthly_lot_auto_*.db")
        backups = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        for stale in backups[max_copies:]:
            try:
                os.remove(stale)
                logger.info(f"Rotated old auto-backup: {stale}")
            except Exception as exc:
                logger.warning(f"Failed to remove old backup {stale}: {exc}")

    # ── Legacy startup prompt (kept for manual reminders) ───────────

    def _prompt_backup_on_startup(self):
        last_backup = self._get_last_backup_date()
        zh = getattr(self, "current_language", "en") == "zh"
        if last_backup:
            days_since = (today() - last_backup).days
            msg = (f"距离上次备份已经过去 {days_since} 天。\n现在备份数据库吗？"
                   if zh else
                   f"It has been {days_since} days since the last backup.\nBack up the database now?")
            logger.info(f"Startup backup reminder: {days_since} days since last backup.")
        else:
            msg = ("还没有备份记录。\n现在备份数据库吗？"
                   if zh else
                   "No backup records found.\nBack up the database now?")
            logger.info("Startup backup reminder: no previous backup found.")

        title = "备份提示" if zh else "Backup Reminder"
        do_backup = messagebox.askyesno(title, msg)
        logger.info(f"Startup backup prompt response: {'yes' if do_backup else 'no'}")
        if do_backup:
            self.backup_database()
