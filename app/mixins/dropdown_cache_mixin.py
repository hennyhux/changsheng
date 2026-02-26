from __future__ import annotations

from dataclasses import dataclass
from tkinter import ttk


@dataclass
class CustomerOption:
    id: int
    name: str
    phone: str | None
    company: str | None


@dataclass
class TruckOption:
    id: int
    plate: str
    state: str | None
    customer_id: int | None


class DropdownCacheMixin:
    def _reload_customer_dropdowns(self):
        customers = self.db.get_customer_dropdown_rows()
        self._customers_cache = [
            CustomerOption(int(row["id"]), row["name"], row["phone"], row["company"])
            for row in customers
        ]
        display = [self._fmt_customer(customer) for customer in self._customers_cache]

        for combo_name in ("truck_customer_combo", "contract_customer_combo"):
            if hasattr(self, combo_name):
                combo = getattr(self, combo_name)
                combo["values"] = display
                combo._search_all_values = display
                if display and not combo.get():
                    combo.current(0)

    def _reload_truck_dropdowns(self):
        trucks = self.db.get_truck_dropdown_rows()
        self._trucks_cache = [
            TruckOption(int(row["id"]), row["plate"], row["state"], row["customer_id"])
            for row in trucks
        ]
        if hasattr(self, "contract_truck_combo"):
            customer_id = None
            if hasattr(self, "contract_customer_combo"):
                customer_id = self._get_selected_customer_id_from_combo(self.contract_customer_combo)
            self._filter_contract_trucks(customer_id)

    def _fmt_customer(self, customer: CustomerOption) -> str:
        extras = []
        if customer.company:
            extras.append(customer.company)
        if customer.phone:
            extras.append(customer.phone)
        tail = f" ({' | '.join(extras)})" if extras else ""
        return f"{customer.id}: {customer.name}{tail}"

    def _fmt_truck(self, truck: TruckOption) -> str:
        state_prefix = f"{truck.state} " if truck.state else ""
        return f"{truck.id}: {truck.plate} {state_prefix}".strip()

    def _filter_contract_trucks(self, customer_id: int | None) -> None:
        trucks = list(getattr(self, "_trucks_cache", []))
        if customer_id is not None:
            trucks = [truck for truck in trucks if truck.customer_id == customer_id]

        display = [self._fmt_truck(truck) for truck in trucks]
        current = self.contract_truck_combo.get().strip() if hasattr(self, "contract_truck_combo") else ""
        if hasattr(self, "contract_truck_combo"):
            self.contract_truck_combo["values"] = display
            self.contract_truck_combo._search_all_values = display
            if current not in display:
                if display:
                    self.contract_truck_combo.current(0)
                else:
                    self.contract_truck_combo.set("")

    def _get_selected_customer_id_from_combo(self, combo: ttk.Combobox) -> int | None:
        val = combo.get().strip()
        if not val:
            return None
        all_vals = getattr(combo, "_search_all_values", list(combo["values"]))
        if val not in all_vals:
            return None
        try:
            return int(val.split(":")[0])
        except (ValueError, IndexError):
            return None

    def _get_selected_truck_id_from_combo(self, combo: ttk.Combobox) -> int | None:
        val = combo.get().strip()
        if not val:
            return None
        all_vals = getattr(combo, "_search_all_values", list(combo["values"]))
        if val not in all_vals:
            return None
        try:
            return int(val.split(":")[0])
        except (ValueError, IndexError):
            return None

    def _set_combo_by_customer_id(self, combo: ttk.Combobox, customer_id: int):
        vals = list(combo["values"])
        for index, value in enumerate(vals):
            if value.startswith(f"{customer_id}:"):
                combo.current(index)
                return
