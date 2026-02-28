from __future__ import annotations

from typing import Callable, Iterable
from core.config import FONTS
import tkinter as tk
from tkinter import ttk
from core.app_logging import trace
from data.language_map import translate_widget_tree


@trace
def show_import_preview(
    parent: tk.Misc,
    file_path: str,
    new_customers: Iterable,
    skip_customers: Iterable,
    new_trucks: Iterable,
    skip_trucks: Iterable,
    new_contracts: Iterable,
    invalid_rows: Iterable[str],
    on_confirm: Callable[[], bool],
) -> None:
    new_customers = list(new_customers)
    skip_customers = list(skip_customers)
    new_trucks = list(new_trucks)
    skip_trucks = list(skip_trucks)
    new_contracts = list(new_contracts)
    invalid_rows = list(invalid_rows)

    preview = tk.Toplevel(parent)
    preview.title("Import Preview")
    preview.geometry("1000x540")
    preview.resizable(True, True)
    preview.transient(parent)
    preview.grab_set()
    preview.columnconfigure(0, weight=1)
    preview.rowconfigure(1, weight=1)

    filename = file_path.replace(chr(92), "/").split("/")[-1]
    ttk.Label(
        preview,
        text=f"File: {filename}",
        font=FONTS.get("base"),
        foreground="#555",
    ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))

    nb = ttk.Notebook(preview)
    nb.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

    def _make_preview_tab(parent_nb, title, items, columns, get_vals):
        tab = ttk.Frame(parent_nb)
        parent_nb.add(tab, text=title)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        tree = ttk.Treeview(tab, columns=columns, show="headings", height=12)
        for c in columns:
            tree.heading(c, text=c, anchor="center")
            tree.column(c, width=120, anchor="center")
        vsb = ttk.Scrollbar(tab, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        for item in items:
            tree.insert("", "end", values=get_vals(item))

    _make_preview_tab(
        nb, f"✅ New Customers ({len(new_customers)})",
        new_customers, ("Name", "Phone", "Company"),
        lambda r: (r["name"], r["phone"] or "", r["company"] or ""),
    )
    _make_preview_tab(
        nb, f"⏭ Skip Customers ({len(skip_customers)})",
        skip_customers, ("Name", "Phone", "Company"),
        lambda r: (r["name"], r["phone"] or "", r["company"] or ""),
    )
    _make_preview_tab(
        nb, f"✅ New Trucks ({len(new_trucks)})",
        new_trucks, ("Plate", "State", "Make", "Model", "Customer"),
        lambda r: (r["plate"], r["state"] or "", r["make"] or "", r["model"] or "", r["customer_name"]),
    )
    _make_preview_tab(
        nb, f"⏭ Skip Trucks ({len(skip_trucks)})",
        skip_trucks, ("Plate", "State", "Make", "Model", "Customer"),
        lambda r: (r["plate"], r["state"] or "", r["make"] or "", r["model"] or "", r["customer_name"]),
    )
    if new_contracts:
        _make_preview_tab(
            nb, f"✅ New Contracts ({len(new_contracts)})",
            new_contracts, ("Plate", "Customer", "Rate ($/mo)", "Start Date"),
            lambda r: (r["plate"], r["customer_name"], f"${r['rate']:.2f}", r["start_date"]),
        )

    ftr = ttk.Frame(preview)
    ftr.grid(row=2, column=0, sticky="ew", padx=12, pady=(4, 10))
    contract_note = f", {len(new_contracts)} contract(s)" if new_contracts else ""
    invalid_note = f". Ignoring {len(invalid_rows)} invalid row(s)" if invalid_rows else ""
    ttk.Label(
        ftr,
        text=(
            f"Will create {len(new_customers)} customer(s), {len(new_trucks)} truck(s){contract_note}. "
            f"Skipping {len(skip_customers)} existing customer(s) and {len(skip_trucks)} existing truck(s){invalid_note}."
        ),
        font=FONTS.get("label_bold"),
    ).pack(side="left")

    def _confirm():
        if on_confirm():
            preview.destroy()

    ttk.Button(ftr, text="Cancel", command=preview.destroy).pack(side="right")
    ttk.Button(ftr, text="Confirm Import", command=_confirm).pack(side="right", padx=(0, 8))

    lang = getattr(parent, "current_language", "en")
    if lang != "en":
        translate_widget_tree(preview, lang)
