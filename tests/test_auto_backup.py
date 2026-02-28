#!/usr/bin/env python3
"""Tests for auto-backup on startup with directory prompt and rotation."""

import os
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mixins.backup_startup_mixin import BackupStartupMixin
from core.config import AUTO_BACKUP_MAX_COPIES
from core.settings_service import SettingsService


# ---------------------------------------------------------------------------
# Config constant
# ---------------------------------------------------------------------------

class TestAutoBackupMaxCopiesConstant(unittest.TestCase):
    def test_constant_is_20(self):
        self.assertEqual(AUTO_BACKUP_MAX_COPIES, 20)


# ---------------------------------------------------------------------------
# SettingsService – auto_backup_dir accessors
# ---------------------------------------------------------------------------

class TestSettingsServiceAutoBackupDir(unittest.TestCase):
    def test_get_auto_backup_dir_empty_settings(self):
        svc = SettingsService("dummy.json")
        self.assertIsNone(svc.get_auto_backup_dir({}))

    def test_get_auto_backup_dir_returns_value(self):
        svc = SettingsService("dummy.json")
        settings = {"auto_backup_dir": "C:/backups"}
        self.assertEqual(svc.get_auto_backup_dir(settings), "C:/backups")

    def test_get_auto_backup_dir_ignores_non_string(self):
        svc = SettingsService("dummy.json")
        self.assertIsNone(svc.get_auto_backup_dir({"auto_backup_dir": 123}))

    def test_get_auto_backup_dir_ignores_empty_string(self):
        svc = SettingsService("dummy.json")
        self.assertIsNone(svc.get_auto_backup_dir({"auto_backup_dir": ""}))

    def test_set_auto_backup_dir_saves(self):
        svc = SettingsService("dummy.json")
        settings = {}
        result = svc.set_auto_backup_dir(settings, "C:/my_backups")
        self.assertTrue(result)
        self.assertEqual(settings["auto_backup_dir"], "C:/my_backups")

    def test_set_auto_backup_dir_rejects_empty(self):
        svc = SettingsService("dummy.json")
        settings = {}
        result = svc.set_auto_backup_dir(settings, "")
        self.assertFalse(result)
        self.assertNotIn("auto_backup_dir", settings)


# ---------------------------------------------------------------------------
# BackupStartupMixin._prompt_auto_backup_dir
# ---------------------------------------------------------------------------

class TestPromptAutoBackupDir(unittest.TestCase):
    @patch("app.mixins.backup_startup_mixin.filedialog")
    @patch("app.mixins.backup_startup_mixin.messagebox")
    def test_skips_if_dir_already_set(self, mock_mb, mock_fd):
        mixin = MagicMock(spec=BackupStartupMixin)
        mixin.current_language = "en"
        tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "test_auto_bk")
        os.makedirs(tmp, exist_ok=True)
        mixin._get_auto_backup_dir = MagicMock(return_value=tmp)

        BackupStartupMixin._prompt_auto_backup_dir(mixin)

        mock_mb.showinfo.assert_not_called()
        mock_fd.askdirectory.assert_not_called()

    @patch("app.mixins.backup_startup_mixin.filedialog")
    @patch("app.mixins.backup_startup_mixin.messagebox")
    def test_prompts_when_not_configured(self, mock_mb, mock_fd):
        mixin = MagicMock()
        mixin.current_language = "en"
        mixin._get_auto_backup_dir = MagicMock(return_value=None)
        mock_fd.askdirectory = MagicMock(return_value="C:/chosen_dir")

        BackupStartupMixin._prompt_auto_backup_dir(mixin)

        mock_mb.showinfo.assert_called_once()
        title = mock_mb.showinfo.call_args[0][0]
        self.assertEqual(title, "Set Auto-Backup Directory")
        mixin._set_auto_backup_dir.assert_called_once_with("C:/chosen_dir")

    @patch("app.mixins.backup_startup_mixin.filedialog")
    @patch("app.mixins.backup_startup_mixin.messagebox")
    def test_chinese_prompt(self, mock_mb, mock_fd):
        mixin = MagicMock()
        mixin.current_language = "zh"
        mixin._get_auto_backup_dir = MagicMock(return_value=None)
        mock_fd.askdirectory = MagicMock(return_value="")

        BackupStartupMixin._prompt_auto_backup_dir(mixin)

        title = mock_mb.showinfo.call_args[0][0]
        self.assertEqual(title, "设置自动备份目录")
        mixin._set_auto_backup_dir.assert_not_called()

    @patch("app.mixins.backup_startup_mixin.filedialog")
    @patch("app.mixins.backup_startup_mixin.messagebox")
    def test_user_cancels_prompt(self, mock_mb, mock_fd):
        mixin = MagicMock()
        mixin.current_language = "en"
        mixin._get_auto_backup_dir = MagicMock(return_value=None)
        mock_fd.askdirectory = MagicMock(return_value="")

        BackupStartupMixin._prompt_auto_backup_dir(mixin)

        mixin._set_auto_backup_dir.assert_not_called()


# ---------------------------------------------------------------------------
# BackupStartupMixin._auto_backup_on_startup
# ---------------------------------------------------------------------------

class TestAutoBackupOnStartup(unittest.TestCase):
    def test_skips_when_no_dir_configured(self):
        mixin = MagicMock()
        mixin._get_auto_backup_dir = MagicMock(return_value=None)

        BackupStartupMixin._auto_backup_on_startup(mixin)

        mixin.db.backup_to.assert_not_called()

    def test_skips_when_dir_does_not_exist(self):
        mixin = MagicMock()
        mixin._get_auto_backup_dir = MagicMock(return_value="/nonexistent/path/xyz")

        BackupStartupMixin._auto_backup_on_startup(mixin)

        mixin.db.backup_to.assert_not_called()

    def test_creates_backup_in_configured_dir(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            mixin = MagicMock(spec=BackupStartupMixin)
            mixin._get_auto_backup_dir = MagicMock(return_value=tmp)
            mixin.db = MagicMock()
            mixin._log_action = MagicMock()
            mixin._rotate_auto_backups = MagicMock()

            BackupStartupMixin._auto_backup_on_startup(mixin)

            mixin.db.backup_to.assert_called_once()
            backup_path = mixin.db.backup_to.call_args[0][0]
            self.assertTrue(backup_path.startswith(tmp))
            self.assertIn("monthly_lot_auto_", backup_path)
            self.assertTrue(backup_path.endswith(".db"))
            mixin._log_action.assert_called_once()

    def test_handles_backup_failure_gracefully(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            mixin = MagicMock(spec=BackupStartupMixin)
            mixin._get_auto_backup_dir = MagicMock(return_value=tmp)
            mixin.db = MagicMock()
            mixin.db.backup_to.side_effect = Exception("disk full")
            mixin._rotate_auto_backups = MagicMock()

            # Should not raise
            BackupStartupMixin._auto_backup_on_startup(mixin)

            mixin._rotate_auto_backups.assert_not_called()


# ---------------------------------------------------------------------------
# BackupStartupMixin._rotate_auto_backups
# ---------------------------------------------------------------------------

class TestRotateAutoBackups(unittest.TestCase):
    def test_keeps_max_copies(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            # Create 25 fake backup files with staggered mtimes
            for i in range(25):
                p = os.path.join(tmp, f"monthly_lot_auto_2026{i:04d}.db")
                with open(p, "w") as f:
                    f.write("x")
                # Ensure distinct mtimes
                os.utime(p, (1000000 + i, 1000000 + i))

            BackupStartupMixin._rotate_auto_backups(tmp, max_copies=20)

            remaining = [f for f in os.listdir(tmp) if f.startswith("monthly_lot_auto_")]
            self.assertEqual(len(remaining), 20)

    def test_no_removal_when_under_limit(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(5):
                p = os.path.join(tmp, f"monthly_lot_auto_{i:04d}.db")
                with open(p, "w") as f:
                    f.write("x")

            BackupStartupMixin._rotate_auto_backups(tmp, max_copies=20)

            remaining = [f for f in os.listdir(tmp) if f.startswith("monthly_lot_auto_")]
            self.assertEqual(len(remaining), 5)

    def test_removes_oldest_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            files = []
            for i in range(5):
                p = os.path.join(tmp, f"monthly_lot_auto_{i:04d}.db")
                with open(p, "w") as f:
                    f.write("x")
                os.utime(p, (1000000 + i, 1000000 + i))
                files.append(p)

            BackupStartupMixin._rotate_auto_backups(tmp, max_copies=3)

            remaining = sorted(os.listdir(tmp))
            self.assertEqual(len(remaining), 3)
            # Oldest two (0000, 0001) should be removed
            self.assertNotIn("monthly_lot_auto_0000.db", remaining)
            self.assertNotIn("monthly_lot_auto_0001.db", remaining)

    def test_ignores_non_matching_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            # Create non-matching files
            with open(os.path.join(tmp, "other_file.db"), "w") as f:
                f.write("x")
            # Create matching files
            for i in range(3):
                p = os.path.join(tmp, f"monthly_lot_auto_{i:04d}.db")
                with open(p, "w") as f:
                    f.write("x")

            BackupStartupMixin._rotate_auto_backups(tmp, max_copies=2)

            all_files = os.listdir(tmp)
            # other_file.db should still exist
            self.assertIn("other_file.db", all_files)
            matching = [f for f in all_files if f.startswith("monthly_lot_auto_")]
            self.assertEqual(len(matching), 2)


# ---------------------------------------------------------------------------
# SettingsMixin wrappers (integration-ish)
# ---------------------------------------------------------------------------

class TestSettingsMixinAutoBackupWrappers(unittest.TestCase):
    def test_get_auto_backup_dir_delegates(self):
        from app.mixins.settings_mixin import SettingsMixin
        mixin = MagicMock(spec=SettingsMixin)
        mixin._app_settings = {"auto_backup_dir": "/some/dir"}
        svc = MagicMock()
        svc.get_auto_backup_dir.return_value = "/some/dir"
        mixin._settings_service = MagicMock(return_value=svc)

        result = SettingsMixin._get_auto_backup_dir(mixin)
        self.assertEqual(result, "/some/dir")

    def test_set_auto_backup_dir_saves(self):
        from app.mixins.settings_mixin import SettingsMixin
        mixin = MagicMock(spec=SettingsMixin)
        mixin._app_settings = {}
        svc = MagicMock()
        svc.set_auto_backup_dir.return_value = True
        mixin._settings_service = MagicMock(return_value=svc)

        SettingsMixin._set_auto_backup_dir(mixin, "/new/dir")

        svc.set_auto_backup_dir.assert_called_once_with({}, "/new/dir")
        mixin._save_app_settings.assert_called_once()


if __name__ == "__main__":
    unittest.main()
