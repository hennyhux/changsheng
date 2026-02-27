import tkinter as tk
from tkinter import ttk

from utils.billing_date_utils import today
from ui.ui_helpers import create_date_input
from core.app_logging import trace


@trace
def build_overdue_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=0)
    frame.rowconfigure(1, weight=1)

    top = ttk.Frame(frame)
    top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
    ttk.Button(
        top, text="💰  Record Payment",
        command=app._record_payment_for_selected_overdue,
        style="Payment.TButton",
    ).pack(side="left", padx=(0, 8))
    ttk.Button(top, text="Refresh", command=app.refresh_overdue).pack(side="left")
    ttk.Label(top, text="As-of Date (YYYY-MM-DD):").pack(side="left", padx=(12, 4))
    app.overdue_as_of = create_date_input(
        top,
        width=12,
        default_iso=today().isoformat(),
        date_entry_cls=getattr(app, "date_entry_cls", None),
    )
    app.overdue_as_of.pack(side="left")
    ttk.Label(top, text="Search:").pack(side="left", padx=(12, 4))
    app.overdue_search = ttk.Entry(top, width=24)
    app.overdue_search.pack(side="left")
    app.overdue_search.bind("<Return>", lambda _e: app.refresh_overdue())
    app.overdue_search.bind("<KeyRelease>", app._on_overdue_search_keyrelease)
    ttk.Button(top, text="Clear", command=app._clear_overdue_search).pack(side="left", padx=6)
    ttk.Label(top, text="Shows contracts with outstanding balance as of the selected date.").pack(side="left", padx=10)

    cols = ("month", "date", "invoice_id", "customer", "scope", "amount", "paid", "balance")
    app.overdue_tree = ttk.Treeview(frame, columns=cols, show="headings", height=22)
    overdue_headings = {"month": "Month", "date": "Date", "invoice_id": "Contract ID", "customer": "Customer", "scope": "Scope", "amount": "Amount", "paid": "Paid", "balance": "Balance"}
    for c in cols:
        app.overdue_tree.heading(
            c,
            text=overdue_headings[c],
            anchor="center",
            command=lambda _c=c: app._sort_tree_column(app.overdue_tree, _c),
        )
        width = 150
        if c == "customer":
            width = 340
        if c == "scope":
            width = 320
        if c == "date":
            width = 140
        if c == "invoice_id":
            width = 160
        if c in ("amount", "paid", "balance"):
            width = 160
        app.overdue_tree.column(c, width=width, anchor="center")
    app.overdue_tree.column("customer", anchor="center")
    app.overdue_tree.column("scope", anchor="center")
    app.overdue_tree.grid(row=1, column=0, sticky="nsew", padx=10)
    overdue_vsb = ttk.Scrollbar(frame, orient="vertical", command=app.overdue_tree.yview)
    app.overdue_tree.configure(yscrollcommand=overdue_vsb.set)
    overdue_vsb.grid(row=1, column=1, sticky="ns", padx=(0, 10))
    app._init_tree_striping(app.overdue_tree)

    def _on_overdue_tree_double_click(event):
        region = app.overdue_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = app.overdue_tree.identify_row(event.y)
        if not row_id:
            return
        app.overdue_tree.selection_set(row_id)
        app.overdue_tree.focus(row_id)
        app._record_payment_for_selected_overdue()

    app.overdue_tree.bind("<Double-1>", _on_overdue_tree_double_click)
