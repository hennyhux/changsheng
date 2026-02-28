from __future__ import annotations

from typing import Iterable
import tkinter as tk
from tkinter import ttk
from core.app_logging import trace
from data.language_map import translate_widget_tree, EN_TO_ZH, ZH_TO_EN


@trace
def show_contract_payment_history(parent: tk.Misc, contract_info: dict, rows: Iterable[dict]) -> None:
    rows = list(rows)

    win = tk.Toplevel(parent)
    win.title(f"Payment History — Contract #{contract_info['contract_id']}")
    win.resizable(True, True)
    win.geometry("1600x900")
    win.minsize(1400, 800)
    win.transient(parent)
    win.grab_set()

    outstanding_value = contract_info.get("outstanding")
    if outstanding_value is not None:
        out_bar = ttk.Frame(win)
        out_bar.pack(fill="x", padx=12, pady=(10, 0))
        ttk.Label(
            out_bar,
            text=f"Current Outstanding: {outstanding_value}",
            foreground="#b00020",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="right")

    hdr = ttk.LabelFrame(win, text="Contract Details")
    hdr.pack(fill="x", padx=12, pady=(8, 4))
    details = [
        ("Contract ID", str(contract_info["contract_id"])),
        ("Status", contract_info["status"]),
        ("Customer", contract_info["customer"]),
        ("Scope", contract_info["scope"]),
        ("Rate", contract_info["rate"]),
        ("Start", contract_info["start"]),
        ("End", contract_info["end"]),
    ]
    for col, (label, val) in enumerate(details):
        ttk.Label(hdr, text=f"{label}:", font=("TkDefaultFont", 9, "bold")).grid(
            row=0, column=col * 2, sticky="e", padx=(8, 2), pady=6)
        ttk.Label(hdr, text=val).grid(
            row=0, column=col * 2 + 1, sticky="w", padx=(0, 12), pady=6)

    tbl_frame = ttk.Frame(win)
    tbl_frame.pack(fill="both", expand=True, padx=12, pady=4)

    hist_cols = ("num", "paid_at", "amount", "method", "reference", "invoice_ym", "notes")
    hist_headings = {
        "num": "#",
        "paid_at": "Paid Date",
        "amount": "Amount",
        "method": "Method",
        "reference": "Reference",
        "invoice_ym": "Invoice Month",
        "notes": "Notes",
    }
    hist_widths = {
        "num": 40,
        "paid_at": 120,
        "amount": 90,
        "method": 90,
        "reference": 110,
        "invoice_ym": 110,
        "notes": 220,
    }

    hist_tree = ttk.Treeview(tbl_frame, columns=hist_cols, show="headings", height=14)
    for c in hist_cols:
        hist_tree.heading(c, text=hist_headings[c], anchor="center")
        hist_tree.column(c, width=hist_widths[c], anchor="center")
    hist_tree.column("notes", anchor="w")

    vsb = ttk.Scrollbar(tbl_frame, orient="vertical", command=hist_tree.yview)
    hist_tree.configure(yscrollcommand=vsb.set)
    hist_tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    tbl_frame.columnconfigure(0, weight=1)
    tbl_frame.rowconfigure(0, weight=1)

    total_paid = 0.0
    for idx, r in enumerate(rows, start=1):
        amt = float(r["amount"])
        total_paid += amt
        hist_tree.insert(
            "",
            "end",
            values=(
                idx,
                r["paid_at"],
                f"${amt:.2f}",
                r["method"],
                r["reference"],
                r["invoice_ym"],
                r["notes"],
            ),
        )

    ftr = ttk.Frame(win)
    ftr.pack(fill="x", padx=12, pady=(4, 10))
    summary_text = (
        f"Total payments: {len(rows)}     Total paid: ${total_paid:.2f}"
        if rows else "No payments recorded for this contract."
    )
    ttk.Label(ftr, text=summary_text, font=("TkDefaultFont", 10, "bold")).pack(side="left")
    ttk.Button(ftr, text="Close", command=win.destroy).pack(side="right")

    lang = getattr(parent, "current_language", "en")
    if lang != "en":
        translate_widget_tree(win, lang)
        mapping = EN_TO_ZH
        for c in hist_cols:
            heading_text = hist_headings[c]
            if heading_text in mapping:
                hist_tree.heading(c, text=mapping[heading_text])
