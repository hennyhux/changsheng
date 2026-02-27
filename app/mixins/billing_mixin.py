from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from core.app_logging import trace
from utils.billing_date_utils import parse_ymd


class BillingMixin:
    def _invoice_group_label(self, contract_count: int, is_open: bool) -> str:
        arrow = "▼" if is_open else "▶"
        noun = "Contract" if contract_count == 1 else "Contracts"
        return f"{arrow} {contract_count} {noun}"

    def _update_invoice_parent_label(self, parent_iid: str):
        children_count = len(self.invoice_tree.get_children(parent_iid))
        is_open = bool(self.invoice_tree.item(parent_iid, "open"))
        values = list(self.invoice_tree.item(parent_iid, "values"))
        if not values:
            return
        values[2] = self._invoice_group_label(children_count, is_open)
        self.invoice_tree.item(parent_iid, values=values)

    def _refresh_invoice_parent_labels(self):
        for parent_iid in self.invoice_tree.get_children(""):
            self._update_invoice_parent_label(parent_iid)

    def _apply_invoice_tree_visual_tags(self):
        for parent_index, parent_iid in enumerate(self.invoice_tree.get_children("")):
            parent_values = self.invoice_tree.item(parent_iid, "values")
            if not parent_values:
                continue

            parent_balance = parent_values[9] if len(parent_values) > 9 else ""
            parent_balance_tag = self._outstanding_tag_from_text(str(parent_balance))
            parent_stripe_tag = self._row_stripe_tag(parent_index)
            is_open = bool(self.invoice_tree.item(parent_iid, "open"))
            if is_open:
                self.invoice_tree.item(
                    parent_iid,
                    tags=("invoice_parent_expanded", parent_balance_tag),
                )
            else:
                self.invoice_tree.item(
                    parent_iid,
                    tags=(parent_stripe_tag, parent_balance_tag),
                )

            for child_index, child_iid in enumerate(self.invoice_tree.get_children(parent_iid)):
                child_values = self.invoice_tree.item(child_iid, "values")
                child_balance = child_values[9] if child_values and len(child_values) > 9 else ""
                child_balance_tag = self._outstanding_tag_from_text(str(child_balance))
                child_stripe_tag = "invoice_child_even" if child_index % 2 == 0 else "invoice_child_odd"
                self.invoice_tree.item(child_iid, tags=(child_stripe_tag, child_balance_tag))

    def _on_invoice_tree_open_close(self, _event=None):
        self._refresh_invoice_parent_labels()
        self._apply_invoice_tree_visual_tags()

    def _toggle_invoice_parent_row(self, event: tk.Event):
        row_id = self.invoice_tree.identify_row(event.y)
        if not row_id:
            return
        if self.invoice_tree.parent(row_id):
            return
        is_open = bool(self.invoice_tree.item(row_id, "open"))
        self.invoice_tree.item(row_id, open=not is_open)
        self._update_invoice_parent_label(row_id)
        return "break"

    @trace
    def collapse_all_invoice_groups(self):
        current_selection = self.invoice_tree.selection()
        if current_selection:
            self.invoice_tree.selection_remove(*current_selection)

        for parent_iid in self.invoice_tree.get_children(""):
            self.invoice_tree.item(parent_iid, open=False)
            children_count = len(self.invoice_tree.get_children(parent_iid))
            values = list(self.invoice_tree.item(parent_iid, "values"))
            if values:
                values[0] = self._invoice_group_label(children_count, False)
                self.invoice_tree.item(parent_iid, values=values)

        self.invoice_tree.focus("")

    @trace
    def expand_all_invoice_groups(self):
        for parent_iid in self.invoice_tree.get_children(""):
            self.invoice_tree.item(parent_iid, open=True)
            children_count = len(self.invoice_tree.get_children(parent_iid))
            values = list(self.invoice_tree.item(parent_iid, "values"))
            if values:
                values[0] = self._invoice_group_label(children_count, True)
                self.invoice_tree.item(parent_iid, values=values)

    def _sort_invoice_tree(self, col: str):
        if getattr(self, "_invoice_sort_col", None) == col:
            self._invoice_sort_rev = not getattr(self, "_invoice_sort_rev", False)
        else:
            self._invoice_sort_col = col
            self._invoice_sort_rev = False

        tree = self.invoice_tree
        numeric_dollar = {"rate", "expected", "paid", "balance"}
        numeric_int    = {"contract_id", "months"}

        def sort_key(iid):
            val = tree.set(iid, col)
            if col in numeric_dollar:
                try:
                    return float(val.replace("$", "").replace(",", "").strip())
                except ValueError:
                    return 0.0
            if col in numeric_int:
                try:
                    return int(val)
                except ValueError:
                    return 0
            return self._alphanum_key(val)

        items = list(tree.get_children(""))
        items.sort(key=sort_key, reverse=self._invoice_sort_rev)
        for idx, iid in enumerate(items):
            tree.move(iid, "", idx)

        invoice_headings = {
            "contract_id": "Contract ID",
            "customer": "Customer",
            "scope": "Scope",
            "rate": "Rate",
            "start": "Start",
            "end": "End",
            "months": "Elapsed Months",
            "expected": "Expected",
            "paid": "Paid",
            "balance": "Outstanding",
            "status": "Status",
        }
        for c in tree["columns"]:
            label = invoice_headings.get(c, c)
            if c == col:
                label += " ▼" if self._invoice_sort_rev else " ▲"
            tree.heading(c, text=label)

    def _on_overdue_search_keyrelease(self, _event=None):
        self._schedule_overdue_search_refresh()

    def _on_invoice_customer_search_keyrelease(self, _event=None):
        self._schedule_invoice_search_refresh()

    def _schedule_invoice_search_refresh(self, delay_ms: int = 250):
        if getattr(self, "_invoice_search_after_id", None) is not None:
            self.after_cancel(self._invoice_search_after_id)
        self._invoice_search_after_id = self.after(delay_ms, self._run_invoice_search_refresh)

    def _run_invoice_search_refresh(self):
        self._invoice_search_after_id = None
        self.refresh_invoices()

    def _schedule_overdue_search_refresh(self, delay_ms: int = 250):
        if getattr(self, "_overdue_search_after_id", None) is not None:
            self.after_cancel(self._overdue_search_after_id)
        self._overdue_search_after_id = self.after(delay_ms, self._run_overdue_search_refresh)

    def _run_overdue_search_refresh(self):
        self._overdue_search_after_id = None
        self.refresh_overdue()

    def _clear_overdue_search(self):
        if getattr(self, "_overdue_search_after_id", None) is not None:
            self.after_cancel(self._overdue_search_after_id)
            self._overdue_search_after_id = None
        if hasattr(self, "overdue_search"):
            self.overdue_search.delete(0, tk.END)
            self.overdue_search.focus_set()
        self.refresh_overdue()

    def _get_selected_overdue_contract_id(self) -> int | None:
        if not hasattr(self, "overdue_tree"):
            return None
        sel = self.overdue_tree.selection()
        if not sel:
            return None
        values = self.overdue_tree.item(sel[0], "values")
        if not values or len(values) < 3:
            return None
        try:
            return int(str(values[2]).strip())
        except (ValueError, TypeError):
            return None

    def _record_payment_for_selected_overdue(self):
        if not hasattr(self, "overdue_tree"):
            return
        sel = self.overdue_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select an overdue row first.")
            return

        values = self.overdue_tree.item(sel[0], "values")
        if not values or len(values) < 5:
            messagebox.showerror("Invalid selection", "Could not read selected overdue row.")
            return

        try:
            contract_id = int(str(values[2]).strip())
        except (ValueError, TypeError):
            messagebox.showerror("Invalid selection", "Selected contract ID is invalid.")
            return

        scope_value = str(values[4]).strip()
        plate_label = None if scope_value.lower() in {"(customer-level)", "customer-level"} else scope_value

        as_of_date = None
        if hasattr(self, "overdue_as_of"):
            as_of_text = self.overdue_as_of.get().strip()
            if as_of_text:
                parsed = parse_ymd(as_of_text)
                if parsed:
                    as_of_date = parsed

        self._open_payment_form_for_contract(contract_id, plate_label, as_of_date)

    def _generate_invoice_pdf_for_selected_overdue(self):
        contract_id = self._get_selected_overdue_contract_id()
        if not contract_id:
            messagebox.showwarning("No Selection", "Select an overdue row first.")
            return
        customer_id = self.db.get_customer_id_by_contract(contract_id)
        if not customer_id:
            messagebox.showerror("Not found", f"Customer for contract {contract_id} was not found.")
            return
        self._generate_customer_invoice_pdf_for_customer_id(customer_id)

    def _on_billing_tab_changed(self, _event=None):
        if not hasattr(self, "billing_notebook"):
            return
        selected = self.billing_notebook.select()
        if selected == str(self.sub_overdue):
            self.refresh_overdue()
        elif selected == str(self.sub_invoices):
            self.refresh_invoices()
        elif selected == str(self.sub_statement):
            self.refresh_statement()
        self.after_idle(self._focus_current_tab_primary_input)
