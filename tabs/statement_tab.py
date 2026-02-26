import tkinter as tk
from tkinter import ttk

from utils.billing_date_utils import today, ym
from core.app_logging import trace


@trace
def build_statement_tab(app, frame):
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(2, weight=1)

    controls = ttk.Frame(frame)
    controls.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
    controls.columnconfigure(9, weight=1)

    ttk.Label(controls, text="Month (YYYY-MM):").grid(row=0, column=0, sticky="w", padx=4)
    app.statement_month = ttk.Entry(controls, width=10)
    app.statement_month.insert(0, ym(today()))
    app.statement_month.grid(row=0, column=1, sticky="w", padx=4)

    ttk.Button(controls, text="Refresh Statement", command=app.refresh_statement).grid(row=0, column=2, padx=8)

    ttk.Label(controls, text="Chart:").grid(row=0, column=3, sticky="e", padx=(14, 4))
    app.statement_chart_mode = tk.StringVar(value="combo")
    app.statement_chart_mode_combo = ttk.Combobox(
        controls,
        width=10,
        state="readonly",
        values=["Combo", "Bar", "Line"],
    )
    app.statement_chart_mode_combo.grid(row=0, column=4, sticky="w", padx=4)
    app.statement_chart_mode_combo.set("Combo")

    def _on_chart_mode_changed(_event=None):
        selected = app.statement_chart_mode_combo.get().strip().lower()
        if selected in {"combo", "bar", "line"}:
            app.statement_chart_mode.set(selected)
        app.refresh_statement()

    app.statement_chart_mode_combo.bind("<<ComboboxSelected>>", _on_chart_mode_changed)

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

    chart = ttk.LabelFrame(frame, text="Expected Monthly Revenue (Last 12 Months)")
    chart.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
    chart.columnconfigure(0, weight=1)
    chart.rowconfigure(0, weight=1)

    app.statement_expected_chart_canvas = tk.Canvas(
        chart,
        height=300,
        bg="#ffffff",
        highlightthickness=0,
        bd=0,
    )
    app.statement_expected_chart_canvas.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
