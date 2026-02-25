import tkinter as tk
from tkinter import ttk


def build_histories_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)
    top_bar = ttk.Frame(frame)
    top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0))
    ttk.Label(top_bar, text="Blackbox Log (all actions and events)", font=("Segoe UI", 14, "bold")).pack(side="left")
    ttk.Button(top_bar, text="Refresh", command=app.refresh_histories).pack(side="right")
    app.histories_text = tk.Text(frame, wrap="none", state="disabled", font=("Consolas", 10))
    app.histories_text.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=10)
    scrollbar_v = ttk.Scrollbar(frame, orient="vertical", command=app.histories_text.yview)
    scrollbar_h = ttk.Scrollbar(frame, orient="horizontal", command=app.histories_text.xview)
    app.histories_text.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
    scrollbar_v.grid(row=1, column=1, sticky="ns", pady=10)
    scrollbar_h.grid(row=2, column=0, sticky="ew", padx=(10, 0))
