#!/usr/bin/env python3
"""Unit tests exercising DatabaseService API methods (not raw SQL)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import tempfile
import unittest
from datetime import datetime

from data.database_service import DatabaseService


class _DBTestCase(unittest.TestCase):
    """Base class that sets up a fresh in-memory-style temp DB per test."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseService(self.db_path)
        self._now = datetime.now().isoformat()

    def tearDown(self):
        self.db.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    # -- helpers --
    def _add_customer(self, name="Test Customer"):
        return self.db.create_customer(name, "555-0000", "TestCo", None, self._now)

    def _add_truck(self, customer_id, plate="TX-001"):
        return self.db.create_truck(customer_id, plate, "TX", "Ford", "F-150", None, self._now)

    def _add_contract(self, customer_id, truck_id=None, rate=500.0,
                      start="2024-01-01", end=None, active=1):
        return self.db.create_contract(
            customer_id, truck_id, rate,
            start[:7], end[:7] if end else None,
            start, end, active, None, self._now,
        )

    def _add_payment(self, contract_id, amount, paid_at="2024-02-01"):
        inv_id = self.db.get_or_create_anchor_invoice(
            contract_id, paid_at[:7], paid_at, self._now
        )
        self.db.create_payment(inv_id, paid_at, amount, "cash", "", "")
        self.db.commit()
        return inv_id


# ---------------------------------------------------------------------------
# Customer CRUD
# ---------------------------------------------------------------------------

class TestCustomerCRUD(_DBTestCase):
    def test_create_and_get_customer(self):
        cid = self._add_customer("Alice")
        self.db.commit()
        row = self.db.get_customer_basic_by_id(cid)
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Alice")

    def test_update_customer(self):
        cid = self._add_customer("Alice")
        self.db.commit()
        self.db.update_customer(cid, "Bob", "999", "NewCo", "note")
        self.db.commit()
        row = self.db.get_customer_basic_by_id(cid)
        self.assertEqual(row["name"], "Bob")
        self.assertEqual(row["phone"], "999")

    def test_delete_customer(self):
        cid = self._add_customer("Doomed")
        self.db.commit()
        self.db.delete_customer(cid)
        self.db.commit()
        row = self.db.get_customer_basic_by_id(cid)
        self.assertIsNone(row)


# ---------------------------------------------------------------------------
# Contract operations
# ---------------------------------------------------------------------------

class TestContractOperations(_DBTestCase):
    def test_create_contract(self):
        cid = self._add_customer()
        self.db.commit()
        ct_id = self._add_contract(cid, rate=750.0)
        self.db.commit()
        self.assertTrue(self.db.contract_exists(ct_id))

    def test_toggle_contract_active(self):
        cid = self._add_customer()
        ct_id = self._add_contract(cid)
        self.db.commit()
        row = self.db.get_contract_active_row(ct_id)
        self.assertEqual(row["is_active"], 1)

        self.db.set_contract_active(ct_id, 0)
        self.db.commit()
        row = self.db.get_contract_active_row(ct_id)
        self.assertEqual(row["is_active"], 0)

    def test_contract_exists_false_for_missing(self):
        self.assertFalse(self.db.contract_exists(99999))


# ---------------------------------------------------------------------------
# Payment queries
# ---------------------------------------------------------------------------

class TestPaidTotals(_DBTestCase):
    def test_get_paid_total_for_contract_as_of(self):
        cid = self._add_customer()
        ct = self._add_contract(cid)
        self.db.commit()
        self._add_payment(ct, 200.0, "2024-02-01")
        self._add_payment(ct, 300.0, "2024-03-01")

        total = self.db.get_paid_total_for_contract_as_of(ct, "2024-02-15")
        self.assertAlmostEqual(total, 200.0)

        total_all = self.db.get_paid_total_for_contract_as_of(ct, "2024-12-31")
        self.assertAlmostEqual(total_all, 500.0)

    def test_get_paid_total_for_contract_no_payments(self):
        cid = self._add_customer()
        ct = self._add_contract(cid)
        self.db.commit()
        total = self.db.get_paid_total_for_contract_as_of(ct, "2024-12-31")
        self.assertAlmostEqual(total, 0.0)

    def test_get_paid_totals_by_customer_as_of(self):
        cid = self._add_customer()
        ct1 = self._add_contract(cid, rate=100.0)
        ct2 = self._add_contract(cid, rate=200.0)
        self.db.commit()
        self._add_payment(ct1, 50.0, "2024-01-15")
        self._add_payment(ct2, 75.0, "2024-01-20")

        rows = self.db.get_paid_totals_by_customer_as_of(cid, "2024-01-31")
        paid_map = {int(r["contract_id"]): float(r["paid_total"]) for r in rows}
        self.assertAlmostEqual(paid_map.get(ct1, 0), 50.0)
        self.assertAlmostEqual(paid_map.get(ct2, 0), 75.0)

    def test_get_paid_totals_by_customer_excludes_other_customers(self):
        c1 = self._add_customer("Alice")
        c2 = self._add_customer("Bob")
        ct1 = self._add_contract(c1)
        ct2 = self._add_contract(c2)
        self.db.commit()
        self._add_payment(ct1, 100.0)
        self._add_payment(ct2, 200.0)

        rows = self.db.get_paid_totals_by_customer_as_of(c1, "2024-12-31")
        paid_map = {int(r["contract_id"]): float(r["paid_total"]) for r in rows}
        self.assertIn(ct1, paid_map)
        self.assertNotIn(ct2, paid_map)

    def test_get_paid_totals_by_customer_empty(self):
        cid = self._add_customer()
        self.db.commit()
        rows = self.db.get_paid_totals_by_customer_as_of(cid, "2024-12-31")
        self.assertEqual(len(rows), 0)

    def test_get_paid_totals_by_contract_as_of(self):
        c = self._add_customer()
        ct = self._add_contract(c)
        self.db.commit()
        self._add_payment(ct, 300.0, "2024-03-01")

        rows = self.db.get_paid_totals_by_contract_as_of("2024-03-01")
        paid_map = {int(r["contract_id"]): float(r["paid_total"]) for r in rows}
        self.assertAlmostEqual(paid_map.get(ct, 0), 300.0)

    def test_as_of_date_filtering(self):
        """Payments after as_of date should not be included."""
        c = self._add_customer()
        ct = self._add_contract(c)
        self.db.commit()
        self._add_payment(ct, 100.0, "2024-01-15")
        self._add_payment(ct, 100.0, "2024-06-15")

        rows = self.db.get_paid_totals_by_customer_as_of(c, "2024-03-01")
        paid_map = {int(r["contract_id"]): float(r["paid_total"]) for r in rows}
        self.assertAlmostEqual(paid_map.get(ct, 0), 100.0)


# ---------------------------------------------------------------------------
# get_or_create_anchor_invoice
# ---------------------------------------------------------------------------

class TestGetOrCreateAnchorInvoice(_DBTestCase):
    def test_creates_invoice_when_none_exist(self):
        cid = self._add_customer()
        ct = self._add_contract(cid)
        self.db.commit()
        inv_id = self.db.get_or_create_anchor_invoice(ct, "2024-01", "2024-01-15", self._now)
        self.assertGreater(inv_id, 0)

    def test_returns_existing_invoice(self):
        cid = self._add_customer()
        ct = self._add_contract(cid)
        self.db.commit()
        inv1 = self.db.get_or_create_anchor_invoice(ct, "2024-01", "2024-01-15", self._now)
        inv2 = self.db.get_or_create_anchor_invoice(ct, "2024-02", "2024-02-15", self._now)
        # Should reuse the existing invoice
        self.assertEqual(inv1, inv2)


# ---------------------------------------------------------------------------
# delete_payments_by_contract
# ---------------------------------------------------------------------------

class TestDeletePaymentsByContract(_DBTestCase):
    def test_deletes_all_payments_for_contract(self):
        cid = self._add_customer()
        ct = self._add_contract(cid)
        self.db.commit()
        self._add_payment(ct, 100.0, "2024-01-01")
        self._add_payment(ct, 200.0, "2024-02-01")

        total_before = self.db.get_paid_total_for_contract_as_of(ct, "2024-12-31")
        self.assertAlmostEqual(total_before, 300.0)

        self.db.delete_payments_by_contract(ct)
        self.db.commit()

        total_after = self.db.get_paid_total_for_contract_as_of(ct, "2024-12-31")
        self.assertAlmostEqual(total_after, 0.0)

    def test_delete_payments_does_not_affect_other_contracts(self):
        cid = self._add_customer()
        ct1 = self._add_contract(cid, rate=100.0)
        ct2 = self._add_contract(cid, rate=200.0)
        self.db.commit()
        self._add_payment(ct1, 50.0)
        self._add_payment(ct2, 75.0)

        self.db.delete_payments_by_contract(ct1)
        self.db.commit()

        self.assertAlmostEqual(
            self.db.get_paid_total_for_contract_as_of(ct2, "2024-12-31"), 75.0
        )


# ---------------------------------------------------------------------------
# payment_count_by_contract
# ---------------------------------------------------------------------------

class TestPaymentCountByContract(_DBTestCase):
    def test_count_with_payments(self):
        cid = self._add_customer()
        ct = self._add_contract(cid)
        self.db.commit()
        self._add_payment(ct, 100.0, "2024-01-01")
        self._add_payment(ct, 100.0, "2024-02-01")
        count = self.db.get_payment_count_by_contract(ct)
        self.assertEqual(count, 2)

    def test_count_no_payments(self):
        cid = self._add_customer()
        ct = self._add_contract(cid)
        self.db.commit()
        count = self.db.get_payment_count_by_contract(ct)
        self.assertEqual(count, 0)


# ---------------------------------------------------------------------------
# get_recent_payments_for_customer
# ---------------------------------------------------------------------------

class TestRecentPaymentsForCustomer(_DBTestCase):
    def test_returns_payments_in_desc_order(self):
        cid = self._add_customer()
        ct = self._add_contract(cid)
        self.db.commit()
        self._add_payment(ct, 100.0, "2024-01-01")
        self._add_payment(ct, 200.0, "2024-03-01")

        rows = self.db.get_recent_payments_for_customer(cid, limit=10)
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(float(rows[0]["amount"]), 200.0)  # most recent first
        self.assertAlmostEqual(float(rows[1]["amount"]), 100.0)

    def test_respects_limit(self):
        cid = self._add_customer()
        ct = self._add_contract(cid)
        self.db.commit()
        for i in range(5):
            self._add_payment(ct, 10.0 * (i + 1), f"2024-0{i + 1}-01")
        rows = self.db.get_recent_payments_for_customer(cid, limit=2)
        self.assertEqual(len(rows), 2)

    def test_empty_for_no_payments(self):
        cid = self._add_customer()
        self.db.commit()
        rows = self.db.get_recent_payments_for_customer(cid, limit=5)
        self.assertEqual(len(rows), 0)


# ---------------------------------------------------------------------------
# customer name / id by contract
# ---------------------------------------------------------------------------

class TestCustomerByContract(_DBTestCase):
    def test_get_customer_name_by_contract(self):
        cid = self._add_customer("Alice")
        ct = self._add_contract(cid)
        self.db.commit()
        name = self.db.get_customer_name_by_contract(ct)
        self.assertEqual(name, "Alice")

    def test_get_customer_name_missing_contract(self):
        name = self.db.get_customer_name_by_contract(99999)
        self.assertIsNone(name)

    def test_get_customer_id_by_contract(self):
        cid = self._add_customer()
        ct = self._add_contract(cid)
        self.db.commit()
        result = self.db.get_customer_id_by_contract(ct)
        self.assertEqual(result, cid)


if __name__ == "__main__":
    unittest.main()
