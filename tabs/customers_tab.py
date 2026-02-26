from tkinter import ttk

from ui.ui_helpers import add_placeholder
from core.app_logging import trace


@trace
def build_customers_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=0)
    frame.rowconfigure(1, weight=1)

    top = ttk.Frame(frame)
    top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
    top.columnconfigure(10, weight=1)

    ttk.Label(top, text="Search:").grid(row=0, column=0, sticky="w")
    app.customer_search = ttk.Entry(top, width=30)
    app.customer_search.grid(row=0, column=1, sticky="w", padx=6)
    app.customer_search.bind("<Return>", lambda e: app.refresh_customers())
    app.customer_search.bind("<KeyRelease>", app._on_customer_search_keyrelease)
    ttk.Button(top, text="Find", command=app.refresh_customers).grid(row=0, column=2, padx=6)
    ttk.Button(top, text="Clear", command=app._clear_customer_search).grid(row=0, column=3, padx=6)
    ttk.Button(top, text="🔴 Delete Selected", command=app.delete_customer).grid(row=0, column=4, padx=6)
    data_frame = ttk.Frame(top)
    data_frame.grid(row=0, column=5, columnspan=3, padx=6, sticky="ew")
    ttk.Button(data_frame, text="Backup DB", command=app.backup_database).pack(side="left", padx=(0, 4))
    ttk.Button(data_frame, text="Restore DB", command=app.restore_database).pack(side="left", padx=2)
    ttk.Button(data_frame, text="Export CSV", command=app.export_customers_trucks_csv).pack(side="left", padx=2)
    ttk.Button(data_frame, text="Import CSV", command=app.import_customers_trucks).pack(side="left", padx=2)
    ttk.Button(top, text="Generate PDF Invoice", command=app.generate_customer_invoice_pdf).grid(row=0, column=8, padx=6)

    cols = ("id", "name", "phone", "company", "notes", "outstanding", "trucks")
    app.customer_tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
    customer_headings = {
        "id": "ID",
        "name": "Name",
        "phone": "Phone",
        "company": "Company",
        "notes": "Notes",
        "outstanding": "Outstanding",
        "trucks": "Trucks Parked",
    }
    for c in cols:
        app.customer_tree.heading(
            c,
            text=customer_headings[c],
            anchor="center",
            command=lambda _c=c: app._sort_tree_column(app.customer_tree, _c),
        )
    app.customer_tree.column("id", width=100, anchor="center", stretch=False)
    app.customer_tree.column("name", width=360, anchor="center", stretch=False)
    app.customer_tree.column("phone", width=220, anchor="center", stretch=False)
    app.customer_tree.column("company", width=300, anchor="center", stretch=False)
    app.customer_tree.column("notes", width=520, anchor="center", stretch=True)
    app.customer_tree.column("outstanding", width=190, anchor="center", stretch=False)
    app.customer_tree.column("trucks", width=220, anchor="center", stretch=False)
    app.customer_tree.grid(row=1, column=0, sticky="nsew", padx=10)
    customer_vsb = ttk.Scrollbar(frame, orient="vertical", command=app.customer_tree.yview)
    app.customer_tree.configure(yscrollcommand=customer_vsb.set)
    customer_vsb.grid(row=1, column=1, sticky="ns", padx=(0, 10))
    app._init_tree_striping(app.customer_tree)
    app.customer_tree.bind("<<TreeviewSelect>>", app._on_customer_tree_select)

    def _on_customer_tree_double_click(event):
        region = app.customer_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = app.customer_tree.identify_row(event.y)
        if not row_id:
            return
        app.customer_tree.selection_set(row_id)
        app.customer_tree.focus(row_id)
        app.edit_selected_customer()

    app.customer_tree.bind("<Double-1>", _on_customer_tree_double_click)

    form = ttk.LabelFrame(frame, text="Add Customer", padding="10")
    form.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
    app._customer_form = form
    for i in range(8):
        form.columnconfigure(i, weight=1 if i == 7 else 0)

    ttk.Label(form, text="Name*", font=("", 9, "bold")).grid(row=0, column=0, sticky="w", padx=6, pady=8)
    app.c_name = ttk.Entry(form, width=25)
    app.c_name.grid(row=0, column=1, sticky="w", padx=6, pady=8)
    add_placeholder(app.c_name, "Enter customer name...")
    app.c_name.bind("<Return>", lambda e: app.add_customer())

    ttk.Label(form, text="Phone").grid(row=0, column=2, sticky="w", padx=6, pady=8)
    app.c_phone = ttk.Entry(form, width=18)
    app.c_phone.grid(row=0, column=3, sticky="w", padx=6, pady=8)
    add_placeholder(app.c_phone, "Phone number...")
    app.c_phone.bind("<Return>", lambda e: app.add_customer())

    ttk.Label(form, text="Company").grid(row=0, column=4, sticky="w", padx=6, pady=8)
    app.c_company = ttk.Entry(form, width=22)
    app.c_company.grid(row=0, column=5, sticky="w", padx=6, pady=8)
    add_placeholder(app.c_company, "Company name...")
    app.c_company.bind("<Return>", lambda e: app.add_customer())

    ttk.Label(form, text="Notes").grid(row=1, column=0, sticky="w", padx=6, pady=8)
    app.c_notes = ttk.Entry(form, width=80)
    app.c_notes.grid(row=1, column=1, columnspan=5, sticky="ew", padx=6, pady=8)
    add_placeholder(app.c_notes, "Additional notes...")
    app.c_notes.bind("<Return>", lambda e: app.add_customer())

    btn_frame = ttk.Frame(form)
    btn_frame.grid(row=0, column=6, rowspan=2, padx=8, pady=6)
    ttk.Button(btn_frame, text="🟢 Add Customer", command=app.add_customer).pack(ipadx=8, ipady=6)
    ttk.Label(btn_frame, text="(Enter in any field)", font=("", 8), foreground="gray").pack()

    app.view_trucks_btn = ttk.Button(
        form,
        text="View Trucks",
        command=app._view_selected_customer_trucks,
        style="ViewTrucks.TButton",
        state="disabled",
    )
    app.view_trucks_btn.grid(row=0, column=7, rowspan=2, sticky="nsew", padx=(16, 6), pady=8)
