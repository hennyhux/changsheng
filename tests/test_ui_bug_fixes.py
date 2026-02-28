#!/usr/bin/env python3
"""Unit tests for 10 UI bug fixes applied in the UI scan session.

Each TestCase class covers one specific fix, validating the root cause
has been eliminated and regressions are caught.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# 1. PDF thread lambda captures exc eagerly (PEP 3110 fix)
# ---------------------------------------------------------------------------
class TestPdfLambdaExcCapture(unittest.TestCase):
    """The `except Exception as exc:` block must eagerly evaluate the error
    message into a local variable *before* passing it to a lambda.
    Python 3 deletes `exc` after the except block exits (PEP 3110), so a
    late-binding closure would raise NameError and permanently jam
    `_pdf_export_in_progress = True`.
    """

    def test_error_msg_eagerly_bound(self):
        """Verify source code uses `error_msg = f\"...{exc}\"` before the lambda."""
        import inspect
        import ui.ui_actions as mod

        source = inspect.getsource(mod.generate_customer_invoice_pdf_for_customer_id_action)
        # The fix stores the string before the lambda
        self.assertIn("error_msg", source)
        # Should NOT have the old pattern where exc is used inside the lambda
        self.assertNotIn('lambda: _on_complete(False, f"Could not generate PDF:\\n{exc}")', source)

    @patch("ui.ui_actions.messagebox")
    @patch("ui.ui_actions.threading")
    @patch("ui.ui_actions.filedialog")
    def test_pdf_in_progress_flag_reset_on_outer_error(self, mock_fd, mock_threading, mock_msg):
        """If the outer try raises, _pdf_export_in_progress must be reset."""
        from ui.ui_actions import generate_customer_invoice_pdf_for_customer_id_action

        app = MagicMock()
        app._pdf_export_in_progress = False
        db = MagicMock()

        # filedialog.asksaveasfilename raises to hit the outer except
        mock_fd.asksaveasfilename.side_effect = RuntimeError("dialog crash")

        generate_customer_invoice_pdf_for_customer_id_action(
            app, db, customer_id=1,
            build_pdf_invoice_data_cb=MagicMock(),
            reportlab_available_cb=MagicMock(return_value=True),
            render_invoice_pdf_cb=MagicMock(),
        )

        # Must be reset even on crash
        self.assertFalse(app._pdf_export_in_progress)


# ---------------------------------------------------------------------------
# 2. toggle_contract_action guards empty values
# ---------------------------------------------------------------------------
class TestToggleContractEmptyValues(unittest.TestCase):
    """Right-clicking an empty tree row (no values tuple) must not crash."""

    @patch("ui.ui_actions.messagebox")
    def test_empty_values_shows_error(self, mock_msg):
        from ui.ui_actions import toggle_contract_action

        app = MagicMock()
        app.contract_tree.selection.return_value = ("I001",)
        # item(sel[0], "values") returns the values directly
        app.contract_tree.item.return_value = ()  # empty tuple
        db = MagicMock()

        toggle_contract_action(app, db)

        mock_msg.showerror.assert_called_once()
        # Must not attempt int() on empty tuple
        db.get_contract_active_row.assert_not_called()

    @patch("ui.ui_actions.messagebox")
    def test_no_selection_warns(self, mock_msg):
        from ui.ui_actions import toggle_contract_action

        app = MagicMock()
        app.contract_tree.selection.return_value = ()
        db = MagicMock()

        toggle_contract_action(app, db)

        mock_msg.showwarning.assert_called_once()

    @patch("ui.ui_actions.messagebox")
    def test_none_values_shows_error(self, mock_msg):
        from ui.ui_actions import toggle_contract_action

        app = MagicMock()
        app.contract_tree.selection.return_value = ("I001",)
        # item(sel[0], "values") returns None
        app.contract_tree.item.return_value = None
        db = MagicMock()

        toggle_contract_action(app, db)

        mock_msg.showerror.assert_called_once()
        db.get_contract_active_row.assert_not_called()


# ---------------------------------------------------------------------------
# 3. Context menu returns early on empty area click
# ---------------------------------------------------------------------------
class TestContextMenuEmptyArea(unittest.TestCase):
    """Right-clicking empty space in a treeview must not show the menu."""

    def _make_mixin(self):
        """Create a minimal instance of the context menu mixin."""
        from app.mixins.context_menu_mixin import ContextMenuMixin
        obj = object.__new__(ContextMenuMixin)
        return obj

    def test_no_popup_on_empty_row(self):
        mixin = self._make_mixin()
        tree = MagicMock()
        menu = MagicMock()
        event = MagicMock()

        # identify_row returns "" when clicking empty area
        tree.identify_row.return_value = ""

        mixin._show_tree_context_menu(event, tree, menu)

        # Menu must NOT be shown
        menu.tk_popup.assert_not_called()
        tree.selection_set.assert_not_called()

    def test_popup_on_valid_row(self):
        mixin = self._make_mixin()
        tree = MagicMock()
        menu = MagicMock()
        event = MagicMock()

        tree.identify_row.return_value = "I001"

        mixin._show_tree_context_menu(event, tree, menu)

        tree.selection_set.assert_called_once_with("I001")
        menu.tk_popup.assert_called_once()


# ---------------------------------------------------------------------------
# 4. FocusOut binding uses add="+" to preserve searchable combo cleanup
# ---------------------------------------------------------------------------
class TestFocusOutBindingAdditive(unittest.TestCase):
    """contracts_tab must use add='+' so `<FocusOut>` doesn't overwrite
    the handler installed by make_searchable_combo.
    """

    def test_bind_uses_add_plus(self):
        import inspect
        from tabs import contracts_tab

        source = inspect.getsource(contracts_tab)
        # Must contain add="+" for the FocusOut binding
        self.assertIn('add="+"', source)
        # Ensure it is on a FocusOut line
        for line in source.splitlines():
            if "<FocusOut>" in line and "_on_contract_customer_changed" in line:
                self.assertIn("add", line)
                break
        else:
            self.fail("No <FocusOut> binding found for _on_contract_customer_changed")


# ---------------------------------------------------------------------------
# 5. Customer ledger dialog has transient() call
# ---------------------------------------------------------------------------
class TestLedgerDialogTransient(unittest.TestCase):
    """The customer ledger Toplevel must call transient(app) so it stays
    on top of the main window."""

    def test_source_has_transient(self):
        import inspect
        import ui.ui_actions as mod

        source = inspect.getsource(mod.show_customer_ledger_action)
        self.assertIn("transient", source)


# ---------------------------------------------------------------------------
# 6. Visual tags reapplied after expand/collapse/toggle
# ---------------------------------------------------------------------------
class TestInvoiceVisualTagsReapplied(unittest.TestCase):
    """expand_all, collapse_all, and double-click toggle must call
    _apply_invoice_tree_visual_tags() after state change.
    """

    def _make_billing_mixin(self):
        from app.mixins.billing_mixin import BillingMixin
        obj = object.__new__(BillingMixin)
        obj.invoice_tree = MagicMock()
        obj._apply_invoice_tree_visual_tags = MagicMock()
        obj._update_invoice_parent_label = MagicMock()
        obj._invoice_group_label = MagicMock(return_value="2 contracts")
        return obj

    def test_toggle_parent_row_calls_visual_tags(self):
        mixin = self._make_billing_mixin()
        mixin.invoice_tree.identify_row.return_value = "P001"
        mixin.invoice_tree.parent.return_value = ""  # it IS a parent
        mixin.invoice_tree.item.return_value = False  # not open

        event = MagicMock()
        mixin._toggle_invoice_parent_row(event)

        mixin._apply_invoice_tree_visual_tags.assert_called_once()

    def test_collapse_all_calls_visual_tags(self):
        mixin = self._make_billing_mixin()
        mixin.invoice_tree.selection.return_value = ()
        # get_children("") returns parents, get_children(parent) returns children
        mixin.invoice_tree.get_children.side_effect = lambda p="": ["P1", "P2"] if p == "" else ["C1"]
        # item(iid, "values") should return a list with at least 3 elements
        def _item_handler(iid, key=None, **kwargs):
            if key == "values":
                return ["a", "b", "c", "d", "e"]
            return None
        mixin.invoice_tree.item.side_effect = _item_handler

        mixin.collapse_all_invoice_groups()

        mixin._apply_invoice_tree_visual_tags.assert_called_once()

    def test_expand_all_calls_visual_tags(self):
        mixin = self._make_billing_mixin()
        mixin.invoice_tree.get_children.side_effect = lambda p="": ["P1"] if p == "" else ["C1"]
        def _item_handler(iid, key=None, **kwargs):
            if key == "values":
                return ["a", "b", "c", "d", "e"]
            return None
        mixin.invoice_tree.item.side_effect = _item_handler

        mixin.expand_all_invoice_groups()

        mixin._apply_invoice_tree_visual_tags.assert_called_once()


# ---------------------------------------------------------------------------
# 7. Invoice sort persists through refresh (_reapply_invoice_tree_sort)
# ---------------------------------------------------------------------------
class TestReapplyInvoiceTreeSort(unittest.TestCase):
    """_reapply_invoice_tree_sort must re-sort and update column headings."""

    def _make_mixin(self, col="rate", rev=False):
        from app.mixins.billing_mixin import BillingMixin
        obj = object.__new__(BillingMixin)
        obj.invoice_tree = MagicMock()
        obj.invoice_tree.__getitem__ = MagicMock(
            return_value=("customer", "plate", "rate", "balance")
        )
        obj._invoice_sort_col = col
        obj._invoice_sort_rev = rev
        obj._alphanum_key = lambda self_unused, v: v.lower() if isinstance(v, str) else v
        # Bind the method properly
        obj._alphanum_key = lambda v: v.lower() if isinstance(v, str) else v
        return obj

    def test_no_col_returns_early(self):
        from app.mixins.billing_mixin import BillingMixin
        obj = object.__new__(BillingMixin)
        obj.invoice_tree = MagicMock()
        # No _invoice_sort_col set at all
        obj._reapply_invoice_tree_sort()
        obj.invoice_tree.move.assert_not_called()

    def test_sort_updates_headings(self):
        mixin = self._make_mixin(col="rate", rev=False)

        # Two parent items
        mixin.invoice_tree.get_children.return_value = ["P1", "P2"]
        mixin.invoice_tree.set.side_effect = lambda iid, c: "$100" if iid == "P1" else "$50"
        mixin.invoice_tree.heading.side_effect = lambda c, *a, **kw: (
            "Rate" if a and a[0] == "text" else None
        )

        mixin._reapply_invoice_tree_sort()

        # Items should have been moved
        assert mixin.invoice_tree.move.call_count == 2
        # Heading updated calls
        heading_calls = [c for c in mixin.invoice_tree.heading.call_args_list
                         if "text" in (c.kwargs or {})]
        self.assertTrue(len(heading_calls) > 0)

    def test_reverse_sort(self):
        mixin = self._make_mixin(col="rate", rev=True)
        mixin.invoice_tree.get_children.return_value = ["P1", "P2"]
        mixin.invoice_tree.set.side_effect = lambda iid, c: "$100" if iid == "P1" else "$200"
        mixin.invoice_tree.heading.side_effect = lambda c, *a, **kw: "Rate"

        mixin._reapply_invoice_tree_sort()

        # With reverse, P2($200) should come first (index 0)
        move_calls = mixin.invoice_tree.move.call_args_list
        self.assertEqual(move_calls[0], call("P2", "", 0))
        self.assertEqual(move_calls[1], call("P1", "", 1))

    def test_refresh_invoices_calls_reapply(self):
        """Confirm refresh_invoices_action source calls _reapply_invoice_tree_sort."""
        import inspect
        import ui.ui_actions as mod

        source = inspect.getsource(mod.refresh_invoices_action)
        self.assertIn("_reapply_invoice_tree_sort", source)


# ---------------------------------------------------------------------------
# 8. Muted foreground restored on dark→light round-trip
# ---------------------------------------------------------------------------
class TestMutedForegroundRestore(unittest.TestCase):
    """Switching dark→light must restore the original foreground for muted
    labels, not leave them with the dark-mode color on a white background.
    """

    def test_source_saves_and_restores_original(self):
        """_apply_theme_to_widget_tree must handle both directions."""
        import inspect
        from app.mixins.theme_language_mixin import ThemeLanguageMixin

        source = inspect.getsource(ThemeLanguageMixin._apply_theme_to_widget_tree)
        # Must save original fg before overriding
        self.assertIn("_original_muted_fg", source)
        # Must restore in light mode
        self.assertIn("del root._original_muted_fg", source)

    def test_dark_mode_saves_original_fg(self):
        """When theme_mode=='dark', the original muted fg should be saved."""
        from app.mixins.theme_language_mixin import ThemeLanguageMixin
        import tkinter.ttk as ttk

        mixin = object.__new__(ThemeLanguageMixin)
        mixin.theme_mode = "dark"
        mixin._theme_palette = {
            "text_widget_bg": "#1e1e1e",
            "text_widget_fg": "#d4d4d4",
            "muted_text": "#d5deea",
            "surface_bg": "#2d2d30",
            "text": "#cccccc",
        }

        # Create a mock ttk.Label with muted fg
        widget = MagicMock(spec=ttk.Label)
        widget.cget.return_value = "#777777"
        widget.winfo_children.return_value = []

        mixin._apply_theme_to_widget_tree(widget)

        # Should have saved original and configured new color
        self.assertEqual(widget._original_muted_fg, "#777777")
        widget.configure.assert_called_once_with(foreground="#d5deea")

    def test_light_mode_restores_original_fg(self):
        """When theme_mode=='light', saved original fg should be restored."""
        from app.mixins.theme_language_mixin import ThemeLanguageMixin
        import tkinter.ttk as ttk

        mixin = object.__new__(ThemeLanguageMixin)
        mixin.theme_mode = "light"
        mixin._theme_palette = {
            "text_widget_bg": "#ffffff",
            "text_widget_fg": "#000000",
            "muted_text": "#d5deea",
            "surface_bg": "#f0f0f0",
            "text": "#000000",
        }

        widget = MagicMock(spec=ttk.Label)
        widget._original_muted_fg = "#777777"
        widget.winfo_children.return_value = []

        mixin._apply_theme_to_widget_tree(widget)

        widget.configure.assert_called_once_with(foreground="#777777")
        # Attribute should be cleaned up
        self.assertFalse(hasattr(widget, "_original_muted_fg"))


# ---------------------------------------------------------------------------
# 9. clear_inline_errors detects by marker attribute, not color
# ---------------------------------------------------------------------------
class TestInlineErrorMarkerDetection(unittest.TestCase):
    """clear_inline_errors must use `_is_inline_error` attribute, not
    background color, because theme changes can alter the color.
    """

    def test_show_inline_error_sets_marker(self):
        """show_inline_error must set _is_inline_error=True on the label."""
        import inspect
        from ui.ui_helpers import show_inline_error

        source = inspect.getsource(show_inline_error)
        self.assertIn("_is_inline_error = True", source)

    def test_clear_uses_marker_not_color(self):
        """clear_inline_errors must check _is_inline_error, not background."""
        import inspect
        from ui.ui_helpers import clear_inline_errors

        source = inspect.getsource(clear_inline_errors)
        self.assertIn("_is_inline_error", source)
        # Must NOT check background color
        self.assertNotIn('#ffebee', source)

    def test_clear_skips_label_without_marker(self):
        """A label with error background but no marker should be kept."""
        import tkinter as tk
        from ui.ui_helpers import clear_inline_errors

        # We mock the parent to avoid needing a real Tk instance
        parent = MagicMock()
        label_with_marker = MagicMock(spec=tk.Label)
        label_with_marker._is_inline_error = True

        label_without_marker = MagicMock(spec=tk.Label)
        # Deliberately do NOT set _is_inline_error

        parent.winfo_children.return_value = [label_with_marker, label_without_marker]

        clear_inline_errors(parent)

        label_with_marker.grid_forget.assert_called_once()
        label_without_marker.grid_forget.assert_not_called()


# ---------------------------------------------------------------------------
# 10. Language map key matches actual widget text
# ---------------------------------------------------------------------------
class TestLanguageMapKeyMatch(unittest.TestCase):
    """The hint label on the Invoices tab says 'plate row', so the language
    map key must also say 'plate row', not 'contract row'.
    """

    def test_plate_row_key_exists(self):
        from data.language_map import EN_TO_ZH

        hint_text = "  \u2190 Select a customer or plate row in the table below, then click an action"
        self.assertIn(hint_text, EN_TO_ZH)

    def test_contract_row_key_does_not_exist(self):
        """The old incorrect key must not be present."""
        from data.language_map import EN_TO_ZH

        old_key = "  \u2190 Select a customer or contract row in the table below, then click an action"
        self.assertNotIn(old_key, EN_TO_ZH)

    def test_invoices_tab_hint_matches_language_map(self):
        """The actual widget text in invoices_tab.py must match a key in EN_TO_ZH."""
        import inspect
        from tabs import invoices_tab
        from data.language_map import EN_TO_ZH

        source = inspect.getsource(invoices_tab)
        # Find the hint text used in the widget
        for line in source.splitlines():
            if "plate row" in line and "Select a customer" in line:
                # Extract the string literal
                for key in EN_TO_ZH:
                    if "plate row" in key and "Select a customer" in key:
                        self.assertIn(key.strip(), line)
                        return
        self.fail("Could not find 'plate row' hint in invoices_tab source")


# ---------------------------------------------------------------------------
# 11. Billing tab refresh on tab switch
# ---------------------------------------------------------------------------
class TestBillingTabRefreshOnSwitch(unittest.TestCase):
    """Switching to the Billing tab must refresh the active billing sub-tab
    so that the customer search filter is applied. Previously, navigating
    from the Trucks tab to Billing left unfiltered data visible even when
    the customer filter field had text.
    """

    @patch("app.mixins.lifecycle_mixin.on_tab_changed_action")
    def test_switching_to_billing_syncs_and_refreshes(self, mock_tab_action):
        from app.mixins.lifecycle_mixin import LifecycleMixin

        mixin = object.__new__(LifecycleMixin)
        mixin.main_notebook = MagicMock()
        mixin.tab_contracts = MagicMock()
        mixin.tab_billing = MagicMock()
        mixin._tab_has_unsaved_data = MagicMock(return_value=False)
        mixin._sync_search_boxes_from_truck_search = MagicMock()
        mixin._on_billing_tab_changed = MagicMock()
        mixin._focus_current_tab_primary_input = MagicMock()
        mixin.after_idle = MagicMock()

        # Simulate switching to billing tab
        mixin.main_notebook.select.return_value = str(mixin.tab_billing)

        mixin._on_tab_changed(MagicMock())

        mixin._sync_search_boxes_from_truck_search.assert_called_once()
        mixin._on_billing_tab_changed.assert_called_once()

    @patch("app.mixins.lifecycle_mixin.on_tab_changed_action")
    def test_switching_to_other_tab_does_not_refresh_billing(self, mock_tab_action):
        from app.mixins.lifecycle_mixin import LifecycleMixin

        mixin = object.__new__(LifecycleMixin)
        mixin.main_notebook = MagicMock()
        mixin.tab_contracts = MagicMock()
        mixin.tab_billing = MagicMock()
        mixin.tab_dashboard = MagicMock()
        mixin._tab_has_unsaved_data = MagicMock(return_value=False)
        mixin._sync_search_boxes_from_truck_search = MagicMock()
        mixin._on_billing_tab_changed = MagicMock()
        mixin.refresh_contracts = MagicMock()
        mixin._focus_current_tab_primary_input = MagicMock()
        mixin.after_idle = MagicMock()

        # Simulate switching to dashboard (not billing, not contracts)
        mixin.main_notebook.select.return_value = str(mixin.tab_dashboard)

        mixin._on_tab_changed(MagicMock())

        mixin._on_billing_tab_changed.assert_not_called()


if __name__ == "__main__":
    unittest.main()
