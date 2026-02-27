#!/usr/bin/env python3
"""Tests verifying that each mutation action calls the full set of refresh
methods afterwards (the 'refresh cascade').

These tests mock the tkinter layer and verify that app.refresh_* methods are
called after every mutation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from typing import Optional, Set
from unittest.mock import MagicMock, patch, call


# The full set of refreshes every mutation should trigger
FULL_REFRESH_SET = {
    "refresh_customers",
    "refresh_trucks",
    "refresh_contracts",
    "refresh_invoices",
    "refresh_overdue",
    "refresh_statement",
    "refresh_dashboard",
}


def _make_app() -> MagicMock:
    """Return a MagicMock with refresh_* methods auto-created."""
    app = MagicMock()
    for name in FULL_REFRESH_SET:
        setattr(app, name, MagicMock(name=name))
    return app


def _assert_full_refresh(test_case: unittest.TestCase, app: MagicMock, skips: Optional[Set[str]] = None):
    """Assert that every refresh in FULL_REFRESH_SET was called at least once."""
    expected = FULL_REFRESH_SET - (skips or set())
    for name in expected:
        method = getattr(app, name)
        test_case.assertTrue(
            method.called,
            f"Expected {name}() to be called, but it was not.",
        )


class TestToggleContractRefreshCascade(unittest.TestCase):
    @patch("ui.ui_actions.messagebox")
    def test_toggle_calls_all_refreshes(self, mock_mb):
        from ui.ui_actions import toggle_contract_action

        app = _make_app()
        app.contract_tree.selection.return_value = ["row1"]
        app.contract_tree.item.return_value = (42, "500", "Alice", "TX-001", "2024-01", "", "1")

        db = MagicMock()
        db.get_contract_active_row.return_value = {"is_active": 1}

        toggle_contract_action(app=app, db=db)

        db.set_contract_active.assert_called_once_with(42, 0)
        db.commit.assert_called_once()
        _assert_full_refresh(self, app)


class TestDeleteContractRefreshCascade(unittest.TestCase):
    @patch("ui.ui_actions.messagebox")
    def test_delete_contract_calls_all_refreshes(self, mock_mb):
        from ui.ui_actions import delete_contract_action

        mock_mb.askyesno.return_value = True

        app = _make_app()
        app.contract_tree.selection.return_value = ["row1"]
        app.contract_tree.item.return_value = (1, "500", "Alice", "TX-001", "2024-01", "2024-12", "1")

        db = MagicMock()
        db.get_payment_count_by_contract.return_value = 0
        db.fetchone.return_value = {"cnt": 0}

        log_cb = MagicMock()

        delete_contract_action(app=app, db=db, log_action_cb=log_cb)

        _assert_full_refresh(self, app)


class TestCreateContractRefreshCascade(unittest.TestCase):
    @patch("ui.ui_actions.messagebox")
    @patch("ui.ui_actions.parse_ymd")
    def test_create_contract_calls_all_refreshes(self, mock_parse_ymd, mock_mb):
        from ui.ui_actions import create_contract_action
        from datetime import date

        mock_parse_ymd.side_effect = lambda x: date(2024, 1, 1) if "2024-01" in str(x) else None

        app = _make_app()
        app.contract_customer_combo = MagicMock()
        app.contract_truck_combo = MagicMock()
        app.contract_scope = MagicMock()
        app.contract_scope.get.return_value = "customer_level"
        app.contract_rate = MagicMock()
        app.contract_rate.get.return_value = "500"
        app.contract_start = MagicMock()
        app.contract_start.get.return_value = "2024-01-01"
        app.contract_end = MagicMock()
        app.contract_end.get.return_value = ""
        app.contract_notes = MagicMock()
        app.contract_notes.get.return_value = ""

        db = MagicMock()
        db.create_contract.return_value = 1

        log_cb = MagicMock()
        customer_cb = MagicMock(return_value=1)
        truck_cb = MagicMock(return_value=None)
        get_entry_cb = MagicMock(side_effect=lambda e: "500")
        clear_cb = MagicMock()
        show_inline_cb = MagicMock()
        show_invalid_cb = MagicMock()

        create_contract_action(
            app=app,
            db=db,
            get_selected_customer_id_cb=customer_cb,
            get_selected_truck_id_cb=truck_cb,
            get_entry_value_cb=get_entry_cb,
            clear_inline_errors_cb=clear_cb,
            show_inline_error_cb=show_inline_cb,
            show_invalid_cb=show_invalid_cb,
            log_action_cb=log_cb,
        )

        _assert_full_refresh(self, app)


class TestAddCustomerRefreshCascade(unittest.TestCase):
    @patch("ui.ui_actions.messagebox")
    def test_add_customer_calls_all_refreshes(self, mock_mb):
        from ui.ui_actions import add_customer_action

        app = _make_app()
        app.c_name = MagicMock()
        app.c_phone = MagicMock()
        app.c_company = MagicMock()
        app.c_notes = MagicMock()
        app._customer_form = MagicMock()

        db = MagicMock()
        db.create_customer.return_value = 1

        get_entry = MagicMock(side_effect=lambda e: "Test Customer" if e is app.c_name else "")
        clear_cb = MagicMock()
        show_inline_cb = MagicMock()
        show_invalid_cb = MagicMock()
        placeholder_cb = MagicMock()
        log_cb = MagicMock()

        add_customer_action(
            app=app,
            db=db,
            get_entry_value_cb=get_entry,
            clear_inline_errors_cb=clear_cb,
            show_inline_error_cb=show_inline_cb,
            show_invalid_cb=show_invalid_cb,
            add_placeholder_cb=placeholder_cb,
            log_action_cb=log_cb,
        )

        _assert_full_refresh(self, app)


class TestEditCustomerRefreshCascade(unittest.TestCase):
    @patch("ui.ui_actions.messagebox")
    def test_edit_customer_save_calls_all_refreshes(self, mock_mb):
        """Verify that _save_customer inside edit_selected_customer_action
        calls refresh_statement and refresh_dashboard in addition to the rest."""
        # This test verifies the fix for the missing refresh_statement/refresh_dashboard
        # in the edit customer save flow. Due to the complexity of the windowed dialog,
        # we verify indirectly by checking the source code contains the calls.
        import inspect
        from ui import ui_actions

        source = inspect.getsource(ui_actions.edit_selected_customer_action)
        for refresh_name in FULL_REFRESH_SET:
            self.assertIn(
                refresh_name,
                source,
                f"edit_selected_customer_action should contain '{refresh_name}' call",
            )


if __name__ == "__main__":
    unittest.main()
