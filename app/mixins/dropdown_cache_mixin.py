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
    usdot_account_id: int | None


@dataclass
class UsdotOption:
    id: int
    usdot_number: str


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

        if hasattr(self, "usdot_driver_combo"):
            current = self.usdot_driver_combo.get().strip()
            self.usdot_driver_combo["values"] = display
            self.usdot_driver_combo._search_all_values = display
            if current not in display:
                self.usdot_driver_combo.set("")

            self._reload_usdot_dropdowns()

    def _reload_truck_dropdowns(self):
        trucks = self.db.get_truck_dropdown_rows()
        self._trucks_cache = [
            TruckOption(
                int(row["id"]),
                row["plate"],
                row["state"],
                row["customer_id"],
                int(row["usdot_account_id"]) if row["usdot_account_id"] is not None else None,
            )
            for row in trucks
        ]
        if hasattr(self, "contract_truck_combo"):
            customer_id = None
            if hasattr(self, "contract_customer_combo"):
                customer_id = self._get_selected_customer_id_from_combo(self.contract_customer_combo)
            self._filter_contract_trucks(customer_id)
            self._reload_usdot_dropdowns(customer_id)
        else:
            self._reload_usdot_dropdowns()

    def _reload_usdot_dropdowns(self, customer_id: int | None = None):
        rows = self.db.get_usdot_dropdown_rows(customer_id)
        self._usdots_cache = [
            UsdotOption(int(row["id"]), str(row["usdot_number"]))
            for row in rows
        ]
        display = [self._fmt_usdot(option) for option in self._usdots_cache]

        if hasattr(self, "contract_usdot_combo"):
            current = self.contract_usdot_combo.get().strip()
            self.contract_usdot_combo["values"] = display
            self.contract_usdot_combo._search_all_values = display
            if current not in display:
                if display:
                    self.contract_usdot_combo.current(0)
                else:
                    self.contract_usdot_combo.set("")

        if hasattr(self, "truck_usdot_combo"):
            all_rows = self.db.get_usdot_dropdown_rows(None)
            all_display = [f"{int(r['id'])}: {str(r['usdot_number'])}" for r in all_rows]
            current = self.truck_usdot_combo.get().strip()
            self.truck_usdot_combo["values"] = all_display
            self.truck_usdot_combo._search_all_values = all_display
            if current not in all_display:
                if all_display:
                    self.truck_usdot_combo.current(0)
                else:
                    self.truck_usdot_combo.set("")

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

    def _fmt_usdot(self, option: UsdotOption) -> str:
        return f"{option.id}: {option.usdot_number}"

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

    def _get_selected_contract_id_from_combo(self, combo: ttk.Combobox) -> int | None:
        val = combo.get().strip()
        if not val:
            return None
        try:
            return int(val.split(":")[0])
        except (ValueError, IndexError):
            return None

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

    def _get_selected_usdot_account_id_from_combo(self, combo: ttk.Combobox) -> int | None:
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

    def _set_combo_by_usdot_account_id(self, combo: ttk.Combobox, usdot_account_id: int):
        vals = list(combo["values"])
        for index, value in enumerate(vals):
            if value.startswith(f"{usdot_account_id}:"):
                combo.current(index)
                return

    def _set_combo_by_customer_id(self, combo: ttk.Combobox, customer_id: int):
        vals = list(combo["values"])
        for index, value in enumerate(vals):
            if value.startswith(f"{customer_id}:"):
                combo.current(index)
                return

