from tkinter import ttk

from .invoices_tab import build_invoices_tab
from .statement_tab import build_statement_tab
from .overdue_tab import build_overdue_tab


def build_billing_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    sub = ttk.Notebook(frame, style="BillingTabs.TNotebook")
    sub.grid(row=0, column=0, sticky="nsew")
    app.billing_notebook = sub

    app.sub_invoices = ttk.Frame(sub)
    app.sub_statement = ttk.Frame(sub)
    app.sub_overdue = ttk.Frame(sub)

    sub.add(app.sub_invoices, text="🧾 Invoices & Payments")
    sub.add(app.sub_statement, text="📊 Monthly Statement")
    sub.add(app.sub_overdue, text="⏰ Overdue")

    build_invoices_tab(app, app.sub_invoices)
    build_statement_tab(app, app.sub_statement)
    build_overdue_tab(app, app.sub_overdue)

    sub.bind("<<NotebookTabChanged>>", app._on_billing_tab_changed)
