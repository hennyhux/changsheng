import tkinter as tk
from tkinter import ttk
from core.app_logging import trace


@trace
def build_histories_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)
    top_bar = ttk.Frame(frame)
    top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0))
    top_bar.columnconfigure(5, weight=1)
    ttk.Label(top_bar, text="Blackbox Log (all actions and events)", font=("Segoe UI", 14, "bold")).pack(side="left")
    ttk.Label(top_bar, text="Quick type:").pack(side="left", padx=(14, 4))
    app.histories_statement_type = ttk.Combobox(
        top_bar,
        width=24,
        state="readonly",
        values=("(Any)",),
    )
    app.histories_statement_type.set("(Any)")
    app.histories_statement_type.pack(side="left")

    def _on_statement_type_selected(_event=None):
        selected = app.histories_statement_type.get().strip()
        app.histories_filter.delete(0, tk.END)
        if selected and selected != "(Any)":
            app.histories_filter.insert(0, selected)
        app.refresh_histories()

    app.histories_statement_type.bind("<<ComboboxSelected>>", _on_statement_type_selected)

    ttk.Label(top_bar, text="Filter statement:").pack(side="left", padx=(14, 4))
    app.histories_filter = ttk.Entry(top_bar, width=26)
    app.histories_filter.pack(side="left")
    app.histories_filter.bind("<Return>", lambda _e: app.refresh_histories())
    ttk.Button(top_bar, text="Apply", command=app.refresh_histories).pack(side="left", padx=(6, 4))
    ttk.Button(
        top_bar,
        text="Clear",
        command=lambda: (app.histories_filter.delete(0, tk.END), app.refresh_histories()),
    ).pack(side="left")
    ttk.Button(top_bar, text="Refresh", command=app.refresh_histories).pack(side="right")
    app.histories_text = tk.Text(frame, wrap="none", state="disabled", font=("Consolas", 10))
    app.histories_text.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=10)
    scrollbar_v = ttk.Scrollbar(frame, orient="vertical", command=app.histories_text.yview)
    scrollbar_h = ttk.Scrollbar(frame, orient="horizontal", command=app.histories_text.xview)
    app.histories_text.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
    scrollbar_v.grid(row=1, column=1, sticky="ns", pady=10)
    scrollbar_h.grid(row=2, column=0, sticky="ew", padx=(10, 0))
