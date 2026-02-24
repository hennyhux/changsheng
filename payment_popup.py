from __future__ import annotations

from typing import Callable
import tkinter as tk
from tkinter import ttk


def show_payment_popup(
    parent: tk.Misc,
    contract_id: int,
    plate_label: str | None,
    balance: float,
    default_date: str,
    on_submit: Callable[[str, str, str, str, str], bool],
    date_input_factory: Callable[[tk.Widget, int, str | None], tk.Widget] | None = None,
    set_date_today_cb: Callable[[tk.Widget], None] | None = None,
) -> None:
    popup = tk.Toplevel(parent)
    title_suffix = f" - Plate {plate_label}" if plate_label else ""
    popup.title(f"Record Payment{title_suffix}")
    popup.geometry("800x400")
    popup.resizable(False, False)

    popup.transient(parent)
    popup.grab_set()

    main = ttk.Frame(popup, padding="15")
    main.pack(fill="both", expand=True)
    main.columnconfigure(0, minsize=190)
    main.columnconfigure(1, weight=1)

    ttk.Label(main, text="Plate:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 10))
    ttk.Label(main, text=(plate_label or "(customer-level)"), font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", pady=(0, 10))

    ttk.Label(main, text="Outstanding Balance:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(0, 10))
    balance_color = "#1b5e20" if abs(balance) <= 0.01 else "#b00020"
    bal_label = tk.Label(main, text=f"${balance:.2f}", font=("Segoe UI", 10), foreground=balance_color)
    bal_label.grid(row=1, column=1, sticky="w", pady=(0, 10))

    ttk.Label(main, text="Amount:", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
    pay_amount = ttk.Entry(main, width=28, font=("Segoe UI", 10))
    pay_amount.insert(0, f"{balance:.2f}")
    pay_amount.grid(row=2, column=1, sticky="ew", pady=(0, 8))
    pay_amount.focus()

    ttk.Label(main, text="Payment Date:", font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
    date_row = ttk.Frame(main)
    date_row.grid(row=3, column=1, sticky="ew", pady=(0, 8))
    date_row.columnconfigure(0, weight=1)

    if date_input_factory is not None:
        pay_date = date_input_factory(date_row, width=22, default_iso=default_date)
        pay_date.grid(row=0, column=0, sticky="ew")
    else:
        pay_date = ttk.Entry(date_row, width=28, font=("Segoe UI", 10))
        pay_date.insert(0, default_date)
        pay_date.grid(row=0, column=0, sticky="ew")

    ttk.Label(main, text="Method:", font=("Segoe UI", 10)).grid(row=4, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
    pay_method = ttk.Combobox(main, state="readonly", values=["cash", "card", "zelle", "venmo", "other"], width=25, font=("Segoe UI", 10))
    pay_method.set("cash")
    pay_method.grid(row=4, column=1, sticky="ew", pady=(0, 8))

    ttk.Label(main, text="Reference:", font=("Segoe UI", 10)).grid(row=5, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
    pay_ref = ttk.Entry(main, width=28, font=("Segoe UI", 10))
    pay_ref.grid(row=5, column=1, sticky="ew", pady=(0, 8))

    ttk.Label(main, text="Notes:", font=("Segoe UI", 10)).grid(row=6, column=0, sticky="nw", padx=(0, 10), pady=(0, 10))
    pay_notes = tk.Text(main, width=34, height=4, font=("Segoe UI", 10))
    pay_notes.grid(row=6, column=1, sticky="nsew", pady=(0, 12))
    main.rowconfigure(6, weight=1)

    btn_frame = ttk.Frame(main)
    btn_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(4, 0))
    btn_frame.columnconfigure(0, weight=1)
    btn_frame.columnconfigure(1, weight=1)

    def on_record() -> None:
        amt_str = pay_amount.get().strip()
        paid_at = pay_date.get().strip()
        method = pay_method.get().strip() or "cash"
        ref = pay_ref.get()
        notes = pay_notes.get("1.0", tk.END)
        if on_submit(amt_str, paid_at, method, ref, notes):
            popup.destroy()

    pay_amount.bind("<Return>", lambda _e: on_record())
    pay_date.bind("<Return>", lambda _e: on_record())
    pay_method.bind("<Return>", lambda _e: on_record())
    pay_ref.bind("<Return>", lambda _e: on_record())

    ttk.Button(btn_frame, text="Record Payment", command=on_record).grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=4)
    ttk.Button(btn_frame, text="Cancel", command=popup.destroy).grid(row=0, column=1, sticky="ew", padx=(6, 0), ipady=4)


def _set_entry_text(widget: tk.Widget, value: str) -> None:
    if hasattr(widget, "delete") and hasattr(widget, "insert"):
        widget.delete(0, tk.END)
        widget.insert(0, value)
