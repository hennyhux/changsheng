#!/usr/bin/env python3
"""Tests for UX polish changes: Escape bindings, Return bindings, center helper,
scrollbar in picker, and placeholder additions."""

import re
import sys
import inspect
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCenterDialogOnParent(unittest.TestCase):
    """Test the center_dialog_on_parent helper logic."""

    def test_centers_on_parent(self):
        from ui.ui_helpers import center_dialog_on_parent

        parent = MagicMock()
        parent.update_idletasks = MagicMock()
        parent.winfo_rootx.return_value = 100
        parent.winfo_rooty.return_value = 50
        parent.winfo_width.return_value = 1280
        parent.winfo_height.return_value = 800

        dialog = MagicMock()
        dialog.update_idletasks = MagicMock()
        dialog.winfo_screenwidth.return_value = 1920
        dialog.winfo_screenheight.return_value = 1080

        center_dialog_on_parent(dialog, parent, 400, 300)

        call_args = dialog.geometry.call_args[0][0]
        # Should contain computed position
        self.assertRegex(call_args, r"400x300\+\d+\+\d+")
        # Parse position
        match = re.match(r"(\d+)x(\d+)\+(\d+)\+(\d+)", call_args)
        self.assertIsNotNone(match)
        x, y = int(match.group(3)), int(match.group(4))
        # Expected: parent_x + (parent_w - dialog_w) / 2 = 100 + (1280-400)//2 = 540
        # Expected: parent_y + (parent_h - dialog_h) / 2 = 50  + (800-300)//2  = 300
        self.assertEqual(x, 540)
        self.assertEqual(y, 300)

    def test_falls_back_to_screen_center(self):
        from ui.ui_helpers import center_dialog_on_parent

        parent = MagicMock()
        parent.update_idletasks.side_effect = Exception("no display")

        dialog = MagicMock()
        dialog.update_idletasks = MagicMock()
        dialog.winfo_screenwidth.return_value = 1920
        dialog.winfo_screenheight.return_value = 1080

        center_dialog_on_parent(dialog, parent, 600, 400)

        call_args = dialog.geometry.call_args[0][0]
        match = re.match(r"(\d+)x(\d+)\+(\d+)\+(\d+)", call_args)
        self.assertIsNotNone(match)
        x, y = int(match.group(3)), int(match.group(4))
        self.assertEqual(x, 660)  # (1920-600)//2
        self.assertEqual(y, 340)  # (1080-400)//2


class TestDialogEscapeBindings(unittest.TestCase):
    """Verify all dialogs bind <Escape> to close."""

    def _source_contains_escape_bind(self, module_path: str) -> bool:
        src = Path(module_path).read_text(encoding="utf-8")
        return bool(re.search(r'\.bind\(\s*["\']<Escape>["\']', src))

    def test_contract_edit_has_escape(self):
        self.assertTrue(self._source_contains_escape_bind(
            "dialogs/contract_edit_dialog.py"))

    def test_customer_picker_has_escape(self):
        self.assertTrue(self._source_contains_escape_bind(
            "dialogs/customer_picker.py"))

    def test_import_preview_has_escape(self):
        self.assertTrue(self._source_contains_escape_bind(
            "dialogs/import_preview_dialog.py"))

    def test_payment_popup_has_escape(self):
        self.assertTrue(self._source_contains_escape_bind(
            "dialogs/payment_popup.py"))

    def test_payment_history_has_escape(self):
        self.assertTrue(self._source_contains_escape_bind(
            "dialogs/payment_history_dialog.py"))

    def test_edit_customer_has_escape(self):
        self.assertTrue(self._source_contains_escape_bind(
            "ui/ui_actions.py"))


class TestDialogReturnBindings(unittest.TestCase):
    """Verify key dialogs bind <Return> to submit."""

    def test_contract_edit_return_to_save(self):
        src = Path("dialogs/contract_edit_dialog.py").read_text(encoding="utf-8")
        self.assertIn("<Return>", src)
        self.assertIn("_save_contract", src)

    def test_edit_customer_return_to_save(self):
        src = Path("ui/ui_actions.py").read_text(encoding="utf-8")
        matches = re.findall(r'bind\(["\']<Return>["\'].*_save_customer', src)
        self.assertGreaterEqual(len(matches), 4, "All 4 customer entry fields should bind Return")


class TestDialogCentering(unittest.TestCase):
    """Verify dialogs call center_dialog_on_parent."""

    def _source_calls_center(self, path: str) -> bool:
        src = Path(path).read_text(encoding="utf-8")
        return "center_dialog_on_parent" in src

    def test_contract_edit_centered(self):
        self.assertTrue(self._source_calls_center("dialogs/contract_edit_dialog.py"))

    def test_customer_picker_centered(self):
        self.assertTrue(self._source_calls_center("dialogs/customer_picker.py"))

    def test_import_preview_centered(self):
        self.assertTrue(self._source_calls_center("dialogs/import_preview_dialog.py"))

    def test_payment_history_centered(self):
        self.assertTrue(self._source_calls_center("dialogs/payment_history_dialog.py"))

    def test_edit_customer_centered(self):
        self.assertTrue(self._source_calls_center("ui/ui_actions.py"))


class TestCustomerPickerScrollbar(unittest.TestCase):
    """Customer picker tree should have a vertical scrollbar."""

    def test_scrollbar_present(self):
        src = Path("dialogs/customer_picker.py").read_text(encoding="utf-8")
        self.assertIn("Scrollbar", src)
        self.assertIn("yscrollcommand", src)


class TestSearchPlaceholders(unittest.TestCase):
    """Verify placeholder text on search entries missing them before."""

    def test_overdue_search_placeholder(self):
        src = Path("tabs/overdue_tab.py").read_text(encoding="utf-8")
        self.assertIn("add_placeholder(app.overdue_search", src)

    def test_invoice_search_placeholder(self):
        src = Path("tabs/invoices_tab.py").read_text(encoding="utf-8")
        self.assertIn("add_placeholder(app.invoice_customer_search", src)

    def test_contract_search_placeholder(self):
        src = Path("tabs/contracts_tab.py").read_text(encoding="utf-8")
        self.assertIn("add_placeholder(app.contract_search", src)

    def test_contract_search_label_cleaned(self):
        src = Path("tabs/contracts_tab.py").read_text(encoding="utf-8")
        self.assertNotIn("(Search by name)", src, "Old parenthetical label should be replaced")


if __name__ == "__main__":
    unittest.main()
