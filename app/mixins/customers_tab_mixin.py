from __future__ import annotations

import tkinter as tk
from tkinter import messagebox


class CustomersTabMixin:
    def _clear_customer_search(self):
        if getattr(self, "_customer_search_after_id", None) is not None:
            self.after_cancel(self._customer_search_after_id)
            self._customer_search_after_id = None
        self.customer_search.delete(0, tk.END)
        self.refresh_customers()

    def _on_customer_search_keyrelease(self, _event=None):
        self._schedule_customer_search_refresh()

    def _schedule_customer_search_refresh(self, delay_ms: int = 250):
        if getattr(self, "_customer_search_after_id", None) is not None:
            self.after_cancel(self._customer_search_after_id)
        self._customer_search_after_id = self.after(delay_ms, self._run_customer_search_refresh)

    def _run_customer_search_refresh(self):
        self._customer_search_after_id = None
        self.refresh_customers()

    def _on_customer_tree_select(self, _event=None):
        self._sync_selected_customer_to_forms()
        self._update_view_trucks_button_state()

    def _update_view_trucks_button_state(self):
        if not hasattr(self, "view_trucks_btn"):
            return
        has_selection = bool(self.customer_tree.selection()) if hasattr(self, "customer_tree") else False
        self.view_trucks_btn.configure(state=("normal" if has_selection else "disabled"))

    def _view_selected_customer_trucks(self):
        sel = self.customer_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a customer row first.")
            self._update_view_trucks_button_state()
            return

        values = self.customer_tree.item(sel[0], "values")
        if not values:
            return

        customer_id = int(values[0])
        customer_name = str(values[1])

        self.main_notebook.select(self.tab_trucks)
        self.truck_search.delete(0, tk.END)
        self.truck_search.insert(0, customer_name)
        self.truck_search.focus_set()
        self.truck_search.icursor(tk.END)
        self._sync_search_boxes_from_truck_search(force=True)
        self._truck_search_mode = "customer_name"
        self._truck_filter_customer_id = customer_id
        self.refresh_trucks()

        if hasattr(self, "truck_customer_combo"):
            self._set_combo_by_customer_id(self.truck_customer_combo, customer_id)

        truck_rows = self.truck_tree.get_children("")
        if truck_rows:
            first_iid = truck_rows[0]
            self.truck_tree.selection_set(first_iid)
            self.truck_tree.focus(first_iid)
            self.truck_tree.see(first_iid)
        else:
            messagebox.showinfo("No Trucks", f"No trucks found for customer '{customer_name}'.")

    def _set_selected_customer(self, customer_id: int):
        if hasattr(self, "truck_customer_combo"):
            self._set_combo_by_customer_id(self.truck_customer_combo, customer_id)
        if hasattr(self, "contract_customer_combo"):
            self._set_combo_by_customer_id(self.contract_customer_combo, customer_id)
