import tkinter as tk
from tkinter import ttk

from core.config import FONTS
from core.app_logging import trace
from utils.billing_date_utils import today
from ui.ui_helpers import create_date_input, set_date_input_today


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

    ttk.Label(search_bar, text="As of:").grid(row=0, column=4, padx=(14, 4), pady=8, sticky="e")
    app.dashboard_as_of_entry = create_date_input(
        search_bar,
        width=12,
        default_iso=today().isoformat(),
        date_entry_cls=getattr(app, "date_entry_cls", None),
    )
    app.dashboard_as_of_entry.grid(row=0, column=5, padx=4, pady=8, sticky="w")

    def _set_dashboard_as_of_today() -> None:
        set_date_input_today(app.dashboard_as_of_entry, getattr(app, "date_entry_cls", None))
        app.refresh_dashboard()

    ttk.Button(search_bar, text="Today", command=_set_dashboard_as_of_today).grid(row=0, column=6, padx=(4, 4), pady=8)
    ttk.Button(search_bar, text="Refresh KPI", command=app.refresh_dashboard).grid(row=0, column=7, padx=(4, 8), pady=8)

    app.dashboard_as_of_entry.bind("<Return>", lambda _e: app.refresh_dashboard())
    app.dashboard_as_of_entry.bind("<<DateEntrySelected>>", lambda _e: app.refresh_dashboard())

    results_wrap = ttk.Frame(search_bar)
    results_wrap.grid(row=1, column=0, columnspan=8, sticky="nsew", padx=8, pady=(0, 8))
    results_wrap.columnconfigure(0, weight=1)
    results_wrap.rowconfigure(0, weight=1)

    app.dashboard_search_tree = ttk.Treeview(
        results_wrap,
        columns=("type", "match", "detail"),
        show="headings",
        height=5,
    )
    app.dashboard_search_tree.heading(
        "type",
        text="Type",
        anchor="center",
        command=lambda: app._sort_tree_column(app.dashboard_search_tree, "type"),
    )
    app.dashboard_search_tree.heading(
        "match",
        text="Match",
        anchor="center",
        command=lambda: app._sort_tree_column(app.dashboard_search_tree, "match"),
    )
    app.dashboard_search_tree.heading(
        "detail",
        text="Detail",
        anchor="center",
        command=lambda: app._sort_tree_column(app.dashboard_search_tree, "detail"),
    )
    app.dashboard_search_tree.column("type", width=120, anchor="center")
    app.dashboard_search_tree.column("match", width=260, anchor="center")
    app.dashboard_search_tree.column("detail", width=560, anchor="center")
    app.dashboard_search_tree.grid(row=0, column=0, sticky="nsew")
    search_vsb = ttk.Scrollbar(results_wrap, orient="vertical", command=app.dashboard_search_tree.yview)
    app.dashboard_search_tree.configure(yscrollcommand=search_vsb.set)
    search_vsb.grid(row=0, column=1, sticky="ns")

    def _on_dashboard_search_tree_double_click(event):
        region = app.dashboard_search_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = app.dashboard_search_tree.identify_row(event.y)
        if not row_id:
            return
        app.dashboard_search_tree.selection_set(row_id)
        app.dashboard_search_tree.focus(row_id)
        app._open_dashboard_search_selection()

    app.dashboard_search_tree.bind("<Double-1>", _on_dashboard_search_tree_double_click)
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
    expected_month_label = add_card(frame, 1, 1, "Expected This Month", app.dash_expected_month_var)
    expected_month_label.bind("<Double-1>", lambda _e: app._open_statement_tab_from_dashboard())
    add_card(frame, 2, 0, "Total Outstanding", app.dash_total_outstanding_var)
    overdue_30_label = add_card(frame, 2, 1, "Overdue 30+ Days", app.dash_overdue_30_var)
    overdue_30_label.bind("<Double-1>", lambda _e: app._open_overdue_tab_from_dashboard())
