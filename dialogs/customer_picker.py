from __future__ import annotations

from typing import Callable, Iterable
import tkinter as tk
from tkinter import ttk, messagebox
from core.app_logging import trace
from data.language_map import translate_widget_tree, EN_TO_ZH


@trace
def open_customer_picker(
    parent: tk.Misc,
    customers: Iterable,
    normalize: Callable[[str], str],
    on_select: Callable[[int], None],
) -> None:
    def cget(customer, key: str, default=None):
        try:
            return customer[key]
        except Exception:
            pass
        try:
            return getattr(customer, key)
        except Exception:
            return default

    customers = list(customers)
    if not customers:
        messagebox.showinfo("No customers", "No customers found. Add a customer first.")
        return

    picker = tk.Toplevel(parent)
    picker.title("Find Customer")
    picker.geometry("760x460")
    picker.minsize(680, 380)
    picker.transient(parent)
    picker.grab_set()
    picker.columnconfigure(0, weight=1)
    picker.rowconfigure(1, weight=1)

    top = ttk.Frame(picker)
    top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
    top.columnconfigure(1, weight=1)
    ttk.Label(top, text="Search customer:").grid(row=0, column=0, sticky="w", padx=(0, 8))
    search_entry = ttk.Entry(top)
    search_entry.grid(row=0, column=1, sticky="ew")
    search_entry.focus()

    cols = ("id", "name", "phone", "company")
    tree = ttk.Treeview(picker, columns=cols, show="headings", height=14)
    headings = {"id": "ID", "name": "Name", "phone": "Phone", "company": "Company"}
    widths = {"id": 80, "name": 260, "phone": 170, "company": 220}
    for c in cols:
        tree.heading(c, text=headings[c], anchor="center")
        tree.column(c, width=widths[c], anchor="center")
    tree.grid(row=1, column=0, sticky="nsew", padx=12)

    def _populate(rows: list) -> None:
        for item in tree.get_children():
            tree.delete(item)
        for customer in rows:
            tree.insert(
                "",
                "end",
                values=(
                    cget(customer, "id", ""),
                    cget(customer, "name", ""),
                    cget(customer, "phone", "") or "",
                    cget(customer, "company", "") or "",
                ),
            )

    def _filtered_rows() -> list:
        raw = search_entry.get()
        query = normalize(raw).lower()
        if not query:
            return customers
        return [
            customer
            for customer in customers
            if (
                query in str(cget(customer, "id", "")).lower()
                or query in str(cget(customer, "name", "") or "").lower()
                or query in str(cget(customer, "phone", "") or "").lower()
                or query in str(cget(customer, "company", "") or "").lower()
            )
        ]

    def _refresh_results(_event=None) -> None:
        _populate(_filtered_rows())
        children = tree.get_children()
        if children:
            tree.selection_set(children[0])
            tree.focus(children[0])

    def _select_customer(_event=None) -> None:
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a customer first.")
            return
        values = tree.item(sel[0], "values")
        if not values:
            return
        customer_id = int(values[0])
        on_select(customer_id)
        picker.destroy()

    def _on_tree_double_click(event) -> None:
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = tree.identify_row(event.y)
        if not row_id:
            return
        tree.selection_set(row_id)
        tree.focus(row_id)
        _select_customer()

    search_entry.bind("<KeyRelease>", _refresh_results)
    search_entry.bind("<Return>", _select_customer)
    tree.bind("<Double-1>", _on_tree_double_click)
    tree.bind("<Return>", _select_customer)

    btns = ttk.Frame(picker)
    btns.grid(row=2, column=0, sticky="ew", padx=12, pady=12)
    ttk.Button(btns, text="Select", command=_select_customer).pack(side="right")
    ttk.Button(btns, text="Cancel", command=picker.destroy).pack(side="right", padx=(0, 8))

    _populate(customers)
    children = tree.get_children()
    if children:
        tree.selection_set(children[0])
        tree.focus(children[0])

    lang = getattr(parent, "current_language", "en")
    if lang != "en":
        translate_widget_tree(picker, lang)
        for c in cols:
            if headings[c] in EN_TO_ZH:
                tree.heading(c, text=EN_TO_ZH[headings[c]])
