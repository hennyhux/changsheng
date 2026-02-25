#!/usr/bin/env python3
"""Unit tests for language_map.py module."""

import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from language_map import EN_TO_ZH


class TestLanguageMap(unittest.TestCase):
    """Test the English to Chinese translation dictionary."""

    def test_language_map_is_dict(self):
        """Test that EN_TO_ZH is a dictionary."""
        assert isinstance(EN_TO_ZH, dict)

    def test_language_map_not_empty(self):
        """Test that language map is not empty."""
        assert len(EN_TO_ZH) > 0

    def test_main_app_title_translated(self):
        """Test main app title has translation."""
        assert "Changsheng - Truck Lot Tracker" in EN_TO_ZH
        assert EN_TO_ZH["Changsheng - Truck Lot Tracker"] == "长生 - 卡车停车场管理"

    def test_dashboard_tab_translated(self):
        """Test dashboard tab translation."""
        assert "📈 Dashboard" in EN_TO_ZH
        translated = EN_TO_ZH["📈 Dashboard"]
        assert "仪表盘" in translated

    def test_customers_tab_translated(self):
        """Test customers tab translation."""
        assert "👥 Customers" in EN_TO_ZH
        translated = EN_TO_ZH["👥 Customers"]
        assert "客户" in translated

    def test_trucks_tab_translated(self):
        """Test trucks tab translation."""
        assert "🚚 Trucks" in EN_TO_ZH
        translated = EN_TO_ZH["🚚 Trucks"]
        assert "卡车" in translated

    def test_contracts_tab_translated(self):
        """Test contracts tab translation."""
        assert "📝 Contracts" in EN_TO_ZH
        translated = EN_TO_ZH["📝 Contracts"]
        assert "合同" in translated

    def test_billing_tab_translated(self):
        """Test billing tab translation."""
        assert "💵 Billing" in EN_TO_ZH
        translated = EN_TO_ZH["💵 Billing"]
        assert "账务" in translated

    def test_invoices_tab_translated(self):
        """Test invoices tab translation."""
        assert "🧾 Invoices & Payments" in EN_TO_ZH
        translated = EN_TO_ZH["🧾 Invoices & Payments"]
        assert "发票" in translated

    def test_common_buttons_translated(self):
        """Test common button labels are translated."""
        common_buttons = [
            "Search",
            "Delete Selected",
            "Add Customer",
            "Add Truck",
            "Create Contract",
            "Clear",
            "Refresh"
        ]
        for button in common_buttons:
            assert button in EN_TO_ZH, f"Button '{button}' not in translation map"
            assert EN_TO_ZH[button], f"Translation for '{button}' is empty"

    def test_form_fields_translated(self):
        """Test form field labels are translated."""
        form_fields = [
            "Name*",
            "Phone",
            "Company",
            "Notes",
            "Plate*",
            "State",
            "Make",
            "Model",
            "Customer",
        ]
        for field in form_fields:
            assert field in EN_TO_ZH, f"Field '{field}' not in translation map"
            assert EN_TO_ZH[field], f"Translation for '{field}' is empty"

    def test_no_empty_translations(self):
        """Test that no translations are empty strings."""
        for english, chinese in EN_TO_ZH.items():
            assert chinese and isinstance(chinese, str), \
                f"Empty or invalid translation for '{english}': '{chinese}'"

    def test_all_values_are_strings(self):
        """Test that all translation values are strings."""
        for english, chinese in EN_TO_ZH.items():
            assert isinstance(english, str), f"Key is not a string: {english}"
            assert isinstance(chinese, str), f"Value is not a string: {chinese}"

    def test_bidirectional_lookup(self):
        """Test that we can look up any translation."""
        sample_keys = [
            "Changsheng - Truck Lot Tracker",
            "Search",
            "Name*",
            "Language:",
        ]
        for key in sample_keys:
            assert key in EN_TO_ZH, f"Key '{key}' not found in translation map"


if __name__ == "__main__":
    unittest.main()
