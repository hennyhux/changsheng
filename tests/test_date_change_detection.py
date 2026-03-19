#!/usr/bin/env python3
"""Tests for midnight date rollover detection and refresh."""

import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mixins.date_change_detection_mixin import (  # noqa: E402
    DateChangeDetectionMixin,
    _MIDNIGHT_CHECK_INTERVAL_MS,
)


class _CloseTracker:
    def __init__(self):
        self.close_calls: list[bool] = []

    def on_close(self, force: bool = False):
        self.close_calls.append(force)


class MockApp(DateChangeDetectionMixin, _CloseTracker):
    """Minimal app class for testing date change detection."""

    def __init__(self):
        super().__init__()
        self._after_id = 100
        self._midnight_check_id = None
        self._date_change_detection_active = False
        self.refresh_customers = MagicMock()
        self.refresh_trucks = MagicMock()
        self.refresh_contracts = MagicMock()
        self.refresh_invoices = MagicMock()
        self.refresh_dashboard = MagicMock()
        self.refresh_statement = MagicMock()
        self.refresh_overdue = MagicMock()
        self.after = MagicMock(side_effect=self._next_after_id)
        self.after_cancel = MagicMock()

    def _next_after_id(self, _delay, _callback):
        self._after_id += 1
        return self._after_id


class TestDateChangeDetectionMixin(unittest.TestCase):
    """Test automated date change detection and view refresh."""

    @patch("app.mixins.date_change_detection_mixin.today")
    def test_init_stores_current_date_and_schedules_check(self, mock_today):
        mock_today.return_value = date(2026, 3, 18)
        app = MockApp()

        app._init_date_change_detection()

        self.assertTrue(app._date_change_detection_active)
        self.assertEqual(app._app_date, date(2026, 3, 18))
        app.after.assert_called_once_with(
            _MIDNIGHT_CHECK_INTERVAL_MS,
            app._check_for_midnight_rollover,
        )
        self.assertEqual(app._midnight_check_id, 101)

    def test_schedule_midnight_check_replaces_existing_timer(self):
        app = MockApp()
        app._date_change_detection_active = True
        app._midnight_check_id = 77

        app._schedule_midnight_check()

        app.after_cancel.assert_called_once_with(77)
        app.after.assert_called_once_with(
            _MIDNIGHT_CHECK_INTERVAL_MS,
            app._check_for_midnight_rollover,
        )
        self.assertEqual(app._midnight_check_id, 101)

    @patch("app.mixins.date_change_detection_mixin.today")
    def test_check_for_midnight_no_change_only_reschedules(self, mock_today):
        current_date = date(2026, 3, 18)
        mock_today.return_value = current_date

        app = MockApp()
        app._date_change_detection_active = True
        app._app_date = current_date
        app._midnight_check_id = 88

        app._check_for_midnight_rollover()

        self.assertEqual(app._app_date, current_date)
        app.refresh_customers.assert_not_called()
        app.refresh_trucks.assert_not_called()
        app.refresh_contracts.assert_not_called()
        app.refresh_invoices.assert_not_called()
        app.refresh_dashboard.assert_not_called()
        app.refresh_statement.assert_not_called()
        app.refresh_overdue.assert_not_called()
        app.after.assert_called_once_with(
            _MIDNIGHT_CHECK_INTERVAL_MS,
            app._check_for_midnight_rollover,
        )
        self.assertEqual(app._midnight_check_id, 101)

    @patch("app.mixins.date_change_detection_mixin.today")
    def test_check_for_midnight_detects_change_and_refreshes_all(self, mock_today):
        old_date = date(2026, 3, 18)
        new_date = date(2026, 3, 19)
        mock_today.return_value = new_date

        app = MockApp()
        app._date_change_detection_active = True
        app._app_date = old_date
        app._midnight_check_id = 88

        app._check_for_midnight_rollover()

        self.assertEqual(app._app_date, new_date)
        app.refresh_customers.assert_called_once()
        app.refresh_trucks.assert_called_once()
        app.refresh_contracts.assert_called_once()
        app.refresh_invoices.assert_called_once()
        app.refresh_dashboard.assert_called_once()
        app.refresh_statement.assert_called_once()
        app.refresh_overdue.assert_called_once()
        app.after.assert_called_once_with(
            _MIDNIGHT_CHECK_INTERVAL_MS,
            app._check_for_midnight_rollover,
        )
        self.assertEqual(app._midnight_check_id, 101)

    def test_refresh_for_date_change_continues_after_one_failure(self):
        app = MockApp()
        app.refresh_dashboard.side_effect = RuntimeError("UI error")

        app._refresh_for_date_change()

        app.refresh_customers.assert_called_once()
        app.refresh_trucks.assert_called_once()
        app.refresh_contracts.assert_called_once()
        app.refresh_invoices.assert_called_once()
        app.refresh_dashboard.assert_called_once()
        app.refresh_statement.assert_called_once()
        app.refresh_overdue.assert_called_once()

    @patch("app.mixins.date_change_detection_mixin.today")
    def test_inactive_check_does_not_refresh_or_reschedule(self, mock_today):
        mock_today.return_value = date(2026, 3, 19)

        app = MockApp()
        app._date_change_detection_active = False
        app._app_date = date(2026, 3, 18)
        app._midnight_check_id = 88

        app._check_for_midnight_rollover()

        app.after.assert_not_called()
        app.after_cancel.assert_not_called()
        app.refresh_customers.assert_not_called()
        self.assertEqual(app._midnight_check_id, 88)

    def test_on_close_disables_detection_cancels_timer_and_delegates(self):
        app = MockApp()
        app._date_change_detection_active = True
        app._midnight_check_id = 55

        app.on_close(force=True)

        self.assertFalse(app._date_change_detection_active)
        app.after_cancel.assert_called_once_with(55)
        self.assertIsNone(app._midnight_check_id)
        self.assertEqual(app.close_calls, [True])


class TestMidnightDetectionIntegration(unittest.TestCase):
    """Integration-style tests with real mixin behavior."""

    @patch("app.mixins.date_change_detection_mixin.today")
    def test_full_midnight_detection_flow(self, mock_today):
        original_date = date(2026, 3, 18)
        new_date = date(2026, 3, 19)

        app = MockApp()
        mock_today.return_value = original_date
        app._init_date_change_detection()

        mock_today.return_value = new_date
        app.after.reset_mock()
        app._check_for_midnight_rollover()

        self.assertEqual(app._app_date, new_date)
        self.assertEqual(app.refresh_customers.call_count, 1)
        self.assertEqual(app.refresh_trucks.call_count, 1)
        self.assertEqual(app.refresh_contracts.call_count, 1)
        self.assertEqual(app.refresh_invoices.call_count, 1)
        self.assertEqual(app.refresh_dashboard.call_count, 1)
        self.assertEqual(app.refresh_statement.call_count, 1)
        self.assertEqual(app.refresh_overdue.call_count, 1)
        app.after.assert_called_once_with(
            _MIDNIGHT_CHECK_INTERVAL_MS,
            app._check_for_midnight_rollover,
        )

    @patch("app.mixins.date_change_detection_mixin.today")
    def test_state_preserved_across_multiple_checks(self, mock_today):
        app = MockApp()
        app._date_change_detection_active = True
        app._app_date = date(2026, 3, 18)

        mock_today.return_value = date(2026, 3, 18)
        app._check_for_midnight_rollover()
        self.assertEqual(app._app_date, date(2026, 3, 18))

        mock_today.return_value = date(2026, 3, 19)
        app._check_for_midnight_rollover()
        self.assertEqual(app._app_date, date(2026, 3, 19))

        mock_today.return_value = date(2026, 3, 19)
        app._check_for_midnight_rollover()
        self.assertEqual(app._app_date, date(2026, 3, 19))
        self.assertEqual(app.refresh_customers.call_count, 1)
        self.assertEqual(app.refresh_trucks.call_count, 1)
        self.assertEqual(app.refresh_contracts.call_count, 1)
        self.assertEqual(app.refresh_invoices.call_count, 1)
        self.assertEqual(app.refresh_dashboard.call_count, 1)
        self.assertEqual(app.refresh_statement.call_count, 1)
        self.assertEqual(app.refresh_overdue.call_count, 1)
        self.assertEqual(app.after.call_count, 3)


if __name__ == "__main__":
    unittest.main()
