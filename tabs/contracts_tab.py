import tkinter as tk
from tkinter import ttk

from utils.billing_date_utils import today
from ui.ui_helpers import add_placeholder, create_date_input, make_optional_date_clear_on_blur
from core.app_logging import trace


@trace
def build_contracts_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=0)
    frame.rowconfigure(1, weight=1)

    top = ttk.Frame(frame)
    top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
    top.columnconfigure(6, weight=1)
    ttk.Label(top, text="(Search by name)").grid(row=0, column=0, sticky="w")
    app.contract_search = ttk.Entry(top, width=30)
    app.contract_search.grid(row=0, column=1, sticky="w", padx=6)
    app.contract_search.bind("<Return>", lambda _e: app.refresh_contracts(refresh_dependents=False))
    app.contract_search.bind("<KeyRelease>", app._on_contract_search_keyrelease)
    ttk.Button(top, text="Find", command=lambda: app.refresh_contracts(refresh_dependents=False)).grid(row=0, column=2, padx=6)
    ttk.Button(top, text="Clear", command=app._clear_contract_search).grid(row=0, column=3, padx=6)

    cols = ("contract_id", "status", "customer", "scope", "rate", "start", "end", "outstanding")
    app.contract_tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
    contract_headings = {"contract_id": "Contract ID", "status": "Status", "customer": "Customer", "scope": "Plate", "rate": "Rate", "start": "Start", "end": "End", "outstanding": "Outstanding"}
    for c in cols:
        app.contract_tree.heading(
            c,
            text=contract_headings[c],
            anchor="center",
            command=lambda _c=c: app._sort_tree_column(app.contract_tree, _c),
        )
        width = 150
        if c == "customer":
            width = 320
        if c == "scope":
            width = 300
        if c == "contract_id":
            width = 160
        if c == "status":
            width = 180
        if c == "outstanding":
            width = 170
        app.contract_tree.column(c, width=width, anchor="center")
    app.contract_tree.column("customer", anchor="center")
    app.contract_tree.column("scope", anchor="center")
    app.contract_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 0))
    contract_vsb = ttk.Scrollbar(frame, orient="vertical", command=app.contract_tree.yview)
    app.contract_tree.configure(yscrollcommand=contract_vsb.set)
    contract_vsb.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=(10, 0))
    app._init_tree_striping(app.contract_tree)

    btns = ttk.Frame(frame)
    btns.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
    ttk.Button(btns, text="💰  Record Payment", command=app.record_payment_for_selected_contract, style="Payment.TButton").pack(side="left", padx=(0, 8))
    ttk.Button(btns, text="Refresh", command=app.refresh_contracts).pack(side="left")
    ttk.Button(btns, text="Toggle Active/Inactive", command=app.toggle_contract).pack(side="left", padx=8)
    ttk.Button(btns, text="🔴 Delete Selected", command=app.delete_contract, style="Warning.TButton").pack(side="left", padx=8)
    ttk.Frame(btns).pack(side="left", fill="x", expand=True)
    ttk.Button(btns, text="🟢 Create Contract", command=app.create_contract, style="CreateContract.TButton").pack(side="right", ipadx=12, ipady=4)

    form = ttk.LabelFrame(frame, text="Create Contract")
    form.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
    app._contract_form = form
    for i in range(12):
        form.columnconfigure(i, weight=1 if i in (11,) else 0)

    ttk.Label(form, text="Customer*").grid(row=0, column=0, sticky="w", padx=6, pady=6)
    app.contract_customer_combo = ttk.Combobox(form, width=40)
    app.contract_customer_combo.grid(row=0, column=1, columnspan=3, sticky="w", padx=6, pady=6)
    app._make_searchable_combo(app.contract_customer_combo)
    app.contract_customer_combo.bind("<<ComboboxSelected>>", app._on_contract_customer_changed)
    app.contract_customer_combo.bind("<FocusOut>", app._on_contract_customer_changed, add="+")

    ttk.Button(form, text="Find Customer", command=app._open_contract_customer_picker).grid(
        row=0, column=4, sticky="w", padx=6, pady=6
    )

    ttk.Label(form, text="Contract scope").grid(row=0, column=5, sticky="w", padx=6, pady=6)
    app.contract_scope = tk.StringVar(value="per_truck")
    ttk.Radiobutton(form, text="Per truck", variable=app.contract_scope, value="per_truck",
                    command=app._on_scope_change).grid(row=0, column=6, sticky="w", padx=6)
    ttk.Radiobutton(form, text="Customer-level", variable=app.contract_scope, value="customer_level",
                    command=app._on_scope_change).grid(row=0, column=7, sticky="w", padx=6)

    ttk.Label(form, text="Truck (if per truck)").grid(row=1, column=0, sticky="w", padx=6, pady=6)
    app.contract_truck_combo = ttk.Combobox(form, width=30)
    app.contract_truck_combo.grid(row=1, column=1, columnspan=2, sticky="w", padx=6, pady=6)
    app._make_searchable_combo(app.contract_truck_combo)

    ttk.Label(form, text="Rate ($/mo)*").grid(row=1, column=3, sticky="w", padx=6, pady=6)
    app.contract_rate = ttk.Entry(form, width=12)
    app.contract_rate.grid(row=1, column=4, sticky="w", padx=6, pady=6)
    add_placeholder(app.contract_rate, "0.00")
    app.contract_rate.bind("<Return>", lambda e: app.create_contract())

    ttk.Label(form, text="Start YYYY-MM-DD").grid(row=1, column=5, sticky="w", padx=6, pady=6)
    start_wrap = ttk.Frame(form)
    start_wrap.grid(row=1, column=6, sticky="w", padx=6, pady=6)
    app.contract_start = create_date_input(
        start_wrap,
        width=12,
        default_iso=today().isoformat(),
        date_entry_cls=getattr(app, "date_entry_cls", None),
    )
    app.contract_start.pack(side="left")

    ttk.Label(form, text="End YYYY-MM-DD (optional)").grid(row=1, column=7, sticky="w", padx=6, pady=6)
    end_wrap = ttk.Frame(form)
    end_wrap.grid(row=1, column=8, sticky="w", padx=6, pady=6)
    app.contract_end = create_date_input(
        end_wrap,
        width=12,
        default_iso=None,
        date_entry_cls=getattr(app, "date_entry_cls", None),
    )
    app.contract_end.pack(side="left")
    make_optional_date_clear_on_blur(app.contract_end, date_entry_cls=getattr(app, "date_entry_cls", None))

    ttk.Label(form, text="Notes").grid(row=2, column=0, sticky="w", padx=6, pady=6)
    app.contract_notes = ttk.Entry(form, width=80)
    app.contract_notes.grid(row=2, column=1, columnspan=10, sticky="ew", padx=6, pady=6)
    app.contract_notes.bind("<Return>", lambda e: app.create_contract())

    app._on_scope_change()
    app._on_contract_customer_changed()
