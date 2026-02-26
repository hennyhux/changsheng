from __future__ import annotations

from datetime import date
from typing import Callable
import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename
from core.app_logging import trace


@trace
def export_customer_ledger_xlsx(
    parent: tk.Misc,
    tree: tk.Misc,
    customer_id: int,
    customer_name: str,
    customer_phone: str,
    customer_company: str,
    summary_text: str,
    log_action: Callable[[str, str], None],
    default_date: str | None = None,
) -> None:
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        messagebox.showerror("Missing Dependency", "openpyxl is required for XLSX export.")
        return

    default_date = default_date or date.today().isoformat()
    fp = asksaveasfilename(
        title="Export Ledger",
        defaultextension=".xlsx",
        initialfile=f"ledger_{customer_name.replace(' ', '_')}_{default_date}.xlsx",
        filetypes=[("Excel Workbook", "*.xlsx")],
        parent=parent,
    )
    if not fp:
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ledger"

    bold = Font(bold=True)
    green_fill = PatternFill("solid", fgColor="DDFFDD")
    gray_fill = PatternFill("solid", fgColor="EEEEEE")
    header_fill = PatternFill("solid", fgColor="D9E1F2")
    center = Alignment(horizontal="center")
    left = Alignment(horizontal="left")

    table_cols = ["A", "B", "C", "D", "E", "F", "G"]

    ws.append(["Customer Ledger"])
    ws.merge_cells("A1:G1")
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = left

    ws.append(["Customer ID", customer_id, "Name", customer_name])
    ws.append(["Phone", customer_phone or "—", "Company", customer_company or "—"])
    for cell in ws[2]:
        cell.font = bold
    for cell in ws[3]:
        cell.font = bold
    ws.append([])

    header_row = ["Entry", "Date / Period", "Billed", "Paid", "Outstanding", "Scope / Method", "Notes / Reference"]
    ws.append(header_row)
    for cell in ws[ws.max_row]:
        cell.font = bold
        cell.alignment = center
        cell.fill = header_fill

    ws.freeze_panes = "A6"

    def _clean_entry(text: str) -> str:
        t = str(text or "").replace("📋 ", "")
        t = t.replace("   └ ", "")
        return t.strip()

    def _money_to_float(text: str):
        try:
            return float(str(text).replace("$", "").replace(",", "").strip())
        except Exception:
            return None

    for iid in tree.get_children(""):
        row_vals = list(tree.item(iid, "values"))
        row_tags = tree.item(iid, "tags")
        if row_vals:
            row_vals[0] = _clean_entry(row_vals[0])

        ws.append(list(row_vals))
        fill = green_fill if "contract_active" in row_tags else gray_fill
        for cell in ws[ws.max_row]:
            cell.fill = fill
            cell.font = bold

        billed = _money_to_float(row_vals[2] if len(row_vals) > 2 else "")
        paid = _money_to_float(row_vals[3] if len(row_vals) > 3 else "")
        bal = _money_to_float(row_vals[4] if len(row_vals) > 4 else "")
        if billed is not None:
            ws.cell(ws.max_row, 3, billed).number_format = "$#,##0.00"
        if paid is not None:
            ws.cell(ws.max_row, 4, paid).number_format = "$#,##0.00"
        if bal is not None:
            ws.cell(ws.max_row, 5, bal).number_format = "$#,##0.00"

        for child in tree.get_children(iid):
            child_vals = list(tree.item(child, "values"))
            if child_vals:
                child_vals[0] = _clean_entry(child_vals[0])
            ws.append(child_vals)
            child_paid = _money_to_float(child_vals[3] if len(child_vals) > 3 else "")
            if child_paid is not None:
                ws.cell(ws.max_row, 4, child_paid).number_format = "$#,##0.00"

    ws.append([])
    ws.append([summary_text])
    ws.merge_cells(f"A{ws.max_row}:G{ws.max_row}")
    ws.cell(ws.max_row, 1).font = Font(bold=True)
    ws.cell(ws.max_row, 1).alignment = left

    for col in table_cols:
        max_len = 0
        for row_i in range(1, ws.max_row + 1):
            val = ws[f"{col}{row_i}"].value
            max_len = max(max_len, len(str(val or "")))
        ws.column_dimensions[col].width = min(max(max_len + 2, 12), 48)

    wb.save(fp)
    log_action("EXPORT_LEDGER", f"Exported ledger for Customer ID {customer_id} ({customer_name}) to {fp}")
    messagebox.showinfo("Exported", f"Ledger saved to:\n{fp}")
