from __future__ import annotations

import tkinter as tk

from dialogs.customer_picker import open_customer_picker
from ui.ui_helpers import get_entry_value
from utils.validation import normalize_whitespace


class TrucksTabMixin:
    def _clear_truck_search(self):
        if getattr(self, "_truck_search_after_id", None) is not None:
            self.after_cancel(self._truck_search_after_id)
            self._truck_search_after_id = None
        self.truck_search.delete(0, tk.END)
        self._sync_search_boxes_from_truck_search(force=True)
        self._truck_search_mode = "all"
        self._truck_filter_customer_id = None
        self.refresh_trucks()

    def _on_truck_search_keyrelease(self, _event=None):
        self._sync_search_boxes_from_truck_search(force=True)
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

    def _sync_search_boxes_from_truck_search(self, force: bool = False):
        if not hasattr(self, "truck_search"):
            return
        text = normalize_whitespace(self.truck_search.get())
        if hasattr(self, "contract_search"):
            existing = normalize_whitespace(get_entry_value(self.contract_search))
            if force or not existing:
                self.contract_search.delete(0, tk.END)
                self.contract_search.insert(0, text)
        if hasattr(self, "invoice_customer_search"):
            existing = normalize_whitespace(get_entry_value(self.invoice_customer_search))
            if force or not existing:
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

