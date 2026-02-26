from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from core.app_logging import get_app_logger

logger = get_app_logger()


class NavigationMixin:
    def _bind_global_shortcuts(self):
        self.bind_all("<Control-f>", self._focus_current_tab_primary_input)
        self.bind_all("<Control-F>", self._focus_current_tab_primary_input)
        self.bind_all("<Control-r>", self._refresh_current_tab)
        self.bind_all("<Control-R>", self._refresh_current_tab)
        self.bind_all("<Control-b>", lambda _event: self.backup_database())
        self.bind_all("<Control-B>", lambda _event: self.backup_database())
        self.bind_all("<Escape>", self._clear_current_tab_search)

    def _get_primary_entry_for_current_tab(self):
        selected_tab = self.main_notebook.select() if hasattr(self, "main_notebook") else ""

        if selected_tab == str(self.tab_dashboard):
            return getattr(self, "dashboard_search_entry", None)
        if selected_tab == str(self.tab_customers):
            return getattr(self, "customer_search", None)
        if selected_tab == str(self.tab_trucks):
            return getattr(self, "truck_search", None)
        if selected_tab == str(self.tab_contracts):
            return getattr(self, "contract_search", None)
        if selected_tab == str(self.tab_histories):
            return getattr(self, "histories_text", None)

        if selected_tab == str(self.tab_billing) and hasattr(self, "billing_notebook"):
            sub_selected = self.billing_notebook.select()
            if sub_selected == str(self.sub_invoices):
                return getattr(self, "invoice_customer_search", None)
            if sub_selected == str(self.sub_overdue):
                return getattr(self, "overdue_search", None)
            if sub_selected == str(self.sub_statement):
                return getattr(self, "statement_month", None)

        return None

    def _focus_current_tab_primary_input(self, _event=None):
        target_widget = self._get_primary_entry_for_current_tab()
        if not target_widget:
            return
        try:
            target_widget.focus_set()
            if isinstance(target_widget, (tk.Entry, ttk.Entry)):
                target_widget.icursor(tk.END)
        except Exception as exc:
            logger.debug(f"Failed to focus primary input for current tab: {exc}")
        return "break"

    def _refresh_current_tab(self, _event=None):
        selected_tab = self.main_notebook.select() if hasattr(self, "main_notebook") else ""
        if selected_tab == str(self.tab_dashboard):
            self.refresh_dashboard()
        elif selected_tab == str(self.tab_customers):
            self.refresh_customers()
        elif selected_tab == str(self.tab_trucks):
            self.refresh_trucks()
        elif selected_tab == str(self.tab_contracts):
            self.refresh_contracts()
        elif selected_tab == str(self.tab_histories):
            self.refresh_histories()
        elif selected_tab == str(self.tab_billing) and hasattr(self, "billing_notebook"):
            sub_selected = self.billing_notebook.select()
            if sub_selected == str(self.sub_invoices):
                self.refresh_invoices()
            elif sub_selected == str(self.sub_statement):
                self.refresh_statement()
            elif sub_selected == str(self.sub_overdue):
                self.refresh_overdue()
        return "break"

    def _clear_current_tab_search(self, _event=None):
        selected_tab = self.main_notebook.select() if hasattr(self, "main_notebook") else ""
        if selected_tab == str(self.tab_dashboard):
            self._clear_dashboard_global_search()
            return "break"
        if selected_tab == str(self.tab_customers):
            self._clear_customer_search()
            return "break"
        if selected_tab == str(self.tab_trucks):
            self._clear_truck_search()
            return "break"
        if selected_tab == str(self.tab_contracts):
            self._clear_contract_search()
            return "break"
        if selected_tab == str(self.tab_billing) and hasattr(self, "billing_notebook"):
            sub_selected = self.billing_notebook.select()
            if sub_selected == str(self.sub_invoices):
                self._clear_invoice_customer_search()
                return "break"
            if sub_selected == str(self.sub_overdue):
                self._clear_overdue_search()
                return "break"
        return None
