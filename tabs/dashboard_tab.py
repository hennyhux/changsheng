import tkinter as tk
from tkinter import ttk

from core.config import FONTS
from core.app_logging import trace


@trace
def build_dashboard_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(0, weight=0)
    frame.rowconfigure(1, weight=1)
    frame.rowconfigure(2, weight=1)

    search_bar = ttk.LabelFrame(frame, text="Global Search")
    search_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(14, 6))
    search_bar.columnconfigure(3, weight=1)

    app.dashboard_search_fields = {
        "All": "all",
        "Plate": "plate",
        "Name": "name",
        "Company": "company",
        "Phone": "phone",
    }
    app.dashboard_search_field = ttk.Combobox(
        search_bar,
        values=list(app.dashboard_search_fields.keys()),
        width=14,
        state="readonly",
    )
    app.dashboard_search_field.grid(row=0, column=0, padx=(8, 6), pady=8, sticky="w")
    app.dashboard_search_field.set("All")
    app.dashboard_search_field.bind("<<ComboboxSelected>>", lambda _e: app._schedule_dashboard_global_search())

    app.dashboard_search_entry = ttk.Entry(search_bar, width=40)
    app.dashboard_search_entry.grid(row=0, column=1, padx=6, pady=8, sticky="w")
    app.dashboard_search_entry.bind("<Return>", lambda _e: app._run_dashboard_global_search())
    app.dashboard_search_entry.bind("<KeyRelease>", lambda _e: app._schedule_dashboard_global_search())

    ttk.Button(search_bar, text="Search", command=app._run_dashboard_global_search).grid(row=0, column=2, padx=6, pady=8)
    ttk.Button(search_bar, text="Clear", command=app._clear_dashboard_global_search).grid(row=0, column=3, padx=(0, 8), pady=8, sticky="w")

    results_wrap = ttk.Frame(search_bar)
    results_wrap.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=8, pady=(0, 8))
    results_wrap.columnconfigure(0, weight=1)
    results_wrap.rowconfigure(0, weight=1)

    app.dashboard_search_tree = ttk.Treeview(
        results_wrap,
        columns=("type", "match", "detail"),
        show="headings",
        height=5,
    )
    app.dashboard_search_tree.heading("type", text="Type", anchor="center")
    app.dashboard_search_tree.heading("match", text="Match", anchor="center")
    app.dashboard_search_tree.heading("detail", text="Detail", anchor="center")
    app.dashboard_search_tree.column("type", width=120, anchor="center")
    app.dashboard_search_tree.column("match", width=260, anchor="center")
    app.dashboard_search_tree.column("detail", width=560, anchor="center")
    app.dashboard_search_tree.grid(row=0, column=0, sticky="nsew")
    search_vsb = ttk.Scrollbar(results_wrap, orient="vertical", command=app.dashboard_search_tree.yview)
    app.dashboard_search_tree.configure(yscrollcommand=search_vsb.set)
    search_vsb.grid(row=0, column=1, sticky="ns")
    app.dashboard_search_tree.bind("<Double-1>", app._open_dashboard_search_selection)
    app.dashboard_search_tree.bind("<Return>", app._open_dashboard_search_selection)

    app._dashboard_search_result_map = {}
    app._dashboard_search_after_id = None

    app.dash_active_contracts_var = tk.StringVar(value="0")
    app.dash_expected_month_var = tk.StringVar(value="$0.00")
    app.dash_total_outstanding_var = tk.StringVar(value="$0.00")
    app.dash_overdue_30_var = tk.StringVar(value="0")

    def add_card(parent: tk.Widget, row: int, col: int, title: str, value_var: tk.StringVar):
        card = ttk.LabelFrame(parent, text=title, padding=28)
        card.grid(row=row, column=col, sticky="nsew", padx=18, pady=18)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)
        value_label = ttk.Label(
            card,
            textvariable=value_var,
            anchor="center",
            justify="center",
            font=FONTS["dashboard_title"],
        )
        value_label.grid(row=0, column=0, sticky="nsew")
        return value_label

    add_card(frame, 1, 0, "Total Active Contracts", app.dash_active_contracts_var)
    add_card(frame, 1, 1, "Expected This Month", app.dash_expected_month_var)
    add_card(frame, 2, 0, "Total Outstanding", app.dash_total_outstanding_var)
    overdue_30_label = add_card(frame, 2, 1, "Overdue 30+ Days", app.dash_overdue_30_var)
    overdue_30_label.bind("<Double-1>", lambda _e: app._open_overdue_tab_from_dashboard())
