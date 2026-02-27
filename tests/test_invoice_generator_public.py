#!/usr/bin/env python3
"""Unit tests for the public functions in invoice_generator.py:
   build_invoice_groups() and build_pdf_invoice_data().
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from datetime import date
from typing import Optional
from unittest.mock import MagicMock, patch, PropertyMock

from invoicing.invoice_generator import (
    build_invoice_groups,
    build_pdf_invoice_data,
    _build_contract_line,
    _next_due_after,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row(overrides: Optional[dict] = None) -> dict:
    """Return a minimal active-contract row dict, optionally overridden."""
    base = {
        "contract_id": 1,
        "customer_id": 100,
        "customer_name": "Alice",
        "monthly_rate": 500.0,
        "start_date": "2024-01-15",
        "end_date": "",
        "plate": "TX-001",
    }
    if overrides:
        base.update(overrides)
    return base


def _make_db(**kwargs) -> MagicMock:
    """Return a MagicMock DatabaseService with sensible defaults."""
    db = MagicMock()
    db.get_active_contracts_with_customer_plate_for_invoices.return_value = kwargs.get(
        "invoice_rows", []
    )
    db.get_paid_total_for_contract_as_of.return_value = kwargs.get("paid_total", 0.0)
    db.get_customer_basic_by_id.return_value = kwargs.get(
        "customer_row", {"id": 100, "name": "Alice", "phone": "555", "company": "Co"}
    )
    db.get_active_contracts_for_customer_invoice.return_value = kwargs.get(
        "customer_contracts", []
    )
    db.get_paid_totals_by_customer_as_of.return_value = kwargs.get(
        "paid_by_customer", []
    )
    db.get_recent_payments_for_customer.return_value = kwargs.get(
        "recent_payments", []
    )
    return db


# ---------------------------------------------------------------------------
# _build_contract_line
# ---------------------------------------------------------------------------

class TestBuildContractLine(unittest.TestCase):
    """Tests for the internal _build_contract_line helper."""

    def test_basic_one_month(self):
        """Contract started 2024-01-15, as_of 2024-01-20 → 1 month elapsed."""
        db = _make_db(paid_total=0.0)
        line = _build_contract_line(db, _row(), date(2024, 1, 20))
        self.assertIsNotNone(line)
        self.assertEqual(line.months_elapsed, 1)
        self.assertAlmostEqual(line.expected_amount, 500.0)
        self.assertAlmostEqual(line.outstanding, 500.0)
        self.assertEqual(line.status, "DUE")

    def test_fully_paid(self):
        db = _make_db(paid_total=500.0)
        line = _build_contract_line(db, _row(), date(2024, 1, 20))
        self.assertIsNotNone(line)
        self.assertAlmostEqual(line.outstanding, 0.0)
        self.assertEqual(line.status, "PAID")

    def test_overpayment_still_paid_status(self):
        """If paid > expected, outstanding goes negative but status is PAID."""
        db = _make_db(paid_total=1500.0)
        line = _build_contract_line(db, _row(), date(2024, 1, 20))
        self.assertIsNotNone(line)
        self.assertLessEqual(line.outstanding, 0.01)
        self.assertEqual(line.status, "PAID")

    def test_end_date_caps_expected(self):
        """When end_date < as_of, expected should be capped at end_date."""
        row = _row({"start_date": "2024-01-01", "end_date": "2024-03-01"})
        db = _make_db(paid_total=0.0)
        line = _build_contract_line(db, row, date(2025, 1, 1))
        self.assertIsNotNone(line)
        # effective_end = min(2024-03-01, 2025-01-01) = 2024-03-01
        # elapsed = 3 months (Jan, Feb, Mar)
        self.assertEqual(line.months_elapsed, 3)
        self.assertAlmostEqual(line.expected_amount, 1500.0)

    def test_end_date_after_as_of_uses_as_of(self):
        """When end_date > as_of, effective_end = as_of."""
        row = _row({"start_date": "2024-01-01", "end_date": "2026-01-01"})
        db = _make_db(paid_total=0.0)
        line = _build_contract_line(db, row, date(2024, 3, 1))
        self.assertIsNotNone(line)
        self.assertEqual(line.months_elapsed, 3)

    def test_missing_start_date_returns_none(self):
        row = _row({"start_date": ""})
        db = _make_db()
        line = _build_contract_line(db, row, date(2024, 6, 1))
        self.assertIsNone(line)

    def test_invalid_start_date_returns_none(self):
        row = _row({"start_date": "not-a-date"})
        db = _make_db()
        line = _build_contract_line(db, row, date(2024, 6, 1))
        self.assertIsNone(line)

    def test_scope_fallback_to_customer_level(self):
        """When plate is None, scope should be '(customer-level)'."""
        row = _row({"plate": None})
        db = _make_db(paid_total=0.0)
        line = _build_contract_line(db, row, date(2024, 2, 1))
        self.assertEqual(line.scope, "(customer-level)")


# ---------------------------------------------------------------------------
# build_invoice_groups
# ---------------------------------------------------------------------------

class TestBuildInvoiceGroups(unittest.TestCase):
    """Tests for the public build_invoice_groups function."""

    def test_empty_contracts(self):
        db = _make_db(invoice_rows=[])
        groups, total = build_invoice_groups(db, date(2024, 6, 1))
        self.assertEqual(groups, [])
        self.assertAlmostEqual(total, 0.0)

    def test_single_customer_single_contract(self):
        rows = [_row()]
        db = _make_db(invoice_rows=rows, paid_total=0.0)
        groups, total = build_invoice_groups(db, date(2024, 2, 1))
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].customer_name, "Alice")
        self.assertEqual(len(groups[0].contracts), 1)
        self.assertEqual(groups[0].status, "DUE")

    def test_two_customers_sorted_alphabetically(self):
        rows = [
            _row({"customer_id": 1, "customer_name": "Zara", "contract_id": 10}),
            _row({"customer_id": 2, "customer_name": "Alice", "contract_id": 20}),
        ]
        db = _make_db(invoice_rows=rows, paid_total=0.0)
        groups, _ = build_invoice_groups(db, date(2024, 2, 1))
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0].customer_name, "Alice")
        self.assertEqual(groups[1].customer_name, "Zara")

    def test_customer_with_all_paid(self):
        rows = [_row()]
        db = _make_db(invoice_rows=rows, paid_total=5000.0)
        groups, total = build_invoice_groups(db, date(2024, 2, 1))
        self.assertEqual(groups[0].status, "PAID")
        self.assertLessEqual(total, 0.01)

    def test_multiple_contracts_same_customer(self):
        rows = [
            _row({"contract_id": 1, "plate": "TX-001"}),
            _row({"contract_id": 2, "plate": "TX-002"}),
        ]
        db = _make_db(invoice_rows=rows, paid_total=0.0)
        groups, _ = build_invoice_groups(db, date(2024, 2, 1))
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0].contracts), 2)

    def test_skips_invalid_start_date_rows(self):
        rows = [_row({"start_date": "invalid"})]
        db = _make_db(invoice_rows=rows)
        groups, total = build_invoice_groups(db, date(2024, 6, 1))
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0].contracts), 0)


# ---------------------------------------------------------------------------
# build_pdf_invoice_data
# ---------------------------------------------------------------------------

class TestBuildPdfInvoiceData(unittest.TestCase):
    """Tests for build_pdf_invoice_data."""

    def test_customer_not_found_returns_none(self):
        db = _make_db(customer_row=None)
        result = build_pdf_invoice_data(db, 999, date(2024, 6, 1))
        self.assertIsNone(result)

    def test_no_contracts_returns_empty(self):
        db = _make_db(customer_contracts=[], paid_by_customer=[], recent_payments=[])
        result = build_pdf_invoice_data(db, 100, date(2024, 6, 1))
        self.assertIsNotNone(result)
        self.assertEqual(result.contracts, [])
        self.assertAlmostEqual(result.total_expected, 0.0)
        self.assertIsNone(result.next_due_date)

    def test_single_contract_outstanding(self):
        contract_rows = [
            {"id": 1, "monthly_rate": 300.0, "start_date": "2024-01-01", "end_date": "", "plate": "TX-1"}
        ]
        db = _make_db(
            customer_contracts=contract_rows,
            paid_by_customer=[],
            recent_payments=[],
        )
        result = build_pdf_invoice_data(db, 100, date(2024, 3, 1))
        self.assertIsNotNone(result)
        self.assertEqual(len(result.contracts), 1)
        self.assertAlmostEqual(result.total_expected, 900.0)  # 3 months * 300
        self.assertAlmostEqual(result.total_paid, 0.0)
        self.assertAlmostEqual(result.total_outstanding, 900.0)

    def test_end_date_caps_expected_in_pdf(self):
        contract_rows = [
            {"id": 1, "monthly_rate": 200.0, "start_date": "2024-01-01", "end_date": "2024-02-01", "plate": "TX-1"}
        ]
        db = _make_db(
            customer_contracts=contract_rows,
            paid_by_customer=[],
            recent_payments=[],
        )
        # as_of far in the future, but end_date caps at 2024-02-01
        result = build_pdf_invoice_data(db, 100, date(2025, 1, 1))
        self.assertIsNotNone(result)
        # effective_end = min(2024-02-01, 2025-01-01) = 2024-02-01
        # elapsed = 2 months (Jan, Feb)
        self.assertAlmostEqual(result.total_expected, 400.0)

    def test_paid_by_customer_reduces_outstanding(self):
        contract_rows = [
            {"id": 5, "monthly_rate": 100.0, "start_date": "2024-01-01", "end_date": "", "plate": "TX-1"}
        ]
        paid = [{"contract_id": 5, "paid_total": 200.0}]
        db = _make_db(
            customer_contracts=contract_rows,
            paid_by_customer=paid,
            recent_payments=[],
        )
        result = build_pdf_invoice_data(db, 100, date(2024, 3, 1))
        self.assertAlmostEqual(result.total_paid, 200.0)
        self.assertAlmostEqual(result.total_outstanding, 100.0)  # 300 expected - 200 paid

    def test_invoice_uuid_is_present(self):
        db = _make_db(customer_contracts=[], paid_by_customer=[], recent_payments=[])
        result = build_pdf_invoice_data(db, 100, date(2024, 6, 1))
        self.assertTrue(len(result.invoice_uuid) > 0)

    def test_recent_payments_included(self):
        payment_rows = [
            {
                "paid_at": "2024-02-01",
                "amount": 100.0,
                "method": "cash",
                "contract_id": 1,
                "plate": "TX-1",
                "reference": "REF-1",
                "notes": "",
            }
        ]
        db = _make_db(
            customer_contracts=[],
            paid_by_customer=[],
            recent_payments=payment_rows,
        )
        result = build_pdf_invoice_data(db, 100, date(2024, 6, 1))
        self.assertEqual(len(result.recent_payments), 1)
        self.assertAlmostEqual(result.recent_payments[0].amount, 100.0)
        self.assertEqual(result.recent_payments[0].method, "cash")

    def test_next_due_date_calculated(self):
        contract_rows = [
            {"id": 1, "monthly_rate": 100.0, "start_date": "2024-01-15", "end_date": "", "plate": "TX-1"}
        ]
        db = _make_db(
            customer_contracts=contract_rows,
            paid_by_customer=[],
            recent_payments=[],
        )
        result = build_pdf_invoice_data(db, 100, date(2024, 3, 1))
        self.assertIsNotNone(result.next_due_date)


# ---------------------------------------------------------------------------
# _next_due_after
# ---------------------------------------------------------------------------

class TestNextDueAfter(unittest.TestCase):
    def test_as_of_before_start(self):
        result = _next_due_after(date(2024, 3, 15), date(2024, 2, 1))
        self.assertEqual(result, date(2024, 3, 15))

    def test_as_of_same_day_as_start(self):
        result = _next_due_after(date(2024, 3, 15), date(2024, 3, 15))
        self.assertEqual(result, date(2024, 3, 15))

    def test_as_of_after_start_same_month(self):
        result = _next_due_after(date(2024, 3, 15), date(2024, 3, 20))
        # as_of.day (20) > start.day (15), so next month
        self.assertEqual(result, date(2024, 4, 15))

    def test_year_wrap(self):
        result = _next_due_after(date(2024, 1, 10), date(2024, 12, 20))
        self.assertEqual(result, date(2025, 1, 10))


if __name__ == "__main__":
    unittest.main()
