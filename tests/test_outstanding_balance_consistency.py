#!/usr/bin/env python3
"""Regression tests for shared outstanding-balance calculations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import inspect
import unittest
from datetime import date
from unittest.mock import MagicMock

from utils.outstanding_balance import compute_contract_balance
from ui.ui_actions import get_contract_outstanding_as_of_action
import invoicing.invoice_generator as invoice_generator
import invoicing.ledger_export as ledger_export
import ui.ui_actions as ui_actions


class TestOutstandingBalanceHelper(unittest.TestCase):
    def test_compute_contract_balance_clamps_overpayment_to_zero(self):
        balance = compute_contract_balance(
            monthly_rate=500.0,
            start_date_value="2024-01-01",
            end_date_value=None,
            paid_total=2000.0,
            as_of_date=date(2024, 1, 31),
        )

        self.assertIsNotNone(balance)
        self.assertEqual(balance.months_elapsed, 1)
        self.assertAlmostEqual(balance.expected_amount, 500.0)
        self.assertAlmostEqual(balance.outstanding, 0.0)

    def test_get_contract_outstanding_as_of_action_uses_shared_clamped_balance(self):
        db = MagicMock()
        db.get_contract_snapshot.return_value = {
            "monthly_rate": 500.0,
            "start_date": "2024-01-01",
            "end_date": None,
        }
        db.get_paid_total_for_contract_as_of.return_value = 2000.0

        outstanding = get_contract_outstanding_as_of_action(db, 7, date(2024, 1, 31))

        self.assertAlmostEqual(outstanding, 0.0)


class TestOutstandingBalanceConsistency(unittest.TestCase):
    def test_invoice_generator_uses_shared_helper(self):
        src = inspect.getsource(invoice_generator)
        self.assertIn("compute_contract_balance", src)
        self.assertNotIn("outstanding = max(0.0, expected_amount - paid_total)", src)
        self.assertNotIn("outstanding = max(0.0, expected - paid)", src)

    def test_ledger_export_uses_shared_helper(self):
        src = inspect.getsource(ledger_export)
        self.assertIn("compute_contract_balance", src)
        self.assertNotIn("outstanding = billed - total_paid", src)

    def test_contract_summary_views_stop_using_inline_outstanding_math(self):
        src = inspect.getsource(ui_actions.refresh_contracts_action)
        self.assertIn("compute_contract_balance", src)
        self.assertNotIn("outstanding_amt = expected - paid_by_contract.get", src)

        src = inspect.getsource(ui_actions.refresh_customers_action)
        self.assertIn("compute_contract_balance", src)
        self.assertNotIn("outstanding = expected - paid_by_contract.get", src)

        src = inspect.getsource(ui_actions.refresh_trucks_action)
        self.assertIn("compute_contract_balance", src)
        self.assertNotIn("outstanding_amt = expected - paid_by_contract.get", src)


if __name__ == "__main__":
    unittest.main()
