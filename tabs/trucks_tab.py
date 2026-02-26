import tkinter as tk
from tkinter import ttk

from ui.ui_helpers import add_placeholder, create_date_input, open_calendar_for_widget
from core.app_logging import trace


@trace
def build_trucks_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=0)
    frame.rowconfigure(1, weight=1)

    top = ttk.Frame(frame)
    top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
    top.columnconfigure(8, weight=1)

    ttk.Label(top, text="Search (plate/name):").grid(row=0, column=0, sticky="w")
    app.truck_search = ttk.Entry(top, width=20)
    app.truck_search.grid(row=0, column=1, sticky="w", padx=6)
    app.truck_search.bind("<Return>", lambda e: app.refresh_trucks())
    app.truck_search.bind("<KeyRelease>", app._on_truck_search_keyrelease)
    app._truck_search_mode = "all"
    app._truck_filter_customer_id = None
    ttk.Button(top, text="Find", command=app.refresh_trucks).grid(row=0, column=2, padx=6)
    ttk.Button(top, text="Clear", command=app._clear_truck_search).grid(row=0, column=3, padx=6)
    ttk.Button(top, text="Delete Selected", command=app.delete_truck).grid(row=0, column=4, padx=6)
    ttk.Button(top, text="💰  Record Payment", command=app.record_payment_for_selected_truck, style="Payment.TButton").grid(row=0, column=5, padx=6)
    ttk.Button(top, text="View Contract History", command=app.view_selected_truck_contract_history).grid(row=0, column=6, padx=6)

    cols = ("id", "plate", "state", "make", "model", "customer", "outstanding")
    app.truck_tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
    truck_headings = {"id": "ID", "plate": "Plate", "state": "State", "make": "Make", "model": "Model", "customer": "Customer", "outstanding": "Outstanding"}
    for c in cols:
        app.truck_tree.heading(
            c,
            text=truck_headings[c],
            anchor="center",
            command=lambda _c=c: app._sort_tree_column(app.truck_tree, _c),
        )
        width_map = {"id": 100, "plate": 180, "state": 80, "make": 180, "model": 180, "customer": 420, "outstanding": 170}
        app.truck_tree.column(c, width=width_map.get(c, 150), anchor="center")
    app.truck_tree.column("plate", anchor="center")
    app.truck_tree.column("make", anchor="center")
    app.truck_tree.column("model", anchor="center")
    app.truck_tree.column("customer", anchor="center", stretch=True)
    app.truck_tree.column("outstanding", anchor="center")
    app.truck_tree.grid(row=1, column=0, sticky="nsew", padx=10)
    truck_vsb = ttk.Scrollbar(frame, orient="vertical", command=app.truck_tree.yview)
    app.truck_tree.configure(yscrollcommand=truck_vsb.set)
    truck_vsb.grid(row=1, column=1, sticky="ns", padx=(0, 10))
    app._init_tree_striping(app.truck_tree)

    def _on_truck_tree_double_click(event):
        region = app.truck_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = app.truck_tree.identify_row(event.y)
        if not row_id:
            return
        app.truck_tree.selection_set(row_id)
        app.truck_tree.focus(row_id)
        app.view_selected_truck_contract_history()

    app.truck_tree.bind("<Double-1>", _on_truck_tree_double_click)

    form = ttk.LabelFrame(frame, text="Add Truck", padding="14")
    form.grid(row=2, column=0, sticky="ew", padx=10, pady=(12, 14))
    app._truck_form = form
    for i in range(13):
        form.columnconfigure(i, weight=1 if i in (3, 7, 11) else 0)
    form.rowconfigure(0, minsize=44)
    form.rowconfigure(1, minsize=44)

    ttk.Label(form, text="Plate*", font=("", 9, "bold")).grid(row=0, column=0, sticky="w", padx=6, pady=8)
    app.t_plate = ttk.Entry(form, width=16)
    app.t_plate.grid(row=0, column=1, sticky="w", padx=6, pady=8)
    add_placeholder(app.t_plate, "License plate...")
    app.t_plate.bind("<Return>", lambda e: app.add_truck())

    ttk.Label(form, text="State").grid(row=0, column=2, sticky="w", padx=6, pady=8)
    app.t_state = ttk.Entry(form, width=8)
    app.t_state.grid(row=0, column=3, sticky="w", padx=6, pady=8)
    add_placeholder(app.t_state, "CA")
    app.t_state.bind("<Return>", lambda e: app.add_truck())

    ttk.Label(form, text="Make").grid(row=0, column=4, sticky="w", padx=6, pady=8)
    app.t_make = ttk.Entry(form, width=14)
    app.t_make.grid(row=0, column=5, sticky="w", padx=6, pady=8)
    add_placeholder(app.t_make, "Ford")
    app.t_make.bind("<Return>", lambda e: app.add_truck())

    ttk.Label(form, text="Model").grid(row=0, column=6, sticky="w", padx=6, pady=8)
    app.t_model = ttk.Entry(form, width=14)
    app.t_model.grid(row=0, column=7, sticky="w", padx=6, pady=8)
    add_placeholder(app.t_model, "F-150")
    app.t_model.bind("<Return>", lambda e: app.add_truck())

    ttk.Label(form, text="Contract Start").grid(row=0, column=8, sticky="w", padx=6, pady=8)
    start_wrap = ttk.Frame(form)
    start_wrap.grid(row=0, column=9, sticky="w", padx=6, pady=8)
    app.t_contract_start = create_date_input(
        start_wrap,
        width=12,
        default_iso=None,
        date_entry_cls=getattr(app, "date_entry_cls", None),
    )
    app.t_contract_start.pack(side="left")
    # Only add a calendar button when the created widget does not already
    # provide its own dropdown (e.g. a `DateEntry`). This avoids duplicate
    # calendar arrows in the UI.
    try:
        date_entry_cls = getattr(app, "date_entry_cls", None)
        if not (date_entry_cls is not None and isinstance(app.t_contract_start, date_entry_cls)):
            ttk.Button(
                start_wrap,
                text="📅",
                width=3,
                command=lambda: open_calendar_for_widget(app, app.t_contract_start, date_entry_cls=getattr(app, "date_entry_cls", None)),
            ).pack(side="left", padx=(6, 0))
    except Exception:
        ttk.Button(
            start_wrap,
            text="📅",
            width=3,
            command=lambda: open_calendar_for_widget(app, app.t_contract_start, date_entry_cls=getattr(app, "date_entry_cls", None)),
        ).pack(side="left", padx=(6, 0))
    app.t_contract_start.bind("<Return>", lambda e: app.add_truck())

    ttk.Label(form, text="Contract End").grid(row=0, column=10, sticky="w", padx=6, pady=8)
    end_wrap = ttk.Frame(form)
    end_wrap.grid(row=0, column=11, sticky="w", padx=6, pady=8)
    app.t_contract_end = create_date_input(
        end_wrap,
        width=12,
        default_iso=None,
        date_entry_cls=getattr(app, "date_entry_cls", None),
    )
    app.t_contract_end.pack(side="left")
    try:
        date_entry_cls = getattr(app, "date_entry_cls", None)
        if not (date_entry_cls is not None and isinstance(app.t_contract_end, date_entry_cls)):
            ttk.Button(
                end_wrap,
                text="📅",
                width=3,
                command=lambda: open_calendar_for_widget(app, app.t_contract_end, date_entry_cls=getattr(app, "date_entry_cls", None)),
            ).pack(side="left", padx=(6, 0))
    except Exception:
        ttk.Button(
            end_wrap,
            text="📅",
            width=3,
            command=lambda: open_calendar_for_widget(app, app.t_contract_end, date_entry_cls=getattr(app, "date_entry_cls", None)),
        ).pack(side="left", padx=(6, 0))
    app.t_contract_end.bind("<Return>", lambda e: app.add_truck())

    ttk.Label(form, text="Customer").grid(row=1, column=0, sticky="w", padx=6, pady=8)
    app.truck_customer_combo = ttk.Combobox(form, width=36)
    app.truck_customer_combo.grid(row=1, column=1, columnspan=3, sticky="ew", padx=6, pady=8)
    app.truck_customer_combo.bind("<Return>", lambda e: app.add_truck())
    app._make_searchable_combo(app.truck_customer_combo)

    ttk.Button(form, text="Find Customer", command=app._open_truck_customer_picker).grid(
        row=1, column=4, sticky="w", padx=6, pady=8
    )

    ttk.Label(form, text="Notes").grid(row=1, column=5, sticky="w", padx=6, pady=8)
    app.t_notes = ttk.Entry(form, width=34)
    app.t_notes.grid(row=1, column=6, columnspan=2, sticky="ew", padx=6, pady=8)
    add_placeholder(app.t_notes, "Additional notes...")
    app.t_notes.bind("<Return>", lambda e: app.add_truck())

    ttk.Label(form, text="Contract Cost").grid(row=1, column=8, sticky="w", padx=6, pady=8)
    app.t_contract_rate = ttk.Entry(form, width=12)
    app.t_contract_rate.grid(row=1, column=9, sticky="w", padx=6, pady=8)
    add_placeholder(app.t_contract_rate, "Monthly cost...")
    app.t_contract_rate.bind("<Return>", lambda e: app.add_truck())

    btn_frame = ttk.Frame(form)
    btn_frame.grid(row=0, column=12, rowspan=2, padx=(12, 8), pady=8)
    ttk.Button(btn_frame, text="Add Truck", command=app.add_truck).pack(ipadx=10, ipady=6)
    ttk.Label(btn_frame, text="(Enter in any field)", font=("", 8), foreground="gray").pack()
