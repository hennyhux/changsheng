import tkinter as tk
from tkinter import ttk

from utils.billing_date_utils import today
from core.config import FONTS, TAG_COLORS
from ui.ui_helpers import create_date_input
from core.app_logging import trace


@trace
def build_invoices_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=0)
    frame.rowconfigure(2, weight=1)

    controls = ttk.LabelFrame(frame, text="Billing Date Controls", style="BillingControls.TLabelframe")
    controls.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
    controls.columnconfigure(12, weight=1)

    ttk.Label(controls, text="As-of Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", padx=6, pady=6)
    app.invoice_date = create_date_input(
        controls,
        width=12,
        default_iso=today().isoformat(),
        date_entry_cls=getattr(app, "date_entry_cls", None),
    )
    app.invoice_date.grid(row=0, column=1, sticky="w", padx=6, pady=6)

    ttk.Button(controls, text="Recalculate", command=app.refresh_invoices).grid(row=0, column=3, padx=6)
    ttk.Button(controls, text="Collapse All", command=app.collapse_all_invoice_groups).grid(row=0, column=4, padx=6)
    ttk.Button(controls, text="Expand All", command=app.expand_all_invoice_groups).grid(row=0, column=5, padx=6)
    ttk.Label(controls, text="Customer:").grid(row=0, column=6, sticky="e", padx=(10, 4), pady=6)
    app.invoice_customer_search = ttk.Entry(controls, width=22)
    app.invoice_customer_search.grid(row=0, column=7, sticky="w", padx=4, pady=6)
    app.invoice_customer_search.bind("<Return>", lambda _e: app.refresh_invoices())
    ttk.Button(controls, text="Clear", command=app._clear_invoice_customer_search).grid(row=0, column=8, padx=6)
    app.invoice_total_balance_var = tk.StringVar(value="$0.00")
    ttk.Label(controls, text="Total Outstanding:").grid(row=0, column=9, sticky="e", padx=(14, 4), pady=6)
    ttk.Label(controls, textvariable=app.invoice_total_balance_var, foreground="#b00020", font=FONTS["heading"]).grid(row=0, column=10, sticky="w", padx=4, pady=6)

    action_bar = ttk.Frame(frame, style="BillingAction.TFrame", padding="8")
    action_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))
    action_bar.columnconfigure(4, weight=1)

    ttk.Button(
        action_bar, text="💰  Record Payment",
        command=app._open_payment_form_window,
        style="Payment.TButton",
    ).grid(row=0, column=0, padx=(4, 8), pady=4, ipadx=4)

    ttk.Button(
        action_bar, text="📜  View History",
        command=app.show_contract_payment_history,
    ).grid(row=0, column=1, padx=4, pady=4)

    ttk.Button(
        action_bar, text="⚠️  Reset Payments",
        command=app.reset_contract_payments,
        style="Warning.TButton",
    ).grid(row=0, column=2, padx=4, pady=4)

    ttk.Label(
        action_bar,
        text="  ← Select a customer or plate row in the table below, then click an action",
        foreground="#777777",
        font=(FONTS["base"][0], max(FONTS["base"][1] - 1, 9), "italic"),
    ).grid(row=0, column=4, sticky="w", padx=12)

    cols = ("contract_id", "customer", "scope", "rate", "start", "end", "months", "expected", "paid", "balance", "status")
    app.invoice_tree = ttk.Treeview(frame, columns=cols, show="headings", height=18, style="Billing.Treeview")
    invoice_headings = {
        "contract_id": "",
        "customer": "Customer",
        "scope": "Plate",
        "rate": "Rate",
        "start": "Start",
        "end": "End",
        "months": "Elapsed Months",
        "expected": "Expected",
        "paid": "Paid",
        "balance": "Outstanding",
        "status": "Status",
    }
    for c in cols:
        app.invoice_tree.heading(
            c, text=invoice_headings[c], anchor="center",
            command=lambda _c=c: app._sort_invoice_tree(_c),
        )
        width = 150
        if c == "customer":
            width = 320
        if c == "scope":
            width = 300
        if c in ("start", "end"):
            width = 140
        if c == "contract_id":
            width = 1
        if c == "months":
            width = 180
        if c in ("expected", "paid", "balance"):
            width = 160
        if c == "status":
            width = 180
        app.invoice_tree.column(c, width=width, anchor="center")
    app.invoice_tree.column("contract_id", width=1, minwidth=0, stretch=False)
    app.invoice_tree.column("customer", anchor="center")
    app.invoice_tree.column("scope", anchor="center")
    app._init_tree_striping(app.invoice_tree)
    app.invoice_tree.tag_configure("status_due", 
                                    foreground=TAG_COLORS["status_due"]["foreground"],
                                    background=TAG_COLORS["status_due"]["background"],
                                    font=TAG_COLORS["status_due"]["font"])
    app.invoice_tree.tag_configure("status_paid", 
                                    foreground=TAG_COLORS["status_paid"]["foreground"],
                                    background=TAG_COLORS["status_paid"]["background"])
    app.invoice_tree.tag_configure("bal_zero", foreground="#2e7d32")
    app.invoice_tree.tag_configure("bal_no_contract", foreground="#b58900")
    app.invoice_tree.tag_configure("bal_due", foreground="#b00020")
    app.invoice_tree.tag_configure("invoice_parent_expanded", background="#dff0ff")
    app.invoice_tree.tag_configure("invoice_child_even", background="#ffffff")
    app.invoice_tree.tag_configure("invoice_child_odd", background="#f9fbff")

    app.invoice_tree.grid(row=2, column=0, sticky="nsew", padx=10)
    invoice_vsb = ttk.Scrollbar(frame, orient="vertical", command=app.invoice_tree.yview)
    app.invoice_tree.configure(yscrollcommand=invoice_vsb.set)
    invoice_vsb.grid(row=2, column=1, sticky="ns", padx=(0, 10))
    app.invoice_tree.bind("<<TreeviewOpen>>", app._on_invoice_tree_open_close)
    app.invoice_tree.bind("<<TreeviewClose>>", app._on_invoice_tree_open_close)
    app.invoice_tree.bind("<Double-1>", app._toggle_invoice_parent_row)
