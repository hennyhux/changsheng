from __future__ import annotations

import re
from datetime import date, timedelta
import tkinter as tk
from tkinter import messagebox

from core.app_logging import trace, get_trace_logger

_log = get_trace_logger()
from utils.billing_date_utils import add_months, parse_ymd, today
from utils.validation import normalize_whitespace


class DashboardMixin:
    def _clear_dashboard_global_search(self):
        if self._dashboard_search_after_id is not None:
            self.after_cancel(self._dashboard_search_after_id)
            self._dashboard_search_after_id = None
        if hasattr(self, "dashboard_search_entry"):
            self.dashboard_search_entry.delete(0, tk.END)
            self.dashboard_search_entry.focus_set()
        if hasattr(self, "dashboard_search_tree"):
            for item in self.dashboard_search_tree.get_children():
                self.dashboard_search_tree.delete(item)
        self._dashboard_search_result_map = {}

    def _schedule_dashboard_global_search(self, delay_ms: int = 250):
        if self._dashboard_search_after_id is not None:
            self.after_cancel(self._dashboard_search_after_id)
        self._dashboard_search_after_id = self.after(delay_ms, self._run_dashboard_global_search)

    def _run_dashboard_global_search(self):
        self._dashboard_search_after_id = None
        if not hasattr(self, "dashboard_search_tree"):
            return

        query = normalize_whitespace(self.dashboard_search_entry.get())
        if not query:
            self._clear_dashboard_global_search()
            return

        query_l = query.lower()
        selected_label = self.dashboard_search_field.get().strip() if hasattr(self, "dashboard_search_field") else "All"
        selected_field = self.dashboard_search_fields.get(selected_label, "all")
        field = self._detect_dashboard_search_field(query) if selected_field == "all" else selected_field

        for item in self.dashboard_search_tree.get_children():
            self.dashboard_search_tree.delete(item)
        self._dashboard_search_result_map = {}

        query_plate = re.sub(r"[^a-z0-9]", "", query_l)
        query_digits = re.sub(r"\D", "", query)

        def _matches(field_name: str, candidate: str) -> bool:
            candidate_l = normalize_whitespace(candidate).lower()
            if not candidate_l:
                return False

            if field_name == "plate":
                candidate_plate = re.sub(r"[^a-z0-9]", "", candidate_l)
                if not query_plate or not candidate_plate:
                    return False
                return query_plate in candidate_plate

            if field_name == "phone":
                candidate_digits = re.sub(r"\D", "", candidate)
                if not query_digits or not candidate_digits:
                    return False
                return query_digits in candidate_digits

            if field == "name_or_company" and field_name in {"name", "company"}:
                return query_l in candidate_l
            return query_l in candidate_l and (field == "all" or field == field_name)

        results: list[tuple[str, str, str, dict[str, str | int]]] = []

        customer_rows = self.db.get_customers_with_truck_count(q=None, limit=5000)
        for row in customer_rows:
            name = str(row["name"] or "")
            phone = str(row["phone"] or "")
            company = str(row["company"] or "")
            if _matches("name", name) or _matches("phone", phone) or _matches("company", company):
                detail = f"Phone: {phone or '—'} | Company: {company or '—'}"
                results.append(("Customer", name, detail, {"tab": "customers", "id": int(row["id"]), "name": name }))

        truck_rows = self.db.get_trucks_with_customer(q=None, limit=5000)
        for row in truck_rows:
            plate = str(row["plate"] or "")
            customer = str(row["customer_name"] or "")
            if _matches("plate", plate) or (field == "all" and query_l in customer.lower()):
                detail = f"Customer: {customer or '—'} | {str(row['make'] or '—')} {str(row['model'] or '')}".strip()
                results.append(("Truck", plate, detail, {"tab": "trucks", "id": int(row["id"]) }))

        for result_type, match_text, detail, meta in results:
            iid = self.dashboard_search_tree.insert("", "end", values=(result_type, match_text, detail))
            self._dashboard_search_result_map[iid] = meta

        self._reapply_tree_sort(self.dashboard_search_tree)

    def _detect_dashboard_search_field(self, query: str) -> str:
        text = normalize_whitespace(query)
        if not text:
            return "all"

        lowered = text.lower()
        digit_count = sum(ch.isdigit() for ch in text)
        has_alpha = any(ch.isalpha() for ch in text)

        if lowered.startswith("#") and lowered[1:].isdigit():
            return "all"
        if lowered.startswith("contract ") and lowered.split(" ", 1)[1].isdigit():
            return "all"

        phone_digits = re.sub(r"\D", "", text)
        if not has_alpha and len(phone_digits) >= 7:
            return "phone"

        plate_compact = re.sub(r"[^a-z0-9]", "", lowered)
        if has_alpha and digit_count > 0 and 4 <= len(plate_compact) <= 12:
            return "plate"

        return "name_or_company"

    def _open_dashboard_search_selection(self, _event=None):
        if not hasattr(self, "dashboard_search_tree"):
            return
        sel = self.dashboard_search_tree.selection()
        if not sel:
            return

        meta = self._dashboard_search_result_map.get(sel[0])
        if not meta:
            return

        target_tab = meta.get("tab")
        target_id = int(meta.get("id", 0))
        if target_id <= 0:
            return

        if target_tab == "customers":
            self.main_notebook.select(self.tab_customers)
            customer_name = meta.get("name", "")
            if customer_name and hasattr(self, "customer_search"):
                self.customer_search.delete(0, "end")
                self.customer_search.insert(0, customer_name)
                _log.debug("Pre-filled customer search with '%s' from global search", customer_name)
            self.refresh_customers()
            self._select_tree_row_by_id(self.customer_tree, target_id)
            self._set_selected_customer(target_id)
        elif target_tab == "trucks":
            self.main_notebook.select(self.tab_trucks)
            self.refresh_trucks()
            self._select_tree_row_by_id(self.truck_tree, target_id)
        elif target_tab == "contracts":
            self.main_notebook.select(self.tab_contracts)
            self.refresh_contracts()
            self._select_tree_row_by_id(self.contract_tree, target_id)

    @trace
    def refresh_dashboard(self):
        if not hasattr(self, "dash_active_contracts_var"):
            return

        as_of_date = today()
        if hasattr(self, "dashboard_as_of_entry"):
            as_of_text = self.dashboard_as_of_entry.get().strip()
            if as_of_text:
                parsed = parse_ymd(as_of_text)
                if not parsed:
                    messagebox.showerror("Date format error", "Dashboard As-of date must be YYYY-MM-DD.")
                    return
                as_of_date = parsed
        month_start = date(as_of_date.year, as_of_date.month, 1)
        next_y, next_m = add_months(as_of_date.year, as_of_date.month, 1)
        month_end = date(next_y, next_m, 1) - timedelta(days=1)

        contracts = self.db.get_active_contracts_for_dashboard()
        paid_rows = self.db.get_paid_totals_by_contract_as_of(as_of_date.isoformat())
        paid_by_contract = {int(row["contract_id"]): float(row["paid_total"]) for row in paid_rows}

        active_count = len(contracts)
        expected_month = 0.0
        total_outstanding = 0.0
        overdue_30_count = 0

        for r in contracts:
            start_d = parse_ymd(r["start_date"])
            if not start_d:
                continue

            end_d = parse_ymd(r["end_date"]) if r["end_date"] else None
            if start_d <= month_end and (end_d is None or end_d >= month_start):
                expected_month += float(r["monthly_rate"])

            outstanding = self._get_contract_outstanding_as_of(int(r["contract_id"]), as_of_date)
            total_outstanding += outstanding

            if outstanding > 0.01:
                paid_total = paid_by_contract.get(int(r["contract_id"]), 0.0)

                rate = float(r["monthly_rate"])
                paid_months = int(paid_total // rate) if rate > 0 else 0
                due_y, due_m = add_months(start_d.year, start_d.month, paid_months)
                next_y2, next_m2 = add_months(due_y, due_m, 1)
                last_day = (date(next_y2, next_m2, 1) - timedelta(days=1)).day
                due_day = min(start_d.day, last_day)
                oldest_due = date(due_y, due_m, due_day)

                if oldest_due <= (as_of_date - timedelta(days=30)):
                    overdue_30_count += 1

        self.dash_active_contracts_var.set(str(active_count))
        self.dash_expected_month_var.set(f"${expected_month:.2f}")
        self.dash_total_outstanding_var.set(f"${total_outstanding:.2f}")
        self.dash_overdue_30_var.set(str(overdue_30_count))

    def _open_overdue_tab_from_dashboard(self):
        self.main_notebook.select(self.tab_billing)
        if hasattr(self, "billing_notebook") and hasattr(self, "sub_overdue"):
            self.billing_notebook.select(self.sub_overdue)
        self.refresh_overdue()

    def _open_statement_tab_from_dashboard(self):
        self.main_notebook.select(self.tab_billing)
        if hasattr(self, "billing_notebook") and hasattr(self, "sub_statement"):
            self.billing_notebook.select(self.sub_statement)
        self.refresh_statement()

    def _refresh_affected_tabs_after_truck_change(self):
        """Optimized batch refresh after truck add/delete. Avoids redundant queries."""
        self.refresh_customers()
        self.refresh_trucks()
        self.refresh_contracts(refresh_dependents=False)
        self.refresh_invoices()
        self.refresh_overdue()
        self.refresh_statement()
        self.refresh_dashboard()
