import tkinter as tk
from tkinter import ttk

from billing_date_utils import today, ym


def build_statement_tab(app, frame):
    frame.columnconfigure(0, weight=1)

    controls = ttk.Frame(frame)
    controls.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
    controls.columnconfigure(6, weight=1)

    ttk.Label(controls, text="Month (YYYY-MM):").grid(row=0, column=0, sticky="w", padx=4)
    app.statement_month = ttk.Entry(controls, width=10)
    app.statement_month.insert(0, ym(today()))
    app.statement_month.grid(row=0, column=1, sticky="w", padx=4)

    ttk.Button(controls, text="Refresh Statement", command=app.refresh_statement).grid(row=0, column=2, padx=8)

    summary = ttk.LabelFrame(frame, text="Monthly Totals")
    summary.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

    app.statement_expected_var = tk.StringVar(value="$0.00")
    app.statement_paid_var = tk.StringVar(value="$0.00")
    app.statement_balance_var = tk.StringVar(value="$0.00")

    ttk.Label(summary, text="Expected for month:").grid(row=0, column=0, sticky="w", padx=8, pady=8)
    ttk.Label(summary, textvariable=app.statement_expected_var).grid(row=0, column=1, sticky="w", padx=8, pady=8)

    ttk.Label(summary, text="Paid toward month invoices:").grid(row=1, column=0, sticky="w", padx=8, pady=8)
    ttk.Label(summary, textvariable=app.statement_paid_var).grid(row=1, column=1, sticky="w", padx=8, pady=8)

    ttk.Label(summary, text="Outstanding:").grid(row=2, column=0, sticky="w", padx=8, pady=8)
    ttk.Label(summary, textvariable=app.statement_balance_var).grid(row=2, column=1, sticky="w", padx=8, pady=8)
