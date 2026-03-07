from tkinter import ttk

from ui.ui_helpers import add_placeholder
from core.app_logging import trace


@trace
def build_usdot_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=0)
    frame.rowconfigure(1, weight=1)

    top = ttk.Frame(frame)
    top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
    top.columnconfigure(8, weight=1)

    ttk.Label(top, text="Search:").grid(row=0, column=0, sticky="w")
    app.usdot_search = ttk.Entry(top, width=30)
    app.usdot_search.grid(row=0, column=1, sticky="w", padx=6)
    app.usdot_search.bind("<Return>", lambda _e: app.refresh_usdots())
    app.usdot_search.bind("<KeyRelease>", app._on_usdot_search_keyrelease)
    ttk.Button(top, text="Find", command=app.refresh_usdots).grid(row=0, column=2, padx=6)
    ttk.Button(top, text="Clear", command=app._clear_usdot_search).grid(row=0, column=3, padx=6)
    ttk.Button(top, text="Refresh", command=app.refresh_usdots).grid(row=0, column=4, padx=6)

    cols = ("id", "usdot_number", "driver", "legal_name", "phone", "notes", "trucks", "contracts")
    app.usdot_tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
    headings = {
        "id": "ID",
        "usdot_number": "USDOT",
        "driver": "Driver",
        "legal_name": "Legal Name",
        "phone": "Phone",
        "notes": "Notes",
        "trucks": "Linked Trucks",
        "contracts": "Linked Contracts",
    }
    for c in cols:
        app.usdot_tree.heading(
            c,
            text=headings[c],
            anchor="center",
            command=lambda _c=c: app._sort_tree_column(app.usdot_tree, _c),
        )

    app.usdot_tree.column("id", width=100, anchor="center", stretch=False)
    app.usdot_tree.column("usdot_number", width=200, anchor="center", stretch=False)
    app.usdot_tree.column("driver", width=340, anchor="center", stretch=False)
    app.usdot_tree.column("legal_name", width=300, anchor="center", stretch=False)
    app.usdot_tree.column("phone", width=220, anchor="center", stretch=False)
    app.usdot_tree.column("notes", width=420, anchor="center", stretch=True)
    app.usdot_tree.column("trucks", width=160, anchor="center", stretch=False)
    app.usdot_tree.column("contracts", width=180, anchor="center", stretch=False)

    app.usdot_tree.grid(row=1, column=0, sticky="nsew", padx=10)
    usdot_vsb = ttk.Scrollbar(frame, orient="vertical", command=app.usdot_tree.yview)
    app.usdot_tree.configure(yscrollcommand=usdot_vsb.set)
    usdot_vsb.grid(row=1, column=1, sticky="ns", padx=(0, 10))
    app._init_tree_striping(app.usdot_tree)
    app.usdot_tree.bind("<<TreeviewSelect>>", app._on_usdot_tree_select)

    form = ttk.LabelFrame(frame, text="Add USDOT", padding="10")
    form.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
    app._usdot_form = form
    for i in range(8):
        form.columnconfigure(i, weight=1 if i in (1, 3, 5) else 0)

    ttk.Label(form, text="USDOT Number*", font=("", 9, "bold")).grid(row=0, column=0, sticky="w", padx=6, pady=8)
    app.usdot_number_entry = ttk.Entry(form, width=18)
    app.usdot_number_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=8)
    add_placeholder(app.usdot_number_entry, "USDOT number...")
    app.usdot_number_entry.bind("<Return>", lambda _e: app.add_usdot())

    ttk.Label(form, text="Driver*", font=("", 9, "bold")).grid(row=0, column=2, sticky="w", padx=6, pady=8)
    app.usdot_driver_combo = ttk.Combobox(form)
    app.usdot_driver_combo.grid(row=0, column=3, sticky="ew", padx=6, pady=8)
    app._make_searchable_combo(app.usdot_driver_combo)
    app.usdot_driver_combo.bind("<Return>", lambda _e: app.add_usdot())
    app.usdot_driver_combo.bind("<<ComboboxSelected>>", app._on_usdot_driver_selected)

    ttk.Label(form, text="Phone").grid(row=0, column=4, sticky="w", padx=6, pady=8)
    app.usdot_phone_entry = ttk.Entry(form, width=20)
    app.usdot_phone_entry.grid(row=0, column=5, sticky="ew", padx=6, pady=8)
    add_placeholder(app.usdot_phone_entry, "Phone number...")
    app.usdot_phone_entry.bind("<Return>", lambda _e: app.add_usdot())

    ttk.Label(form, text="Legal Name").grid(row=1, column=0, sticky="w", padx=6, pady=8)
    app.usdot_legal_name_entry = ttk.Entry(form, width=30)
    app.usdot_legal_name_entry.grid(row=1, column=1, columnspan=3, sticky="ew", padx=6, pady=8)
    add_placeholder(app.usdot_legal_name_entry, "Legal entity name...")
    app.usdot_legal_name_entry.bind("<Return>", lambda _e: app.add_usdot())

    ttk.Label(form, text="Link Contract (optional)").grid(row=1, column=4, sticky="w", padx=6, pady=8)
    app.usdot_contract_combo = ttk.Combobox(form, width=20, state="readonly")
    app.usdot_contract_combo.grid(row=1, column=5, sticky="ew", padx=6, pady=8)

    ttk.Label(form, text="Notes").grid(row=2, column=0, sticky="w", padx=6, pady=8)
    app.usdot_notes_entry = ttk.Entry(form, width=80)
    app.usdot_notes_entry.grid(row=2, column=1, columnspan=5, sticky="ew", padx=6, pady=8)
    add_placeholder(app.usdot_notes_entry, "Additional notes...")
    app.usdot_notes_entry.bind("<Return>", lambda _e: app.add_usdot())

    btn_frame = ttk.Frame(form)
    btn_frame.grid(row=0, column=6, rowspan=3, sticky="ne", padx=(12, 6), pady=6)
    ttk.Button(btn_frame, text="🟢 Add USDOT", command=app.add_usdot).pack(ipadx=8, ipady=6)
    ttk.Label(btn_frame, text="(Enter in any field)", font=("", 8), foreground="gray").pack(pady=(4, 0))
