import tkinter as tk
from tkinter import ttk

from utils.billing_date_utils import today
from ui.ui_helpers import add_placeholder, create_date_input
from core.app_logging import trace


@trace
def build_overdue_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=0)
    frame.rowconfigure(1, weight=1)

    top = ttk.Frame(frame)
    top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    ttk.Button(
        top, text="💰  Record Payment",
        command=app._record_payment_for_selected_overdue,
        style="Payment.TButton",
    ).pack(side="left", padx=(0, 8))
    ttk.Button(
        top, text="📄  Invoice PDF",
        command=app._generate_invoice_pdf_for_selected_overdue,
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
    app.overdue_as_of.bind("<<DateEntrySelected>>", lambda _e: app.refresh_overdue())
    app.overdue_as_of.bind("<Return>", lambda _e: app.refresh_overdue())
    app.overdue_as_of.bind("<FocusOut>", lambda _e: app._schedule_overdue_date_refresh())
    ttk.Label(top, text="Search:").pack(side="left", padx=(12, 4))
    app.overdue_search = ttk.Entry(top, width=24)
    app.overdue_search.pack(side="left")
    add_placeholder(app.overdue_search, "Customer or plate...")
    app.overdue_search.bind("<Return>", lambda _e: app.refresh_overdue())
    app.overdue_search.bind("<KeyRelease>", app._on_overdue_search_keyrelease)
    ttk.Button(top, text="Clear", command=app._clear_overdue_search).pack(side="left", padx=6)

    # ── Summary bar ─────────────────────────────────────────────────
    summary = ttk.Frame(frame)
    summary.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))
    app.overdue_count_var = tk.StringVar(value="0 overdue contracts")
    app.overdue_total_expected_var = tk.StringVar(value="Expected: $0.00")
    app.overdue_total_paid_var = tk.StringVar(value="Paid: $0.00")
    app.overdue_total_balance_var = tk.StringVar(value="Outstanding: $0.00")
    ttk.Label(summary, textvariable=app.overdue_count_var, font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 20))
    ttk.Label(summary, textvariable=app.overdue_total_expected_var).pack(side="left", padx=(0, 16))
    ttk.Label(summary, textvariable=app.overdue_total_paid_var).pack(side="left", padx=(0, 16))
    ttk.Label(summary, textvariable=app.overdue_total_balance_var, font=("Segoe UI", 10, "bold")).pack(side="left")

    cols = ("date", "invoice_id", "customer", "scope", "amount", "paid", "balance")
    app.overdue_tree = ttk.Treeview(frame, columns=cols, show="headings", height=22)
    overdue_headings = {"date": "As-of Date", "invoice_id": "Contract ID", "customer": "Customer", "scope": "Scope", "amount": "Expected", "paid": "Paid", "balance": "Outstanding"}
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
