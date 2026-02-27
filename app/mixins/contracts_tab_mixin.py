from __future__ import annotations

from dialogs.customer_picker import open_customer_picker
from utils.validation import normalize_whitespace


class ContractsTabMixin:
    def _on_scope_change(self):
        if self.contract_scope.get() == "customer_level":
            self.contract_truck_combo.configure(state="disabled")
        else:
            self.contract_truck_combo.configure(state="normal")

    def _open_contract_customer_picker(self):
        if not hasattr(self, "_customers_cache") or not self._customers_cache:
            self._reload_customer_dropdowns()

        customers = list(getattr(self, "_customers_cache", []))

        def on_select(customer_id: int) -> None:
            self._set_combo_by_customer_id(self.contract_customer_combo, customer_id)
            self._on_contract_customer_changed()
            self.contract_rate.focus()

        open_customer_picker(self, customers, normalize_whitespace, on_select)

    def _on_contract_customer_changed(self, _event=None):
        if not hasattr(self, "contract_truck_combo"):
            return
        customer_id = self._get_selected_customer_id_from_combo(self.contract_customer_combo)
        self._filter_contract_trucks(customer_id)

    def _clear_contract_search(self):
        if getattr(self, "_contract_search_after_id", None) is not None:
            self.after_cancel(self._contract_search_after_id)
            self._contract_search_after_id = None
        if hasattr(self, "contract_search"):
            self.contract_search.delete(0, "end")
        self.refresh_contracts(refresh_dependents=False)

    def _on_contract_search_keyrelease(self, _event=None):
        self._schedule_contract_search_refresh()

    def _schedule_contract_search_refresh(self, delay_ms: int = 250):
        if getattr(self, "_contract_search_after_id", None) is not None:
            self.after_cancel(self._contract_search_after_id)
        self._contract_search_after_id = self.after(delay_ms, self._run_contract_search_refresh)

    def _run_contract_search_refresh(self):
        self._contract_search_after_id = None
        self.refresh_contracts(refresh_dependents=False)
