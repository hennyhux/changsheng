from __future__ import annotations

import tkinter as tk


class UsdotTabMixin:
    def _clear_usdot_search(self):
        if getattr(self, "_usdot_search_after_id", None) is not None:
            self.after_cancel(self._usdot_search_after_id)
            self._usdot_search_after_id = None
        if hasattr(self, "usdot_search"):
            self.usdot_search.delete(0, tk.END)
        self.refresh_usdots()

    def _on_usdot_search_keyrelease(self, _event=None):
        self._schedule_usdot_search_refresh()

    def _schedule_usdot_search_refresh(self, delay_ms: int = 250):
        if getattr(self, "_usdot_search_after_id", None) is not None:
            self.after_cancel(self._usdot_search_after_id)
        self._usdot_search_after_id = self.after(delay_ms, self._run_usdot_search_refresh)

    def _run_usdot_search_refresh(self):
        self._usdot_search_after_id = None
        self.refresh_usdots()

    def _on_usdot_driver_selected(self, _event=None):
        """When a driver is chosen, repopulate the contract combo with only their contracts."""
        if not hasattr(self, "usdot_driver_combo") or not hasattr(self, "usdot_contract_combo"):
            return
        customer_id = self._get_selected_customer_id_from_combo(self.usdot_driver_combo)
        self._load_usdot_contract_combo(customer_id)

    def _load_usdot_contract_combo(self, customer_id: int | None):
        """Populate usdot_contract_combo with contracts for the given customer."""
        if not hasattr(self, "usdot_contract_combo"):
            return
        if customer_id is None:
            self.usdot_contract_combo["values"] = []
            self.usdot_contract_combo.set("")
            return
        rows = self.db.get_contracts_by_customer_for_dropdown(customer_id)
        options = [f"{r['contract_id']}: {r['scope']} (${float(r['monthly_rate']):.0f}/mo)" for r in rows]
        self.usdot_contract_combo["values"] = options
        self.usdot_contract_combo.set("")

    def _on_usdot_tree_select(self, _event=None):
        if not hasattr(self, "usdot_tree"):
            return
        sel = self.usdot_tree.selection()
        if not sel:
            return
        values = self.usdot_tree.item(sel[0], "values")
        if not values:
            return

        usdot_account_id = None
        try:
            usdot_account_id = int(values[0])
        except Exception:
            usdot_account_id = None

        row = self.db.get_usdot_account_basic_by_id(usdot_account_id) if usdot_account_id is not None else None
        if row is None:
            return

        self.usdot_number_entry.delete(0, tk.END)
        self.usdot_number_entry.insert(0, str(row["usdot_number"] or "").strip())
        self.usdot_legal_name_entry.delete(0, tk.END)
        self.usdot_legal_name_entry.insert(0, str(row["legal_name"] or "").strip())
        self.usdot_phone_entry.delete(0, tk.END)
        self.usdot_phone_entry.insert(0, str(row["phone"] or "").strip())
        self.usdot_notes_entry.delete(0, tk.END)
        self.usdot_notes_entry.insert(0, str(row["notes"] or "").strip())
        if hasattr(self, "usdot_driver_combo"):
            customer_id = int(row["customer_id"]) if row["customer_id"] is not None else None
            if customer_id is not None:
                self._set_combo_by_customer_id(self.usdot_driver_combo, customer_id)
            else:
                self.usdot_driver_combo.set("")
            self._load_usdot_contract_combo(customer_id)
        if hasattr(self, "usdot_contract_combo"):
            self.usdot_contract_combo.set("")
