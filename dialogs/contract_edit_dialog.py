from __future__ import annotations

from typing import Callable, Iterable
import tkinter as tk
from tkinter import ttk
from core.app_logging import trace
from data.language_map import translate_widget_tree
from ui.ui_helpers import center_dialog_on_parent


@trace
def open_contract_edit_dialog(
    parent: tk.Misc,
    contract_id: int,
    row: dict,
    customer_values: Iterable[str],
    usdot_values: Iterable[str],
    date_input_factory: Callable[..., ttk.Entry],
    make_searchable_combo: Callable[[ttk.Combobox], None],
    on_save: Callable[[ttk.Combobox, ttk.Combobox, str, str, str, str, bool], bool],
    optional_date_clear_on_blur_cb: Callable[[tk.Widget], None] = None,
) -> None:
    def row_get(key: str, default=None):
        try:
            return row[key]
        except Exception:
            return default

    win = tk.Toplevel(parent)
    win.title(f"Edit Contract #{contract_id}")
    win.geometry("1800x560")
    win.minsize(1220, 500)
    win.resizable(True, True)
    win.transient(parent)
    win.grab_set()
    win.bind("<Escape>", lambda _e: win.destroy())
    center_dialog_on_parent(win, parent, 1800, 560)

    frm = ttk.Frame(win, padding=12)
    frm.pack(fill="both", expand=True)
    frm.columnconfigure(1, weight=1)
    frm.columnconfigure(3, weight=1)

    ttk.Label(frm, text="Customer*").grid(row=0, column=0, sticky="w", padx=6, pady=6)
    customer_combo = ttk.Combobox(frm, width=42)
    customer_combo.grid(row=0, column=1, sticky="ew", padx=6, pady=6)
    make_searchable_combo(customer_combo)

    ttk.Label(frm, text="USDOT*").grid(row=0, column=2, sticky="w", padx=6, pady=6)
    usdot_combo = ttk.Combobox(frm, width=30)
    usdot_combo.grid(row=0, column=3, sticky="ew", padx=6, pady=6)
    make_searchable_combo(usdot_combo)

    ttk.Label(frm, text="Rate ($/mo)*").grid(row=1, column=2, sticky="w", padx=6, pady=6)
    rate_entry = ttk.Entry(frm, width=12)
    rate_entry.grid(row=1, column=3, sticky="ew", padx=6, pady=6)
    try:
        monthly_rate = float(row_get("monthly_rate", 0.0) or 0.0)
    except Exception:
        monthly_rate = 0.0
    rate_entry.insert(0, f"{monthly_rate:.2f}")

    ttk.Separator(frm, orient="horizontal").grid(row=2, column=0, columnspan=4, sticky="ew", pady=(6, 6))

    ttk.Label(frm, text="Start YYYY-MM-DD").grid(row=3, column=0, sticky="w", padx=6, pady=6)
    start_entry = date_input_factory(frm, width=12, default_iso=row_get("start_date"))
    start_entry.grid(row=3, column=1, sticky="w", padx=6, pady=6)

    ttk.Label(frm, text="End YYYY-MM-DD (optional)").grid(row=3, column=2, sticky="w", padx=6, pady=6)
    end_entry = date_input_factory(frm, width=12, default_iso=row_get("end_date"))
    end_entry.grid(row=3, column=3, sticky="w", padx=6, pady=6)
    if optional_date_clear_on_blur_cb is not None:
        optional_date_clear_on_blur_cb(end_entry)
    ttk.Button(end_entry.master, text="Clear", command=lambda: end_entry.delete(0, tk.END)).grid(
        row=3, column=4, sticky="w", padx=(0, 6), pady=6
    )

    ttk.Label(frm, text="Notes").grid(row=4, column=0, sticky="w", padx=6, pady=6)
    notes_entry = ttk.Entry(frm)
    notes_entry.grid(row=4, column=1, columnspan=3, sticky="ew", padx=6, pady=6)
    notes_value = row_get("notes")
    if notes_value:
        notes_entry.insert(0, str(notes_value))

    is_active_var = tk.BooleanVar(value=bool(row_get("is_active")))
    ttk.Checkbutton(frm, text="Active", variable=is_active_var).grid(row=5, column=0, sticky="w", padx=6, pady=(4, 10))

    customer_values = list(customer_values)
    usdot_values = list(usdot_values)
    customer_combo["values"] = customer_values
    customer_combo._search_all_values = list(customer_values)
    usdot_combo["values"] = usdot_values
    usdot_combo._search_all_values = list(usdot_values)

    customer_id_value = row_get("customer_id")
    if customer_id_value is not None:
        for i, v in enumerate(customer_values):
            if v.startswith(f"{int(customer_id_value)}:"):
                customer_combo.current(i)
                break

    usdot_id_value = row_get("usdot_account_id")
    if usdot_id_value:
        for i, v in enumerate(usdot_values):
            if v.startswith(f"{int(usdot_id_value)}:"):
                usdot_combo.current(i)
                break

    def _save_contract():
        rate_str = rate_entry.get()
        start_str = start_entry.get().strip()
        end_str = end_entry.get().strip()
        notes_str = notes_entry.get()
        is_active = bool(is_active_var.get())

        if on_save(customer_combo, usdot_combo, rate_str, start_str, end_str, notes_str, is_active):
            win.destroy()

    action_bar = ttk.Frame(frm)
    action_bar.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(6, 0))
    action_bar.columnconfigure(0, weight=1)
    action_bar.columnconfigure(1, weight=1)

    ttk.Button(action_bar, text="Save Changes", command=_save_contract).grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=4)
    ttk.Button(action_bar, text="Cancel", command=win.destroy).grid(row=0, column=1, sticky="ew", padx=(6, 0), ipady=4)

    rate_entry.bind("<Return>", lambda _e: _save_contract())
    notes_entry.bind("<Return>", lambda _e: _save_contract())
    customer_combo.focus_set()

    lang = getattr(parent, "current_language", "en")
    if lang != "en":
        translate_widget_tree(win, lang)
