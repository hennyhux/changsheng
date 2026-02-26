from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from core.app_logging import trace
from dialogs.customer_picker import open_customer_picker
from dialogs.payment_history_dialog import show_contract_payment_history
from utils.billing_date_utils import today
from utils.validation import normalize_whitespace


class TrucksTabMixin:
    def _clear_truck_search(self):
        if getattr(self, "_truck_search_after_id", None) is not None:
            self.after_cancel(self._truck_search_after_id)
            self._truck_search_after_id = None
        self.truck_search.delete(0, tk.END)
        self._sync_search_boxes_from_truck_search()
        self._truck_search_mode = "all"
        self._truck_filter_customer_id = None
        self.refresh_trucks()

    def _on_truck_search_keyrelease(self, _event=None):
        self._sync_search_boxes_from_truck_search()
        self._truck_search_mode = "all"
        self._truck_filter_customer_id = None
        self._schedule_truck_search_refresh()

    def _schedule_truck_search_refresh(self, delay_ms: int = 250):
        if getattr(self, "_truck_search_after_id", None) is not None:
            self.after_cancel(self._truck_search_after_id)
        self._truck_search_after_id = self.after(delay_ms, self._run_truck_search_refresh)

    def _run_truck_search_refresh(self):
        self._truck_search_after_id = None
        self.refresh_trucks()

    def _sync_search_boxes_from_truck_search(self):
        if not hasattr(self, "truck_search"):
            return
        text = normalize_whitespace(self.truck_search.get())
        if hasattr(self, "contract_search"):
            self.contract_search.delete(0, tk.END)
            self.contract_search.insert(0, text)
        if hasattr(self, "invoice_customer_search"):
            self.invoice_customer_search.delete(0, tk.END)
            self.invoice_customer_search.insert(0, text)

    def _open_truck_customer_picker(self):
        if not hasattr(self, "_customers_cache") or not self._customers_cache:
            self._reload_customer_dropdowns()

        customers = list(getattr(self, "_customers_cache", []))

        def on_select(customer_id: int) -> None:
            self._set_combo_by_customer_id(self.truck_customer_combo, customer_id)
            self.t_notes.focus()

        open_customer_picker(self, customers, normalize_whitespace, on_select)

    @trace
    def view_selected_truck_contract_history(self):
        sel = self.truck_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a truck row first.")
            return

        values = self.truck_tree.item(sel[0], "values")
        if not values:
            messagebox.showerror("Invalid selection", "Could not read selected truck.")
            return

        try:
            truck_id = int(values[0])
        except (ValueError, TypeError):
            messagebox.showerror("Invalid selection", "Selected truck ID is invalid.")
            return

        contract_row = self.db.get_preferred_contract_for_truck(truck_id)
        if not contract_row:
            messagebox.showinfo("No Contract", "No contract was found for this truck.")
            return

        contract_id = int(contract_row["contract_id"])
        rows = self.db.get_contract_payment_history(contract_id)
        status = "ACTIVE" if int(contract_row["is_active"]) == 1 else "INACTIVE"

        scope = str(contract_row["scope"])
        plate = str(contract_row["plate"] or "").strip()
        if plate and scope == "Per-truck":
            scope = f"{scope} ({plate})"

        contract_info = {
            "contract_id": contract_id,
            "status": status,
            "customer": str(contract_row["customer_name"]),
            "scope": scope,
            "rate": f"${float(contract_row['monthly_rate']):.2f}/mo",
            "start": str(contract_row["start_date"]),
            "end": str(contract_row["end_date"] or "—"),
            "outstanding": f"${self._get_contract_outstanding_as_of(contract_id, today()):.2f}",
        }
        show_contract_payment_history(self, contract_info, rows)
