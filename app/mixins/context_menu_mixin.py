from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ContextMenuMixin:
    def _setup_right_click_menus(self):
        self.customer_menu = tk.Menu(self, tearoff=0)
        self.customer_menu.add_command(label="View Ledger", command=self.show_customer_ledger)
        self.customer_menu.add_separator()
        self.customer_menu.add_command(label="Generate PDF Invoice", command=self.generate_customer_invoice_pdf)
        self.customer_menu.add_separator()
        self.customer_menu.add_command(label="Delete Selected", command=self.delete_customer)
        self.customer_menu.add_separator()
        self.customer_menu.add_command(label="Refresh", command=self.refresh_customers)

        self.truck_menu = tk.Menu(self, tearoff=0)
        self.truck_menu.add_command(label="View Contract History", command=self.view_selected_truck_contract_history)
        self.truck_menu.add_separator()
        self.truck_menu.add_command(label="Delete Selected", command=self.delete_truck)
        self.truck_menu.add_separator()
        self.truck_menu.add_command(label="Refresh", command=self.refresh_trucks)

        self.contract_menu = tk.Menu(self, tearoff=0)
        self.contract_menu.add_command(label="View Payment History", command=self.show_contract_payment_history)
        self.contract_menu.add_separator()
        self.contract_menu.add_command(label="Edit Contract", command=self.edit_contract)
        self.contract_menu.add_command(label="Toggle Active/Inactive", command=self.toggle_contract)

        self.invoice_menu = tk.Menu(self, tearoff=0)
        self.invoice_menu.add_command(label="Fill Payment Form", command=self._open_payment_form_window)
        self.invoice_menu.add_command(label="Generate PDF Invoice", command=self._generate_invoice_pdf_from_billing_selection)
        self.invoice_menu.add_separator()
        self.invoice_menu.add_command(label="Reset Payments", command=self.reset_contract_payments)
        self.invoice_menu.add_separator()
        self.invoice_menu.add_command(label="Recalculate", command=self.refresh_invoices)

        self.overdue_menu = tk.Menu(self, tearoff=0)
        self.overdue_menu.add_command(label="Record Payment", command=self._record_payment_for_selected_overdue)
        self.overdue_menu.add_command(label="Generate PDF Invoice", command=self._generate_invoice_pdf_for_selected_overdue)
        self.overdue_menu.add_separator()
        self.overdue_menu.add_command(label="Refresh", command=self.refresh_overdue)

        self.customer_tree.bind("<Button-3>", lambda event: self._show_tree_context_menu(event, self.customer_tree, self.customer_menu))
        self.truck_tree.bind("<Button-3>", lambda event: self._show_tree_context_menu(event, self.truck_tree, self.truck_menu))
        self.contract_tree.bind("<Button-3>", lambda event: self._show_tree_context_menu(event, self.contract_tree, self.contract_menu))
        self.invoice_tree.bind("<Button-3>", lambda event: self._show_tree_context_menu(event, self.invoice_tree, self.invoice_menu))
        self.overdue_tree.bind("<Button-3>", lambda event: self._show_tree_context_menu(event, self.overdue_tree, self.overdue_menu))

    def _show_tree_context_menu(self, event: tk.Event, tree: ttk.Treeview, menu: tk.Menu):
        row_id = tree.identify_row(event.y)
        if row_id:
            tree.selection_set(row_id)
            tree.focus(row_id)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
