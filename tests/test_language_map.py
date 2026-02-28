#!/usr/bin/env python3
"""Unit tests for language_map.py module."""

import sys
import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from data.language_map import EN_TO_ZH, ZH_TO_EN, translate_widget_tree


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

    # ── New localization coverage ──────────────────────────────────

    def test_zh_to_en_reverse_map_complete(self):
        """Every EN→ZH entry has a corresponding ZH→EN entry."""
        for en, zh in EN_TO_ZH.items():
            assert zh in ZH_TO_EN, f"ZH_TO_EN missing reverse for '{en}' → '{zh}'"
            assert ZH_TO_EN[zh] == en

    def test_emoji_prefixed_buttons_translated(self):
        """Buttons that carry emoji prefixes must be in the map."""
        emoji_buttons = [
            "🔴 Delete Selected",
            "🟢 Add Customer",
            "🟢 Add Truck",
            "🟢 Create Contract",
            "⬇ Export XLSX",
        ]
        for btn in emoji_buttons:
            assert btn in EN_TO_ZH, f"Emoji button '{btn}' not in map"

    def test_dashboard_kpi_strings_translated(self):
        """Dashboard KPI labels are translated."""
        for key in ("As of:", "Refresh KPI", "Total Active Contracts",
                     "Expected This Month", "Total Outstanding",
                     "Overdue 30+ Days", "Oldest Unpaid Invoice"):
            assert key in EN_TO_ZH, f"Dashboard string '{key}' missing"

    def test_dashboard_search_headings_translated(self):
        """Dashboard search-tree headings are in the map."""
        for key in ("Type", "Match", "Detail"):
            assert key in EN_TO_ZH, f"Dashboard heading '{key}' missing"

    def test_statement_strings_translated(self):
        """Statement tab strings are translated."""
        for key in ("Chart:", "Expected Monthly Revenue (Last 12 Months)"):
            assert key in EN_TO_ZH, f"Statement string '{key}' missing"

    def test_dialog_labels_translated(self):
        """All dialog labels added for dialogs are translated."""
        dialog_keys = [
            "Plate:", "(customer-level)", "Outstanding Balance:",
            "Amount:", "Payment Date:", "Method:", "Reference:",
            "Notes:", "Cancel", "Select", "Confirm Import",
            "Search customer:", "Import Preview", "Contract Details",
            "Paid Date", "Invoice Month", "Ledger Entries",
            "Entry", "Date / Period", "Billed", "Scope / Method",
            "Notes / Reference", "Rate ($/mo)", "Start Date",
        ]
        for key in dialog_keys:
            assert key in EN_TO_ZH, f"Dialog label '{key}' missing"

    def test_theme_label_translated(self):
        """Top bar Theme: label is translated."""
        assert "Theme:" in EN_TO_ZH

    def test_trucks_parked_translated(self):
        """Trucks tab 'Trucks Parked' label is translated."""
        assert "Trucks Parked" in EN_TO_ZH

    def test_translate_widget_tree_to_zh(self):
        """translate_widget_tree converts English labels to Chinese."""
        root = MagicMock()
        child = MagicMock()
        child.cget.return_value = "Cancel"
        child.winfo_children.return_value = []
        root.cget.return_value = "Select"
        root.winfo_children.return_value = [child]

        translate_widget_tree(root, "zh")

        root.configure.assert_called_once_with(text="选择")
        child.configure.assert_called_once_with(text="取消")

    def test_translate_widget_tree_to_en(self):
        """translate_widget_tree converts Chinese labels back to English."""
        root = MagicMock()
        root.cget.return_value = "取消"
        root.winfo_children.return_value = []

        translate_widget_tree(root, "en")

        root.configure.assert_called_once_with(text="Cancel")

    def test_translate_widget_tree_skips_unknown(self):
        """translate_widget_tree ignores text not in the map."""
        root = MagicMock()
        root.cget.return_value = "something_unknown_xyz"
        root.winfo_children.return_value = []

        translate_widget_tree(root, "zh")

        root.configure.assert_not_called()

    def test_translate_widget_tree_handles_cget_error(self):
        """translate_widget_tree does not crash if cget raises."""
        root = MagicMock()
        root.cget.side_effect = Exception("no text option")
        root.winfo_children.return_value = []

        # Should not raise
        translate_widget_tree(root, "zh")


if __name__ == "__main__":
    unittest.main()
