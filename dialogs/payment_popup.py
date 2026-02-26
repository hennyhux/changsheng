from __future__ import annotations

from typing import Callable
import tkinter as tk
from tkinter import ttk
from core.app_logging import trace
from core.config import FONTS


@trace
def show_payment_popup(
    parent: tk.Misc,
    contract_id: int,
    plate_label: str | None,
    balance: float,
    default_date: str,
    on_submit: Callable[[str, str, str, str, str], bool],
    date_input_factory: Callable[[tk.Widget, int, str | None], tk.Widget] | None = None,
) -> None:
    base_font = FONTS["base"]
    heading_font = FONTS["heading"]
    base_font_size = 12
    if isinstance(base_font, tuple) and len(base_font) >= 2:
        try:
            base_font_size = int(base_font[1])
        except Exception:
            base_font_size = 12

    popup_width = max(900, int(base_font_size * 62))
    popup_height = max(520, int(base_font_size * 36))

    popup = tk.Toplevel(parent)
    title_suffix = f" - Plate {plate_label}" if plate_label else ""
    popup.title(f"Record Payment{title_suffix}")
    popup.geometry(f"{popup_width}x{popup_height}")
    popup.minsize(max(860, popup_width - 80), max(500, popup_height - 60))
    popup.resizable(True, True)

    popup.transient(parent)
    popup.grab_set()

    popup.update_idletasks()
    try:
        parent.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + max(0, (parent_w - popup_width) // 2)
        y = parent_y + max(0, (parent_h - popup_height) // 2)
    except Exception:
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        x = max(0, (screen_w - popup_width) // 2)
        y = max(0, (screen_h - popup_height) // 2)
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

    main = ttk.Frame(popup, padding="22")
    main.pack(fill="both", expand=True)
    main.columnconfigure(0, minsize=260)
    main.columnconfigure(1, weight=1)

    ttk.Label(main, text="Plate:", font=heading_font).grid(row=0, column=0, sticky="w", padx=(0, 14), pady=(0, 14))
    ttk.Label(main, text=(plate_label or "(customer-level)"), font=base_font).grid(row=0, column=1, sticky="w", pady=(0, 14))

    ttk.Label(main, text="Outstanding Balance:", font=heading_font).grid(row=1, column=0, sticky="w", padx=(0, 14), pady=(0, 14))
    balance_color = "#1b5e20" if abs(balance) <= 0.01 else "#b00020"
    bal_label = tk.Label(main, text=f"${balance:.2f}", font=heading_font, foreground=balance_color)
    bal_label.grid(row=1, column=1, sticky="w", pady=(0, 14))

    ttk.Label(main, text="Amount:", font=base_font).grid(row=2, column=0, sticky="w", padx=(0, 14), pady=(0, 10))
    pay_amount = ttk.Entry(main, width=34, font=base_font)
    pay_amount.insert(0, f"{balance:.2f}")
    pay_amount.grid(row=2, column=1, sticky="ew", pady=(0, 10), ipady=6)
    pay_amount.focus()

    ttk.Label(main, text="Payment Date:", font=base_font).grid(row=3, column=0, sticky="w", padx=(0, 14), pady=(0, 10))
    date_row = ttk.Frame(main)
    date_row.grid(row=3, column=1, sticky="ew", pady=(0, 10))
    date_row.columnconfigure(0, weight=1)

    if date_input_factory is not None:
        pay_date = date_input_factory(date_row, width=28, default_iso=default_date)
        pay_date.grid(row=0, column=0, sticky="ew")
    else:
        pay_date = ttk.Entry(date_row, width=34, font=base_font)
        pay_date.insert(0, default_date)
        pay_date.grid(row=0, column=0, sticky="ew")
    if hasattr(pay_date, "configure"):
        try:
            pay_date.configure(font=base_font)
        except Exception:
            pass

    ttk.Label(main, text="Method:", font=base_font).grid(row=4, column=0, sticky="w", padx=(0, 14), pady=(0, 10))
    pay_method = ttk.Combobox(main, state="readonly", values=["cash", "card", "zelle", "venmo", "other"], width=30, font=base_font)
    pay_method.set("cash")
    pay_method.grid(row=4, column=1, sticky="ew", pady=(0, 10), ipady=4)

    ttk.Label(main, text="Reference:", font=base_font).grid(row=5, column=0, sticky="w", padx=(0, 14), pady=(0, 10))
    pay_ref = ttk.Entry(main, width=34, font=base_font)
    pay_ref.grid(row=5, column=1, sticky="ew", pady=(0, 10), ipady=6)

    ttk.Label(main, text="Notes:", font=base_font).grid(row=6, column=0, sticky="nw", padx=(0, 14), pady=(0, 12))
    pay_notes = tk.Text(main, width=44, height=7, font=base_font)
    pay_notes.grid(row=6, column=1, sticky="nsew", pady=(0, 14))
    main.rowconfigure(6, weight=1)

    btn_frame = ttk.Frame(main)
    btn_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 0))
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

    ttk.Button(btn_frame, text="Record Payment", command=on_record).grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=10)
    ttk.Button(btn_frame, text="Cancel", command=popup.destroy).grid(row=0, column=1, sticky="ew", padx=(8, 0), ipady=10)


def _set_entry_text(widget: tk.Widget, value: str) -> None:
    if hasattr(widget, "delete") and hasattr(widget, "insert"):
        widget.delete(0, tk.END)
        widget.insert(0, value)
