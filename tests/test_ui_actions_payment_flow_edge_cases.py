#!/usr/bin/env python3
"""Edge-case tests for payment-related UI actions."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest

from ui.ui_actions import (
    open_payment_form_for_contract_action,
    open_payment_form_window_action,
    record_payment_for_selected_truck_action,
)


class _MockEntry:
    def __init__(self, value: str):
        self._value = value

    def get(self) -> str:
        return self._value


class TestRecordPaymentForSelectedTruckEdgeCases(unittest.TestCase):
    def test_uses_selected_row_plate_label(self):
        app = MagicMock()
        app.truck_tree.selection.return_value = ["row1"]
        app.truck_tree.item.return_value = ("12", "TX-ABC-123", "TX")

        db = MagicMock()
        db.get_preferred_contract_for_truck.return_value = {
            "contract_id": 42,
            "plate": "TX-ABC-123",
        }

        open_form = MagicMock()

        record_payment_for_selected_truck_action(
            app=app,
            db=db,
            open_payment_form_for_contract_cb=open_form,
        )

        open_form.assert_called_once_with(42, "TX-ABC-123", None)

    def test_falls_back_to_contract_plate_when_row_plate_missing(self):
        app = MagicMock()
        app.truck_tree.selection.return_value = ["row1"]
        app.truck_tree.item.return_value = ("12", "")

        db = MagicMock()
        db.get_preferred_contract_for_truck.return_value = {
            "contract_id": 77,
            "plate": "CA-999",
        }

        open_form = MagicMock()

        record_payment_for_selected_truck_action(
            app=app,
            db=db,
            open_payment_form_for_contract_cb=open_form,
        )

        open_form.assert_called_once_with(77, "CA-999", None)

    @patch("ui.ui_actions.messagebox.showinfo")
    def test_no_contract_shows_info_and_does_not_open_form(self, mock_info):
        app = MagicMock()
        app.truck_tree.selection.return_value = ["row1"]
        app.truck_tree.item.return_value = ("99", "TX-NA")

        db = MagicMock()
        db.get_preferred_contract_for_truck.return_value = None

        open_form = MagicMock()

        record_payment_for_selected_truck_action(
            app=app,
            db=db,
            open_payment_form_for_contract_cb=open_form,
        )

        open_form.assert_not_called()
        mock_info.assert_called_once()


class TestOpenPaymentFormWindowEdgeCases(unittest.TestCase):
    @patch("ui.ui_actions.messagebox.showinfo")
    def test_parent_row_rejected_when_contract_id_not_numeric(self, mock_info):
        app = MagicMock()
        app.invoice_tree.selection.return_value = ["parent"]
        app.invoice_tree.item.return_value = ("", "Acme Inc", "", "", "", "", "", "", "", "")
        app.invoice_date = _MockEntry("2026-02-01")

        open_form = MagicMock()

        open_payment_form_window_action(
            app=app,
            open_payment_form_for_contract_cb=open_form,
        )

        open_form.assert_not_called()
        mock_info.assert_called_once()

    def test_passes_none_as_of_when_invoice_date_invalid(self):
        app = MagicMock()
        app.invoice_tree.selection.return_value = ["child"]
        app.invoice_tree.item.return_value = ("123", "", "PLATE-1", "$100.00", "", "", "", "", "", "$10.00")
        app.invoice_date = _MockEntry("not-a-date")

        open_form = MagicMock()

        open_payment_form_window_action(
            app=app,
            open_payment_form_for_contract_cb=open_form,
        )

        args = open_form.call_args[0]
        self.assertEqual(args[0], 123)
        self.assertEqual(args[1], "PLATE-1")
        self.assertIsNone(args[2])

    def test_defaults_to_customer_level_when_scope_empty(self):
        app = MagicMock()
        app.invoice_tree.selection.return_value = ["child"]
        app.invoice_tree.item.return_value = ("321", "", "", "$100.00", "", "", "", "", "", "$10.00")
        app.invoice_date = _MockEntry("2026-02-01")

        open_form = MagicMock()

        open_payment_form_window_action(
            app=app,
            open_payment_form_for_contract_cb=open_form,
        )

        args = open_form.call_args[0]
        self.assertEqual(args[0], 321)
        self.assertEqual(args[1], "(customer-level)")


class TestOpenPaymentFormForContractPosting(unittest.TestCase):
    @patch("ui.ui_actions.messagebox.showinfo")
    @patch("ui.ui_actions.show_payment_popup")
    def test_anchors_invoice_to_paid_at_month(self, mock_popup, _mock_info):
        app = MagicMock()
        app.refresh_customers = MagicMock()
        app.refresh_contracts = MagicMock()
        app.refresh_trucks = MagicMock()
        app.refresh_invoices = MagicMock()
        app.refresh_statement = MagicMock()
        app.refresh_overdue = MagicMock()
        app.refresh_dashboard = MagicMock()
        app.refresh_histories = MagicMock()

        db = MagicMock()
        db.contract_exists.return_value = True
        db.conn = MagicMock()

        outstanding_cb = MagicMock(side_effect=[100.0, 100.0])
        get_anchor_cb = MagicMock(return_value=111)
        log_action_cb = MagicMock()

        def _submit_from_popup(*args, **kwargs):
            on_submit = args[5]
            ok = on_submit("10", "2026-02-15", "cash", "", "")
            self.assertTrue(ok)

        mock_popup.side_effect = _submit_from_popup

        open_payment_form_for_contract_action(
            app=app,
            db=db,
            contract_id=7,
            plate_label="TX-1",
            as_of_date=date(2026, 3, 1),
            get_contract_outstanding_as_of_cb=outstanding_cb,
            get_or_create_anchor_invoice_cb=get_anchor_cb,
            log_action_cb=log_action_cb,
        )

        db.execute.assert_any_call("BEGIN IMMEDIATE")
        get_anchor_cb.assert_called_once_with(7, date(2026, 2, 15))
        db.create_payment.assert_called_once()
        db.commit.assert_called_once()

    @patch("ui.ui_actions.messagebox.showerror")
    @patch("ui.ui_actions.show_payment_popup")
    def test_rejects_overpayment_above_outstanding(self, mock_popup, mock_error):
        app = MagicMock()
        db = MagicMock()
        db.contract_exists.return_value = True
        db.conn = MagicMock()

        outstanding_cb = MagicMock(side_effect=[100.0, 100.0])
        get_anchor_cb = MagicMock(return_value=111)
        log_action_cb = MagicMock()

        def _submit_from_popup(*args, **kwargs):
            on_submit = args[5]
            ok = on_submit("150", "2026-03-01", "cash", "", "")
            self.assertFalse(ok)

        mock_popup.side_effect = _submit_from_popup

        open_payment_form_for_contract_action(
            app=app,
            db=db,
            contract_id=7,
            plate_label="TX-1",
            as_of_date=date(2026, 3, 1),
            get_contract_outstanding_as_of_cb=outstanding_cb,
            get_or_create_anchor_invoice_cb=get_anchor_cb,
            log_action_cb=log_action_cb,
        )

        db.execute.assert_any_call("BEGIN IMMEDIATE")
        db.conn.rollback.assert_called_once()
        db.create_payment.assert_not_called()
        get_anchor_cb.assert_not_called()
        mock_error.assert_called()


if __name__ == "__main__":
    unittest.main()
