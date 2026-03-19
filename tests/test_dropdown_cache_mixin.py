#!/usr/bin/env python3
"""Tests for dropdown cache state refresh behavior."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mixins.dropdown_cache_mixin import DropdownCacheMixin
from app.mixins.customers_tab_mixin import CustomersTabMixin


class FakeCombo:
    def __init__(self, value: str = ""):
        self._value = value
        self._values = []
        self._search_all_values = []

    def __getitem__(self, key):
        if key == "values":
            return tuple(self._values)
        raise KeyError(key)

    def __setitem__(self, key, value):
        if key == "values":
            self._values = list(value)
            return
        raise KeyError(key)

    def get(self):
        return self._value

    def set(self, value: str):
        self._value = value

    def current(self, index: int):
        self._value = self._values[index]


class _App(DropdownCacheMixin):
    def __init__(self):
        self.db = None
        self.truck_customer_combo = FakeCombo()
        self.contract_customer_combo = FakeCombo()
        self.contract_truck_combo = FakeCombo()


class TestDropdownCacheMixin(unittest.TestCase):
    def test_reload_customer_dropdowns_preserves_selection_by_id(self):
        app = _App()
        app.contract_customer_combo = FakeCombo("7: Alice")
        app.db = type(
            "DB",
            (),
            {
                "get_customer_dropdown_rows": lambda _self: [
                    {"id": 7, "name": "Alice Cooper", "phone": None, "company": None},
                    {"id": 8, "name": "Bob", "phone": None, "company": None},
                ]
            },
        )()

        app._reload_customer_dropdowns()

        self.assertEqual(app.contract_customer_combo.get(), "7: Alice Cooper")

    def test_reload_customer_dropdowns_clears_stale_removed_selection(self):
        app = _App()
        app.contract_customer_combo = FakeCombo("9: Removed Customer")
        app.db = type(
            "DB",
            (),
            {
                "get_customer_dropdown_rows": lambda _self: [
                    {"id": 7, "name": "Alice", "phone": None, "company": None},
                ]
            },
        )()

        app._reload_customer_dropdowns()

        self.assertEqual(app.contract_customer_combo.get(), "")

    def test_reload_truck_dropdowns_preserves_truck_selection_by_id(self):
        app = _App()
        app.contract_customer_combo = FakeCombo("3: Alice")
        app.contract_customer_combo._search_all_values = ["3: Alice"]
        app.contract_truck_combo = FakeCombo("21: OLD-PLATE CA")
        app.db = type(
            "DB",
            (),
            {
                "get_truck_dropdown_rows": lambda _self: [
                    {"id": 21, "plate": "NEW-PLATE", "state": "CA", "customer_id": 3},
                    {"id": 22, "plate": "OTHER", "state": "NV", "customer_id": 3},
                ]
            },
        )()

        app._reload_truck_dropdowns()

        self.assertEqual(app.contract_truck_combo.get(), "21: NEW-PLATE CA")

    def test_reload_truck_dropdowns_clears_invalid_stale_selection(self):
        app = _App()
        app.contract_customer_combo = FakeCombo("3: Alice")
        app.contract_customer_combo._search_all_values = ["3: Alice"]
        app.contract_truck_combo = FakeCombo("99: Removed Truck")
        app.db = type(
            "DB",
            (),
            {
                "get_truck_dropdown_rows": lambda _self: [
                    {"id": 21, "plate": "ACTIVE-TRUCK", "state": "CA", "customer_id": 3},
                ]
            },
        )()

        app._reload_truck_dropdowns()

        self.assertEqual(app.contract_truck_combo.get(), "")


class TestCustomerSelectionSync(unittest.TestCase):
    def test_set_selected_customer_refreshes_dependent_contract_trucks(self):
        class App(CustomersTabMixin):
            def __init__(self):
                self.truck_customer_combo = object()
                self.contract_customer_combo = object()
                self.contract_truck_combo = object()
                self.calls = []

            def _set_combo_by_customer_id(self, combo, customer_id):
                self.calls.append(("set_combo", combo, customer_id))

            def _filter_contract_trucks(self, customer_id):
                self.calls.append(("filter_trucks", customer_id))

        app = App()

        app._set_selected_customer(42)

        self.assertIn(("filter_trucks", 42), app.calls)


if __name__ == "__main__":
    unittest.main()