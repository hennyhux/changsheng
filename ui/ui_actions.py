from __future__ import annotations

import csv
import logging
import sqlite3
import threading
import tkinter as tk
from datetime import date, datetime, timedelta
from time import perf_counter
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING, Any, Callable

from utils.billing_date_utils import elapsed_months_inclusive, now_iso, parse_ym, parse_ymd, today, ym
from data.language_map import translate_widget_tree, EN_TO_ZH
from dialogs.contract_edit_dialog import open_contract_edit_dialog
from core.app_logging import trace, log_ux_action, get_trace_logger
from core.error_handler import safe_ui_action, safe_ui_action_returning
from dialogs.import_preview_dialog import show_import_preview
from dialogs.payment_popup import show_payment_popup
from ui.ui_helpers import create_date_input, make_optional_date_clear_on_blur
from utils.validation import (
    normalize_whitespace,
    optional_phone,
    optional_state,
    optional_text,
    positive_float,
    required_plate,
    required_text,
)
from core.config import FONTS

if TYPE_CHECKING:
    from data.database_service import DatabaseService


logger = logging.getLogger("changsheng_app")
trace_logger = get_trace_logger()


@safe_ui_action("Backup Database")
def backup_database_action(
    app: Any,
    db: "DatabaseService",
    get_last_backup_dir_cb: Callable[[], str | None],
    set_last_backup_dir_cb: Callable[[str], None],
    log_action_cb: Callable[[str, str], None],
) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = f"monthly_lot_backup_{timestamp}.db"
    backup_dir = get_last_backup_dir_cb()

    file_path = filedialog.asksaveasfilename(
        title="Save Database Backup",
        defaultextension=".db",
        initialfile=default_name,
        initialdir=backup_dir,
        filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
    )
    if not file_path:
        return

    try:
        db.backup_to(file_path)
    except Exception as exc:
        messagebox.showerror("Backup Failed", f"Could not create backup:\n{exc}")
        log_action_cb("BACKUP_DB_ERROR", f"Failed to backup database to {file_path}: {exc}")
        return

    log_action_cb("BACKUP_DB", f"Database backup saved to {file_path}")
    set_last_backup_dir_cb(file_path)
    messagebox.showinfo("Backup Complete", f"Database backup saved to:\n{file_path}")


@safe_ui_action("Restore Database")
def restore_database_action(
    app: Any,
    db: "DatabaseService",
    get_last_backup_dir_cb: Callable[[], str | None],
    set_last_backup_dir_cb: Callable[[str], None],
    log_action_cb: Callable[[str, str], None],
) -> None:
    initial_dir = get_last_backup_dir_cb()
    backup_file_path = filedialog.askopenfilename(
        title="Select Backup Database to Restore",
        initialdir=initial_dir,
        filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
    )
    if not backup_file_path:
        return

    confirmed = messagebox.askyesno(
        "Confirm Restore",
        (
            "Restore database from selected backup?\n\n"
            "Workflow:\n"
            "1) Validate backup\n"
            "2) Create safety backup of current DB\n"
            "3) Replace DB file\n"
            "4) Reopen and run smoke checks\n\n"
            "This may overwrite current data."
        ),
        icon="warning",
        default="no",
    )
    if not confirmed:
        return

    final_confirm = messagebox.askyesno(
        "⚠️ Final Confirmation",
        "Proceed with restore now?",
        icon="warning",
        default="no",
    )
    if not final_confirm:
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safety_backup_path = f"monthly_lot_pre_restore_{ts}.db"

    try:
        db.restore_from_backup(backup_file_path, safety_backup_path)

        smoke_counts = {
            "customers": db.count("customers", "1=1", ()),
            "trucks": db.count("trucks", "1=1", ()),
            "contracts": db.count("contracts", "1=1", ()),
            "invoices": db.count("invoices", "1=1", ()),
            "payments": db.count("payments", "1=1", ()),
        }

        app.refresh_customers()
        app.refresh_trucks()
        app.refresh_contracts()
        app.refresh_invoices()
        app.refresh_statement()
        app.refresh_overdue()
        app.refresh_dashboard()
        app.refresh_histories()

        set_last_backup_dir_cb(backup_file_path)
        log_action_cb(
            "RESTORE_DB",
            (
                f"Source Backup: {backup_file_path}, Safety Backup: {safety_backup_path}, "
                f"Smoke Counts: {smoke_counts}"
            ),
        )
        messagebox.showinfo(
            "Restore Complete",
            (
                "Database restored successfully.\n\n"
                f"Safety backup: {safety_backup_path}\n"
                f"Customers: {smoke_counts['customers']}, Trucks: {smoke_counts['trucks']}, "
                f"Contracts: {smoke_counts['contracts']}"
            ),
        )
    except Exception as exc:
        log_action_cb("RESTORE_DB_ERROR", f"Backup: {backup_file_path}, Error: {exc}")
        messagebox.showerror("Restore Failed", f"Could not restore database:\n{exc}")


@safe_ui_action("Export to CSV")
def export_customers_trucks_csv_action(
    app: Any,
    db: "DatabaseService",
    openpyxl_module: Any,
    search_query: str,
    show_invalid_cb: Callable[[str], None],
    log_action_cb: Callable[[str, str], None],
) -> None:
    if len(search_query) > 80:
        show_invalid_cb("Search text must be 80 characters or fewer.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if openpyxl_module is not None:
        default_name = f"customers_trucks_{timestamp}.xlsx"
        filetypes = [("Excel Workbook", "*.xlsx"), ("All Files", "*.*")]
        default_ext = ".xlsx"
    else:
        default_name = f"customers_trucks_{timestamp}.csv"
        filetypes = [("Tab-separated CSV", "*.csv"), ("All Files", "*.*")]
        default_ext = ".csv"

    file_path = filedialog.asksaveasfilename(
        title="Export Customers and Trucks",
        defaultextension=default_ext,
        initialfile=default_name,
        filetypes=filetypes,
    )
    if not file_path:
        return

    rows = db.get_customer_truck_export_rows(q=search_query if search_query else None)
    if not rows:
        messagebox.showinfo("No Data", "No customers/trucks found for export.")
        return

    header = [
        "Customer ID",
        "Customer Name",
        "Phone",
        "Company",
        "Truck ID",
        "Plate",
        "State",
        "Make",
        "Model",
    ]
    data = [
        [
            row["customer_id"],
            row["customer_name"] or "",
            row["phone"] or "",
            row["company"] or "",
            row["truck_id"] or "",
            row["plate"] or "",
            row["state"] or "",
            row["make"] or "",
            row["model"] or "",
        ]
        for row in rows
    ]

    try:
        if openpyxl_module is not None:
            workbook = openpyxl_module.Workbook()
            worksheet = workbook.active
            worksheet.title = "Customers & Trucks"
            worksheet.append(header)
            for data_row in data:
                worksheet.append(data_row)
            for col_cells in worksheet.columns:
                length = max((len(str(cell.value or "")) for cell in col_cells), default=10)
                worksheet.column_dimensions[col_cells[0].column_letter].width = min(length + 4, 50)
            workbook.save(file_path)
        else:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as file_handle:
                writer = csv.writer(file_handle, delimiter="\t")
                writer.writerow(header)
                writer.writerows(data)
    except Exception as exc:
        messagebox.showerror("Export Failed", f"Could not export:\n{exc}")
        log_action_cb("EXPORT_CSV_ERROR", f"Failed to export: {exc}")
        return

    export_query = normalize_whitespace(search_query)
    log_action_cb(
        "EXPORT_CSV",
        (
            f"Rows: {len(rows)}, Query: {export_query or '<none>'}, "
            f"Format: {'xlsx' if openpyxl_module is not None else 'csv'}, Path: {file_path}"
        ),
    )
    messagebox.showinfo("Export Complete", f"File saved to:\n{file_path}")


@safe_ui_action("Import from CSV")
def import_customers_trucks_action(
    app: Any,
    db: "DatabaseService",
    openpyxl_module: Any,
    log_action_cb: Callable[[str, str], None],
) -> None:
    """Import customers/trucks/contracts via file picker and preview dialog."""
    filetypes = [
        ("Excel / CSV", "*.xlsx *.csv *.tsv"),
        ("Excel Workbook", "*.xlsx"),
        ("CSV / TSV", "*.csv *.tsv"),
        ("All Files", "*.*"),
    ]
    file_path = filedialog.askopenfilename(
        title="Import Customers & Trucks",
        filetypes=filetypes,
    )
    if not file_path:
        return

    raw_rows: list[dict] = []
    try:
        ext = file_path.rsplit(".", 1)[-1].lower()
        if ext == "xlsx":
            if openpyxl_module is None:
                messagebox.showerror("Missing Dependency", "openpyxl is required to read .xlsx files.")
                return
            wb = openpyxl_module.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
            rows_iter = ws.iter_rows(values_only=True)
            headers_raw = next(rows_iter, None)
            if not headers_raw:
                messagebox.showerror("Empty File", "The workbook has no data.")
                wb.close()
                return
            headers = [str(h).strip().lower() if h else "" for h in headers_raw]
            for row in rows_iter:
                raw_rows.append({headers[i]: (str(row[i]).strip() if row[i] is not None else "") for i in range(len(headers))})
            wb.close()
        else:
            with open(file_path, newline="", encoding="utf-8-sig") as f:
                sample = f.read(4096)
            delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
            with open(file_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                for row in reader:
                    raw_rows.append({k.strip().lower(): (v.strip() if v else "") for k, v in row.items()})
    except Exception as exc:
        messagebox.showerror("Read Error", f"Could not read file:\n{exc}")
        return

    if not raw_rows:
        messagebox.showinfo("Empty File", "No data rows found in the file.")
        return

    aliases: dict[str, list[str]] = {
        "name": ["customer name", "name", "customer", "姓名", "客户名"],
        "phone": ["phone", "tel", "telephone", "电话"],
        "company": ["company", "company name", "公司"],
        "plate": ["plate", "license plate", "plate number", "车牌"],
        "state": ["state", "st", "州"],
        "make": ["make", "brand", "品牌"],
        "model": ["model", "型号"],
        "monthly_rate": ["monthly rate", "rate", "monthly_rate", "月费", "费率", "$/mo"],
        "start_date": [
            "start date",
            "start",
            "start_date",
            "contract start",
            "开始日期",
            "开始",
            "contract start date",
        ],
    }
    available = set(raw_rows[0].keys())

    def _find_col(field: str) -> str | None:
        for alias in aliases[field]:
            if alias in available:
                return alias
        return None

    col_name = _find_col("name")
    col_phone = _find_col("phone")
    col_company = _find_col("company")
    col_plate = _find_col("plate")
    col_state = _find_col("state")
    col_make = _find_col("make")
    col_model = _find_col("model")
    col_rate = _find_col("monthly_rate")
    col_start = _find_col("start_date")

    if not col_name:
        messagebox.showerror(
            "Missing Column",
            "Could not find a 'Customer Name' column.\n"
            f"Columns found: {', '.join(sorted(available))}",
        )
        return

    existing_names = {
        normalize_whitespace(name_value).lower()
        for name_value in db.get_all_customer_names()
        if normalize_whitespace(name_value)
    }
    existing_plates: set[str] = set()
    for plate_value in db.get_all_truck_plates():
        if not normalize_whitespace(plate_value):
            continue
        try:
            existing_plates.add(required_plate(plate_value))
        except ValueError:
            existing_plates.add(normalize_whitespace(plate_value).upper())

    seen_import_names: dict[str, dict] = {}
    truck_entries: list[dict] = []
    invalid_rows: list[str] = []

    for index, row in enumerate(raw_rows, start=2):
        raw_name = row.get(col_name, "")
        if not normalize_whitespace(raw_name):
            continue

        try:
            customer_name = required_text("Customer Name", raw_name, max_len=80)
            phone = optional_phone(row.get(col_phone, "") if col_phone else "")
            company = optional_text("Company", row.get(col_company, "") if col_company else "", max_len=80)
        except ValueError as exc:
            invalid_rows.append(f"Row {index}: {exc}")
            continue

        key = customer_name.lower()
        if key not in seen_import_names:
            seen_import_names[key] = {
                "name": customer_name,
                "phone": phone,
                "company": company,
            }

        plate = ""
        if col_plate:
            try:
                raw_plate = row.get(col_plate, "")
                plate = required_plate(raw_plate) if normalize_whitespace(raw_plate) else ""
            except ValueError as exc:
                invalid_rows.append(f"Row {index}: {exc}")
                continue

        if plate:
            try:
                state = optional_state(row.get(col_state, "") if col_state else "")
                make = optional_text("Make", row.get(col_make, "") if col_make else "", max_len=40)
                model = optional_text("Model", row.get(col_model, "") if col_model else "", max_len=40)
            except ValueError as exc:
                invalid_rows.append(f"Row {index}: {exc}")
                continue

            rate_raw = row.get(col_rate, "") if col_rate else ""
            rate_val = None
            if normalize_whitespace(rate_raw):
                try:
                    rate_val = positive_float("Monthly Rate", rate_raw)
                except ValueError as exc:
                    invalid_rows.append(f"Row {index}: {exc}")
                    continue

            start_raw = row.get(col_start, "") if col_start else ""
            start_date_str = today().isoformat()
            if start_raw:
                start_clean = normalize_whitespace(start_raw)
                parsed_start = parse_ymd(start_clean)
                if not parsed_start:
                    parsed_ym = parse_ym(start_clean)
                    if parsed_ym:
                        parsed_start = date(parsed_ym[0], parsed_ym[1], 1)
                if not parsed_start:
                    invalid_rows.append(f"Row {index}: Start Date must be YYYY-MM-DD or YYYY-MM.")
                    continue
                start_date_str = parsed_start.isoformat()

            truck_entries.append(
                {
                    "customer_name": customer_name,
                    "plate": plate,
                    "state": state,
                    "make": make,
                    "model": model,
                    "rate": rate_val,
                    "start_date": start_date_str,
                }
            )

    if not seen_import_names and not truck_entries:
        details = "\n".join(invalid_rows[:6])
        messagebox.showerror("Import Error", "No valid rows found in file." + (f"\n\n{details}" if details else ""))
        return

    new_customers = [value for key, value in seen_import_names.items() if key not in existing_names]
    skip_customers = [value for key, value in seen_import_names.items() if key in existing_names]
    new_trucks = [truck for truck in truck_entries if truck["plate"] not in existing_plates]
    skip_trucks = [truck for truck in truck_entries if truck["plate"] in existing_plates]
    new_contracts = [truck for truck in new_trucks if truck["rate"] is not None]

    def _do_import() -> bool:
        now_str = datetime.now().isoformat(sep=" ", timespec="seconds")
        name_to_id: dict[str, int] = {
            row["name"].strip().lower(): int(row["id"])
            for row in db.get_all_customer_id_name_rows()
        }
        for customer in new_customers:
            customer_id = db.create_customer(
                customer["name"],
                customer["phone"] or None,
                customer["company"] or None,
                None,
                now_str,
            )
            name_to_id[customer["name"].lower()] = customer_id

        plate_to_info: dict[str, dict] = {}
        for truck in new_trucks:
            customer_id = name_to_id.get(truck["customer_name"].lower())
            truck_id = db.create_truck(
                customer_id,
                truck["plate"],
                truck["state"] or None,
                truck["make"] or None,
                truck["model"] or None,
                None,
                now_str,
            )
            plate_to_info[truck["plate"]] = {
                "truck_id": truck_id,
                "customer_id": customer_id,
                "rate": truck["rate"],
                "start_date": truck["start_date"],
            }

        contracts_created = 0
        for truck in new_contracts:
            info = plate_to_info.get(truck["plate"])
            if not info:
                continue
            start_date = info["start_date"]
            start_ym = start_date[:7] if start_date else today().isoformat()[:7]
            db.create_contract(
                info["customer_id"],
                info["truck_id"],
                info["rate"],
                start_ym,
                None,
                start_date,
                None,
                1,
                None,
                now_str,
            )
            contracts_created += 1

        db.commit()
        app.refresh_customers()
        app.refresh_trucks()
        app.refresh_contracts()
        app.refresh_invoices()
        app.refresh_overdue()
        app.refresh_statement()
        app.refresh_dashboard()
        app._reload_customer_dropdowns()
        app._reload_truck_dropdowns()
        log_action_cb(
            "IMPORT_CSV",
            (
                f"File: {file_path}, Imported Customers: {len(new_customers)}, Imported Trucks: {len(new_trucks)}, "
                f"Imported Contracts: {contracts_created}, Skipped Customers: {len(skip_customers)}, "
                f"Skipped Trucks: {len(skip_trucks)}, Invalid Rows: {len(invalid_rows)}"
            ),
        )
        log_ux_action(
            "Import CSV",
            f"{len(new_customers)} customers, {len(new_trucks)} trucks, {contracts_created} contracts",
            user_context=f"file={file_path}",
        )
        messagebox.showinfo(
            "Import Complete",
            f"Imported {len(new_customers)} customer(s), {len(new_trucks)} truck(s), "
            f"{contracts_created} contract(s).\n"
            f"Skipped {len(skip_customers)} duplicate customer(s) and "
            f"{len(skip_trucks)} duplicate truck(s)."
            + (f"\nIgnored {len(invalid_rows)} invalid row(s)." if invalid_rows else ""),
        )

        if invalid_rows:
            logger.warning("Import ignored invalid rows: %s", " | ".join(invalid_rows[:20]))

        return True

    show_import_preview(
        parent=app,
        file_path=file_path,
        new_customers=new_customers,
        skip_customers=skip_customers,
        new_trucks=new_trucks,
        skip_trucks=skip_trucks,
        new_contracts=new_contracts,
        invalid_rows=invalid_rows,
        on_confirm=_do_import,
    )


@safe_ui_action("Open Payment Form")
def open_payment_form_for_contract_action(
    app: Any,
    db: "DatabaseService",
    contract_id: int,
    plate_label: str | None,
    as_of_date: date | None,
    get_contract_outstanding_as_of_cb: Callable[[int, date], float],
    get_or_create_anchor_invoice_cb: Callable[[int, date], int],
    log_action_cb: Callable[[str, str], None],
) -> None:
    as_of = as_of_date or today()

    if not db.contract_exists(contract_id):
        messagebox.showerror("Not found", "Contract not found.")
        return

    balance = get_contract_outstanding_as_of_cb(contract_id, as_of)

    def on_submit(amt_str: str, paid_at: str, method: str, ref: str, notes: str) -> bool:
        try:
            amt = positive_float("Amount", amt_str)
            paid_at_clean = required_text("Payment Date", paid_at, max_len=20)
            ref_val = optional_text("Reference", ref, max_len=60)
            notes_val = optional_text("Notes", notes, max_len=300)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return False

        if method not in {"cash", "card", "zelle", "venmo", "other"}:
            messagebox.showerror("Invalid method", "Payment method is invalid.")
            return False

        paid_at_date = parse_ymd(paid_at_clean)
        if not paid_at_date:
            messagebox.showerror("Date format error", "Payment date format must be YYYY-MM-DD.")
            return False

        outstanding = get_contract_outstanding_as_of_cb(contract_id, as_of)
        if outstanding <= 0.01:
            messagebox.showerror("No balance", "No outstanding balance for this contract at the selected as-of date.")
            return False

        max_allowed = outstanding * 12.0
        if amt > max_allowed:
            messagebox.showerror(
                "Amount too large",
                f"Amount exceeds allowed limit. Outstanding: ${outstanding:.2f}; max allowed (12x): ${max_allowed:.2f}.",
            )
            return False

        invoice_id = get_or_create_anchor_invoice_cb(contract_id, as_of)
        db.create_payment(invoice_id, paid_at_date.isoformat(), amt, method, ref_val, notes_val)
        db.commit()
        customer_name = db.get_customer_name_by_contract(contract_id) or ""
        log_ux_action(
            "Record Payment",
            f"${amt:.2f} via {method} for contract {contract_id}",
            user_context=f"customer={customer_name}",
        )
        log_action_cb(
            "RECORD_PAYMENT",
            (
                f"Contract ID: {contract_id}, Invoice ID: {invoice_id}, Customer: {customer_name}, "
                f"Amount: ${amt:.2f}, Paid At: {paid_at_date.isoformat()}, As-Of: {as_of.isoformat()}, "
                f"Method: {method}, Reference: {ref_val}, Notes: {notes_val or ''}"
            ),
        )

        app.refresh_customers()
        app.refresh_contracts()
        app.refresh_trucks()
        app.refresh_invoices()
        app.refresh_statement()
        app.refresh_overdue()
        app.refresh_dashboard()
        app.refresh_histories()
        messagebox.showinfo("✓ Saved", f"Payment of ${amt:.2f} has been recorded.")
        return True

    show_payment_popup(
        app,
        contract_id,
        plate_label,
        balance,
        today().isoformat(),
        on_submit,
        date_input_factory=lambda parent, width, default_iso=None: create_date_input(
            parent,
            width,
            default_iso=default_iso,
            date_entry_cls=getattr(app, "date_entry_cls", None),
        ),
    )


@safe_ui_action("Delete Contract")
def delete_contract_action(
    app: Any,
    db: "DatabaseService",
    log_action_cb: Callable[[str, str], None],
) -> None:
    sel = app.contract_tree.selection()
    if not sel:
        messagebox.showwarning("Select a row", "Select a contract row first.")
        return

    values = app.contract_tree.item(sel[0], "values")
    if not values:
        messagebox.showerror("Invalid selection", "Could not read selected contract.")
        return

    contract_id = int(values[0])
    customer = values[2]
    scope = values[3]

    invoice_count = db.count_invoices_for_contract(contract_id)
    payment_count = db.get_payment_count_by_contract(contract_id)

    ok = messagebox.askyesno(
        "Confirm Delete",
        (
            f"Delete contract ID {contract_id}?\n\n"
            f"  • Customer: {customer}\n"
            f"  • Scope: {scope}\n"
            f"  • Invoices: {invoice_count} (will be deleted)\n"
            f"  • Payments: {payment_count} (will be deleted)\n\n"
            f"This action cannot be undone."
        ),
    )
    if not ok:
        return

    final_confirm = messagebox.askyesno(
        "⚠️ Final Confirmation",
        f"Are you ABSOLUTELY SURE you want to delete contract #{contract_id}?\n\n"
        f"Customer: {customer}\n"
        f"This will permanently delete {invoice_count} invoices and {payment_count} payments.\n\n"
        f"THIS CANNOT BE UNDONE.",
        icon="warning",
    )
    if not final_confirm:
        messagebox.showinfo("Cancelled", "Delete operation was cancelled.")
        return

    db.delete_contract(contract_id)
    db.commit()
    log_ux_action("Delete Contract", f"Contract #{contract_id} for {customer}")
    log_action_cb(
        "DELETE_CONTRACT",
        f"Contract ID: {contract_id}, Customer: {customer}, Scope: {scope}, Deleted Invoices: {invoice_count}, Deleted Payments: {payment_count}",
    )

    app.refresh_customers()
    app.refresh_trucks()
    app.refresh_contracts()
    app.refresh_invoices()
    app.refresh_overdue()
    app.refresh_statement()
    app.refresh_dashboard()
    messagebox.showinfo("✓ Deleted", f"Contract {contract_id} has been deleted.")


@safe_ui_action("Delete Customer")
def delete_customer_action(
    app: Any,
    db: "DatabaseService",
    log_action_cb: Callable[[str, str], None],
) -> None:
    sel = app.customer_tree.selection()
    if not sel:
        messagebox.showwarning("Select a row", "Select a customer row first.")
        return

    values = app.customer_tree.item(sel[0], "values")
    if not values:
        messagebox.showerror("Invalid selection", "Could not read selected customer.")
        return

    customer_id = int(values[0])
    customer_name = values[1]

    contract_count = db.count_contracts_for_customer(customer_id)
    truck_count = db.count_trucks_for_customer(customer_id)

    ok = messagebox.askyesno(
        "Confirm delete",
        (
            f"Delete customer '{customer_name}' (ID {customer_id})?\n\n"
            f"Related contracts to be deleted: {contract_count}\n"
            "(Related invoices and payments will also be deleted.)\n"
            f"Related trucks to be unassigned: {truck_count}"
        ),
    )
    if not ok:
        return

    final_confirm = messagebox.askyesno(
        "⚠️ Final Confirmation",
        f"Are you ABSOLUTELY SURE you want to delete '{customer_name}'?\n\n"
        f"This will permanently delete {contract_count} contracts "
        f"(and their invoices/payments).\n"
        f"{truck_count} truck(s) will be unassigned (not deleted).\n\n"
        f"THIS CANNOT BE UNDONE.",
        icon="warning",
    )
    if not final_confirm:
        messagebox.showinfo("Cancelled", "Delete operation was cancelled.")
        return

    db.delete_customer(customer_id)
    db.commit()
    log_ux_action("Delete Customer", f"ID={customer_id} name='{customer_name}'")
    log_action_cb(
        "DELETE_CUSTOMER",
        f"Customer ID: {customer_id}, Name: {customer_name}, Related Contracts: {contract_count}, Unassigned Trucks: {truck_count}",
    )

    app.refresh_customers()
    app.refresh_trucks()
    app.refresh_contracts()
    app.refresh_invoices()
    app.refresh_overdue()
    app.refresh_statement()
    app.refresh_dashboard()
    messagebox.showinfo("Deleted", f"Customer '{customer_name}' deleted.")


@safe_ui_action("Edit Customer")
def edit_selected_customer_action(
    app: Any,
    db: "DatabaseService",
    log_action_cb: Callable[[str, str], None],
) -> None:
    sel = app.customer_tree.selection()
    if not sel:
        messagebox.showwarning("No Selection", "Select a customer row first.")
        return

    values = app.customer_tree.item(sel[0], "values")
    if not values or len(values) < 7:
        messagebox.showerror("Invalid selection", "Could not read selected customer.")
        return

    customer_id = int(values[0])
    original_name = str(values[1])
    original_phone = str(values[2]).strip()
    original_company = str(values[3]).strip()
    original_notes = str(values[4]).strip()

    win = tk.Toplevel(app)
    win.title(f"Edit Customer #{customer_id}")
    win.geometry("1080x440")
    win.minsize(980, 400)
    win.transient(app)
    win.grab_set()

    frm = ttk.Frame(win, padding=12)
    frm.pack(fill="both", expand=True)
    frm.columnconfigure(1, weight=1)

    ttk.Label(frm, text="Name*").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=8)
    name_entry = ttk.Entry(frm)
    name_entry.grid(row=0, column=1, sticky="ew", pady=8)
    name_entry.insert(0, original_name)

    ttk.Label(frm, text="Phone").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=8)
    phone_entry = ttk.Entry(frm)
    phone_entry.grid(row=1, column=1, sticky="ew", pady=8)
    phone_entry.insert(0, original_phone)

    ttk.Label(frm, text="Company").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=8)
    company_entry = ttk.Entry(frm)
    company_entry.grid(row=2, column=1, sticky="ew", pady=8)
    company_entry.insert(0, original_company)

    ttk.Label(frm, text="Notes").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=8)
    notes_entry = ttk.Entry(frm)
    notes_entry.grid(row=3, column=1, sticky="ew", pady=8)
    notes_entry.insert(0, original_notes)

    btns = ttk.Frame(frm)
    btns.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 0))
    btns.columnconfigure(0, weight=1)
    btns.columnconfigure(1, weight=1)

    def _save_customer() -> None:
        try:
            new_name = required_text("Name", name_entry.get(), max_len=80)
            new_phone = optional_phone(phone_entry.get())
            new_company = optional_text("Company", company_entry.get(), max_len=80)
            new_notes = optional_text("Notes", notes_entry.get(), max_len=300)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        db.update_customer(customer_id, new_name, new_phone, new_company, new_notes)
        db.commit()
        log_ux_action("Edit Customer", f"ID={customer_id} name='{new_name}'")
        log_action_cb(
            "EDIT_CUSTOMER",
            (
                f"Customer ID: {customer_id}, "
                f"Old Name: {original_name}, New Name: {new_name}, "
                f"Old Phone: {original_phone}, New Phone: {new_phone or ''}, "
                f"Old Company: {original_company}, New Company: {new_company or ''}, "
                f"Old Notes: {original_notes}, New Notes: {new_notes or ''}"
            ),
        )

        app.refresh_customers()
        app.refresh_trucks()
        app.refresh_contracts()
        app.refresh_invoices()
        app.refresh_overdue()
        app.refresh_statement()
        app.refresh_dashboard()
        win.destroy()
        messagebox.showinfo("Saved", f"Customer '{new_name}' has been updated.")

    ttk.Button(btns, text="Save Changes", command=_save_customer).grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=4)
    ttk.Button(btns, text="Cancel", command=win.destroy).grid(row=0, column=1, sticky="ew", padx=(6, 0), ipady=4)

    name_entry.focus_set()


@safe_ui_action("Delete Truck")
def delete_truck_action(
    app: Any,
    db: "DatabaseService",
    log_action_cb: Callable[[str, str], None],
) -> None:
    sel = app.truck_tree.selection()
    if not sel:
        messagebox.showwarning("Select a row", "Select a truck row first.")
        return

    values = app.truck_tree.item(sel[0], "values")
    if not values:
        messagebox.showerror("Invalid selection", "Could not read selected truck.")
        return

    truck_id = int(values[0])
    plate = values[1]

    contract_count = db.count_contracts_for_truck(truck_id)

    ok = messagebox.askyesno(
        "Confirm Delete",
        (
            f"Delete truck '{plate}'?\n\n"
            f"  • Related contracts: {contract_count} (will be deleted)\n"
            f"    (Related invoices and payments will also be deleted.)\n\n"
            f"This action cannot be undone."
        ),
    )
    if not ok:
        return

    final_confirm = messagebox.askyesno(
        "⚠️ Final Confirmation",
        f"Are you ABSOLUTELY SURE you want to delete truck '{plate}'?\n\n"
        f"This will permanently delete {contract_count} contracts and related billing history.\n\n"
        f"THIS CANNOT BE UNDONE.",
        icon="warning",
    )
    if not final_confirm:
        messagebox.showinfo("Cancelled", "Delete operation was cancelled.")
        return

    db.delete_truck(truck_id)
    db.commit()
    log_action_cb("DELETE_TRUCK", f"Truck ID: {truck_id}, Plate: {plate}, Related Contracts: {contract_count}")

    app._refresh_affected_tabs_after_truck_change()
    messagebox.showinfo("✓ Deleted", f"Truck '{plate}' has been deleted.")


@safe_ui_action("Toggle Contract Status")
def toggle_contract_action(
    app: Any,
    db: "DatabaseService",
) -> None:
    sel = app.contract_tree.selection()
    if not sel:
        messagebox.showwarning("Select a row", "Select a contract row first.")
        return

    values = app.contract_tree.item(sel[0], "values")
    if not values:
        messagebox.showerror("Invalid selection", "Could not read selected contract.")
        return
    contract_id = int(values[0])

    row = db.get_contract_active_row(contract_id)
    if not row:
        messagebox.showerror("Not found", "Contract not found in DB.")
        return

    new_val = 0 if row["is_active"] else 1
    db.set_contract_active(contract_id, new_val)
    db.commit()
    status_label = "ACTIVE" if new_val else "INACTIVE"
    log_ux_action("Toggle Contract", f"Contract {contract_id} set to {status_label}")
    app.refresh_customers()
    app.refresh_trucks()
    app.refresh_contracts()
    app.refresh_invoices()
    app.refresh_overdue()
    app.refresh_statement()
    app.refresh_dashboard()


@safe_ui_action("Record Payment for Contract")
def record_payment_for_selected_contract_action(
    app: Any,
    open_payment_form_for_contract_cb: Callable[[int], None],
) -> None:
    sel = app.contract_tree.selection()
    if not sel:
        messagebox.showwarning("No Selection", "Select a contract row first.")
        return

    values = app.contract_tree.item(sel[0], "values")
    if not values:
        messagebox.showerror("Invalid selection", "Could not read selected contract.")
        return

    try:
        contract_id = int(values[0])
    except (ValueError, TypeError):
        messagebox.showerror("Invalid selection", "Selected contract ID is invalid.")
        return

    open_payment_form_for_contract_cb(contract_id)


@safe_ui_action("Record Payment for Truck")
def record_payment_for_selected_truck_action(
    app: Any,
    db: "DatabaseService",
    open_payment_form_for_contract_cb: Callable[[int, str | None, date | None], None],
) -> None:
    sel = app.truck_tree.selection()
    if not sel:
        messagebox.showwarning("No Selection", "Select a truck row first.")
        return

    values = app.truck_tree.item(sel[0], "values")
    if not values:
        messagebox.showerror("Invalid selection", "Could not read selected truck.")
        return

    try:
        truck_id = int(values[0])
    except (ValueError, TypeError):
        messagebox.showerror("Invalid selection", "Selected truck ID is invalid.")
        return

    contract_row = db.get_preferred_contract_for_truck(truck_id)
    if not contract_row:
        messagebox.showinfo("No Contract", "No contract was found for this truck.")
        return

    contract_id = int(contract_row["contract_id"])
    plate_label = str(values[1]).strip() if len(values) > 1 else ""
    if not plate_label:
        plate_from_contract = contract_row["plate"] if "plate" in contract_row.keys() else None
        plate_label = str(plate_from_contract or "").strip()
    open_payment_form_for_contract_cb(contract_id, plate_label or None, None)


@safe_ui_action("Edit Contract")
def edit_contract_action(
    app: Any,
    db: "DatabaseService",
    get_selected_customer_id_cb: Callable[[Any], int | None],
    get_selected_truck_id_cb: Callable[[Any], int | None],
    show_invalid_cb: Callable[[str], None],
    log_action_cb: Callable[[str, str], None],
) -> None:
    sel = app.contract_tree.selection()
    if not sel:
        messagebox.showwarning("Select a row", "Select a contract row first.")
        return

    values = app.contract_tree.item(sel[0], "values")
    if not values:
        messagebox.showerror("Invalid selection", "Could not read selected contract.")
        return

    contract_id = int(values[0])
    row = db.get_contract_for_edit(contract_id)
    if not row:
        messagebox.showerror("Not found", "Contract not found in DB.")
        return

    app._reload_customer_dropdowns()
    app._reload_truck_dropdowns()
    customer_values = list(app.contract_customer_combo["values"]) if hasattr(app, "contract_customer_combo") else []
    truck_values = list(app.contract_truck_combo["values"]) if hasattr(app, "contract_truck_combo") else []

    def _save_contract(customer_combo, truck_combo, scope, rate_str, start_str, end_str, notes_str, is_active):
        customer_id = get_selected_customer_id_cb(customer_combo)
        if not customer_id:
            messagebox.showerror("Missing field", "Customer is required.")
            return False

        truck_id = None
        if scope == "per_truck":
            truck_id = get_selected_truck_id_cb(truck_combo)
            if not truck_id:
                messagebox.showerror("Missing field", "Pick a truck (or switch to customer-level contract).")
                return False

        try:
            rate = positive_float("Rate", rate_str)
            notes = optional_text("Notes", notes_str, max_len=300)
        except ValueError as exc:
            show_invalid_cb(str(exc))
            return False

        start = start_str or today().isoformat()
        end = end_str or None
        parsed_start = parse_ymd(start)
        if not parsed_start:
            messagebox.showerror("Date format error", "Start date format must be YYYY-MM-DD.")
            return False

        parsed_end = None
        if end:
            parsed_end = parse_ymd(end)
            if not parsed_end:
                messagebox.showerror("Date format error", "End date format must be YYYY-MM-DD.")
                return False
            if parsed_end < parsed_start:
                messagebox.showerror("Date range error", "End date cannot be earlier than start date.")
                return False

        start_ym_val = parsed_start.strftime("%Y-%m")
        end_ym_val = parsed_end.strftime("%Y-%m") if parsed_end else None

        db.update_contract(
            contract_id,
            customer_id,
            truck_id,
            rate,
            start_ym_val,
            end_ym_val,
            parsed_start.isoformat(),
            parsed_end.isoformat() if parsed_end else None,
            1 if is_active else 0,
            notes,
        )
        db.commit()
        log_action_cb(
            "EDIT_CONTRACT",
            (
                f"Contract ID: {contract_id}, Customer ID: {customer_id}, Truck ID: {truck_id}, "
                f"Scope: {scope}, Rate: ${rate:.2f}, Start: {parsed_start.isoformat()}, "
                f"End: {parsed_end.isoformat() if parsed_end else 'None'}, "
                f"Active: {1 if is_active else 0}, Notes: {notes or ''}"
            ),
        )

        app.refresh_customers()
        app.refresh_trucks()
        app.refresh_contracts()
        app.refresh_invoices()
        app.refresh_overdue()
        app.refresh_statement()
        app.refresh_dashboard()
        messagebox.showinfo("✓ Updated", "Contract has been updated.")
        return True

    open_contract_edit_dialog(
        parent=app,
        contract_id=contract_id,
        row=row,
        customer_values=customer_values,
        truck_values=truck_values,
        date_input_factory=lambda parent, width, default_iso=None: create_date_input(
            parent,
            width,
            default_iso=default_iso,
            date_entry_cls=getattr(app, "date_entry_cls", None),
        ),
        make_searchable_combo=app._make_searchable_combo,
        on_save=_save_contract,
        optional_date_clear_on_blur_cb=lambda widget: make_optional_date_clear_on_blur(
            widget,
            date_entry_cls=getattr(app, "date_entry_cls", None),
        ),
    )


@safe_ui_action("Show Payment History")
def show_contract_payment_history_action(
    app: Any,
    db: "DatabaseService",
    get_contract_outstanding_as_of_cb: Callable[[int, date], float],
    show_contract_payment_history_dialog_cb: Callable[[Any, dict, list], None],
) -> None:
    current_tab = app.main_notebook.tab(app.main_notebook.select(), "text")

    if "Billing" in current_tab:
        sel = app.invoice_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a contract row first.")
            return
        values = app.invoice_tree.item(sel[0], "values")
        if not values:
            return

        try:
            contract_id = int(str(values[0]).strip())
        except (ValueError, TypeError):
            messagebox.showinfo("Parent row", "Please select a contract (not a customer).")
            return

        status = values[10]
        customer = values[1]
        if not str(customer).strip():
            customer = db.get_customer_name_by_contract(contract_id) or ""
        scope = values[2]
        rate = values[3]
        start = values[4]
        end = values[5] or "—"
    else:
        sel = app.contract_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a contract row first.")
            return
        values = app.contract_tree.item(sel[0], "values")
        if not values:
            return

        contract_id = int(values[0])
        status = values[1]
        customer = values[2]
        scope = values[3]
        rate = values[4]
        start = values[5]
        end = values[6] or "—"

    rows = db.get_contract_payment_history(contract_id)
    contract_info = {
        "contract_id": contract_id,
        "status": status,
        "customer": customer,
        "scope": scope,
        "rate": rate,
        "start": start,
        "end": end,
        "outstanding": f"${get_contract_outstanding_as_of_cb(contract_id, today()):.2f}",
    }
    show_contract_payment_history_dialog_cb(app, contract_info, rows)


@safe_ui_action("Create Contract")
def create_contract_action(
    app: Any,
    db: "DatabaseService",
    get_selected_customer_id_cb: Callable[[Any], int | None],
    get_selected_truck_id_cb: Callable[[Any], int | None],
    get_entry_value_cb: Callable[[Any], str],
    clear_inline_errors_cb: Callable[[Any], None],
    show_inline_error_cb: Callable[[Any, str, int, int], Any],
    show_invalid_cb: Callable[[str], None],
    log_action_cb: Callable[[str, str], None],
) -> None:
    if hasattr(app, "_contract_form"):
        clear_inline_errors_cb(app._contract_form)

    customer_id = get_selected_customer_id_cb(app.contract_customer_combo)
    if not customer_id:
        messagebox.showerror("Missing field", "Customer is required.")
        if hasattr(app, "_contract_form"):
            show_inline_error_cb(app._contract_form, "Customer is required", row=3, column=0, columnspan=4)
        return

    scope = app.contract_scope.get()
    truck_id = None
    if scope == "per_truck":
        truck_id = get_selected_truck_id_cb(app.contract_truck_combo)
        if not truck_id:
            messagebox.showerror("Missing field", "Pick a truck (or switch to customer-level contract).")
            if hasattr(app, "_contract_form"):
                show_inline_error_cb(app._contract_form, "Truck is required for per-truck contracts", row=3, column=0, columnspan=4)
            return

    try:
        rate = positive_float("Rate", get_entry_value_cb(app.contract_rate))
        notes = optional_text("Notes", app.contract_notes.get(), max_len=300)
    except ValueError as exc:
        show_invalid_cb(str(exc))
        if hasattr(app, "_contract_form"):
            show_inline_error_cb(app._contract_form, str(exc), row=3, column=0, columnspan=9)
        return

    start = app.contract_start.get().strip() or today().isoformat()
    end = app.contract_end.get().strip() or None
    parsed_start = parse_ymd(start)
    if not parsed_start:
        messagebox.showerror("Date format error", "Start date format must be YYYY-MM-DD.")
        if hasattr(app, "_contract_form"):
            show_inline_error_cb(app._contract_form, "Start date format must be YYYY-MM-DD", row=3, column=5, columnspan=4)
        return

    parsed_end = None
    if end:
        parsed_end = parse_ymd(end)
        if not parsed_end:
            messagebox.showerror("Date format error", "End date format must be YYYY-MM-DD.")
            if hasattr(app, "_contract_form"):
                show_inline_error_cb(app._contract_form, "End date format must be YYYY-MM-DD", row=3, column=7, columnspan=3)
            return
        if parsed_end < parsed_start:
            messagebox.showerror("Date range error", "End date cannot be earlier than start date.")
            if hasattr(app, "_contract_form"):
                show_inline_error_cb(app._contract_form, "End date cannot be earlier than start date", row=3, column=7, columnspan=3)
            return

    start_ym_val = parsed_start.strftime("%Y-%m")
    end_ym_val = parsed_end.strftime("%Y-%m") if parsed_end else None
    db.create_contract(
        customer_id,
        truck_id,
        rate,
        start_ym_val,
        end_ym_val,
        parsed_start.isoformat(),
        parsed_end.isoformat() if parsed_end else None,
        1,
        notes,
        now_iso(),
    )
    db.commit()
    log_ux_action(
        "Create Contract",
        f"Customer {customer_id}, rate=${rate:.2f}, start={parsed_start.isoformat()}",
    )
    log_action_cb(
        "CREATE_CONTRACT",
        (
            f"Customer ID: {customer_id}, Truck ID: {truck_id}, Scope: {scope}, Rate: ${rate:.2f}, "
            f"Start: {parsed_start.isoformat()}, End: {parsed_end.isoformat() if parsed_end else 'None'}, "
            f"Notes: {notes or ''}"
        ),
    )

    app.contract_rate.delete(0, tk.END)
    app.contract_end.delete(0, tk.END)
    app.contract_notes.delete(0, tk.END)
    app.contract_rate.focus()

    app.refresh_customers()
    app.refresh_trucks()
    app.refresh_contracts()
    app.refresh_invoices()
    app.refresh_overdue()
    app.refresh_statement()
    app.refresh_dashboard()
    messagebox.showinfo("✓ Saved", f"Contract created for ${rate:.2f}/month starting {parsed_start}.")


@safe_ui_action("Add Customer")
def add_customer_action(
    app: Any,
    db: "DatabaseService",
    get_entry_value_cb: Callable[[Any], str],
    clear_inline_errors_cb: Callable[[Any], None],
    show_inline_error_cb: Callable[[Any, str, int, int], Any],
    show_invalid_cb: Callable[[str], None],
    add_placeholder_cb: Callable[[Any, str], None],
    log_action_cb: Callable[[str, str], None],
) -> None:
    if hasattr(app, "_customer_form"):
        clear_inline_errors_cb(app._customer_form)

    try:
        name = required_text("Name", get_entry_value_cb(app.c_name), max_len=80)
        phone = optional_phone(get_entry_value_cb(app.c_phone))
        company = optional_text("Company", get_entry_value_cb(app.c_company), max_len=80)
        notes = optional_text("Notes", get_entry_value_cb(app.c_notes), max_len=300)
    except ValueError as exc:
        show_invalid_cb(str(exc))
        if hasattr(app, "_customer_form"):
            show_inline_error_cb(app._customer_form, str(exc), row=2, column=0, columnspan=6)
        app.c_name.focus()
        return

    customer_id = db.create_customer(name, phone, company, notes, now_iso())
    db.commit()
    log_ux_action("Add Customer", f"ID={customer_id} name='{name}'")
    log_action_cb(
        "ADD_CUSTOMER",
        f"Customer ID: {customer_id}, Name: {name}, Phone: {phone or ''}, Company: {company or ''}, Notes: {notes or ''}",
    )

    app.c_name.delete(0, tk.END)
    app.c_phone.delete(0, tk.END)
    app.c_company.delete(0, tk.END)
    app.c_notes.delete(0, tk.END)
    add_placeholder_cb(app.c_name, "Enter customer name...")
    add_placeholder_cb(app.c_phone, "Phone number...")
    add_placeholder_cb(app.c_company, "Company name...")
    add_placeholder_cb(app.c_notes, "Additional notes...")
    app.c_name.focus()

    app.refresh_customers()
    app.refresh_trucks()
    app.refresh_contracts()
    app.refresh_invoices()
    app.refresh_overdue()
    app.refresh_statement()
    app.refresh_dashboard()
    messagebox.showinfo("✓ Saved", f"Customer '{name}' has been added.")


@safe_ui_action("Add Truck")
def add_truck_action(
    app: Any,
    db: "DatabaseService",
    get_entry_value_cb: Callable[[Any], str],
    get_selected_customer_id_cb: Callable[[Any], int | None],
    clear_inline_errors_cb: Callable[[Any], None],
    show_inline_error_cb: Callable[[Any, str, int, int], Any],
    show_invalid_cb: Callable[[str], None],
    add_placeholder_cb: Callable[[Any, str], None],
    log_action_cb: Callable[[str, str], None],
) -> None:
    if hasattr(app, "_truck_form"):
        clear_inline_errors_cb(app._truck_form)

    customer_id = get_selected_customer_id_cb(app.truck_customer_combo)

    try:
        plate = required_plate(get_entry_value_cb(app.t_plate))
        state = optional_state(get_entry_value_cb(app.t_state))
        make = optional_text("Make", get_entry_value_cb(app.t_make), max_len=40)
        model = optional_text("Model", get_entry_value_cb(app.t_model), max_len=40)
        notes = optional_text("Notes", get_entry_value_cb(app.t_notes), max_len=300)
        contract_rate = None
        contract_start = None
        contract_end = None
        if customer_id is not None:
            contract_rate = positive_float("Contract Cost", get_entry_value_cb(app.t_contract_rate))
            start_raw = get_entry_value_cb(app.t_contract_start).strip()
            end_raw = get_entry_value_cb(app.t_contract_end).strip()

            if start_raw:
                parsed_start = parse_ymd(start_raw)
                if not parsed_start:
                    raise ValueError("Contract Start date format must be YYYY-MM-DD.")
                contract_start = parsed_start.isoformat()
            else:
                contract_start = today().isoformat()

            if end_raw:
                parsed_end = parse_ymd(end_raw)
                if not parsed_end:
                    raise ValueError("Contract End date format must be YYYY-MM-DD.")
                contract_end = parsed_end.isoformat()

            if contract_end is not None and contract_start is not None:
                start_date_obj = parse_ymd(contract_start)
                end_date_obj = parse_ymd(contract_end)
                if start_date_obj and end_date_obj and end_date_obj < start_date_obj:
                    raise ValueError("Contract End date cannot be earlier than Contract Start date.")
    except ValueError as exc:
        show_invalid_cb(str(exc))
        if hasattr(app, "_truck_form"):
            show_inline_error_cb(app._truck_form, str(exc), row=2, column=0, columnspan=10)
        app.t_plate.focus()
        return

    try:
        created_at = now_iso()
        truck_id = db.create_truck(customer_id, plate, state, make, model, notes, created_at)

        contract_id = None
        if customer_id is not None and contract_rate is not None:
            start_date = contract_start or today().isoformat()
            end_date = contract_end
            contract_id = db.create_contract(
                customer_id=customer_id,
                truck_id=truck_id,
                monthly_rate=contract_rate,
                start_ym=start_date[:7],
                end_ym=(end_date[:7] if end_date else None),
                start_date=start_date,
                end_date=end_date,
                is_active=1,
                notes=None,
                created_at=created_at,
            )

        db.commit()
        log_action_cb(
            "ADD_TRUCK",
            (
                f"Truck ID: {truck_id}, Plate: {plate}, Customer ID: {customer_id}, State: {state or ''}, "
                f"Make: {make or ''}, Model: {model or ''}, Notes: {notes or ''}"
            ),
        )
        if contract_id is not None:
            log_action_cb(
                "ADD_CONTRACT",
                (
                    f"Auto-created Contract ID: {contract_id}, Truck ID: {truck_id}, Customer ID: {customer_id}, "
                    f"Rate: ${contract_rate:.2f}, Start: {contract_start or ''}, End: {contract_end or 'None'}"
                ),
            )
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", f"Plate '{plate}' already exists or invalid data.")
        return

    for widget in (app.t_plate, app.t_state, app.t_make, app.t_model, app.t_notes, app.t_contract_rate):
        widget.delete(0, tk.END)

    for widget in (app.t_contract_start, app.t_contract_end):
        try:
            widget.delete(0, tk.END)
        except Exception:
            pass

    add_placeholder_cb(app.t_plate, "License plate...")
    add_placeholder_cb(app.t_state, "CA")
    add_placeholder_cb(app.t_make, "Ford")
    add_placeholder_cb(app.t_model, "F-150")
    add_placeholder_cb(app.t_notes, "Additional notes...")
    add_placeholder_cb(app.t_contract_rate, "Monthly cost...")
    app.t_plate.focus()

    app._refresh_affected_tabs_after_truck_change()
    if customer_id is not None:
        messagebox.showinfo("✓ Saved", f"Truck '{plate}' has been added and a contract was created.")
    else:
        messagebox.showinfo("✓ Saved", f"Truck '{plate}' has been added.")


@safe_ui_action("Refresh Contracts")
def refresh_contracts_action(
    app: Any,
    db: "DatabaseService",
    status_badge_cb: Callable[[str], str],
    row_stripe_tag_cb: Callable[[int], str],
    get_contract_outstanding_as_of_cb: Callable[[int, date], float],
    outstanding_tag_from_amount_cb: Callable[[float], str],
    customer_filter_id: int | None = None,
    refresh_dependents: bool = True,
) -> None:
    query_text = app.contract_search.get().strip().lower() if hasattr(app, "contract_search") else ""
    existing_items = app.contract_tree.get_children()
    if existing_items:
        app.contract_tree.delete(*existing_items)

    rows = db.get_contracts_for_grid(limit=500)
    as_of = today()
    paid_rows = db.get_paid_totals_by_contract_as_of(as_of.isoformat())
    paid_by_contract = {int(row["contract_id"]): float(row["paid_total"]) for row in paid_rows}

    visible_row_index = 0

    for row in rows:
        if customer_filter_id is not None and int(row["customer_id"]) != int(customer_filter_id):
            continue

        status = "ACTIVE" if row["is_active"] else "INACTIVE"
        status_display = status_badge_cb(status)
        scope = row["plate"] if row["plate"] else "(customer-level)"
        customer_name = str(row["customer_name"] or "")
        if query_text and query_text not in customer_name.lower():
            continue

        contract_id = int(row["contract_id"])
        start_date = parse_ymd(str(row["start_date"]))
        end_date = parse_ymd(str(row["end_date"])) if row["end_date"] else None
        if start_date:
            effective_end = min(end_date, as_of) if end_date else as_of
            expected = float(row["monthly_rate"]) * elapsed_months_inclusive(start_date, effective_end)
            outstanding_amt = expected - paid_by_contract.get(contract_id, 0.0)
        else:
            outstanding_amt = 0.0

        app.contract_tree.insert(
            "",
            "end",
            values=(
                contract_id,
                status_display,
                customer_name,
                scope,
                f"${float(row['monthly_rate']):.2f}",
                row["start_date"],
                row["end_date"] or "",
                f"${outstanding_amt:.2f}",
            ),
            tags=(row_stripe_tag_cb(visible_row_index), outstanding_tag_from_amount_cb(outstanding_amt)),
        )
        visible_row_index += 1

    app._reapply_tree_sort(app.contract_tree)
    if refresh_dependents:
        app.refresh_invoices()
        app.refresh_overdue()


@safe_ui_action("Refresh Customers")
def refresh_customers_action(
    app: Any,
    db: "DatabaseService",
    show_invalid_cb: Callable[[str], None],
    row_stripe_tag_cb: Callable[[int], str],
    get_contract_outstanding_as_of_cb: Callable[[int, date], float],
    outstanding_tag_from_amount_cb: Callable[[float], str],
) -> None:
    query_text = app.customer_search.get().strip()
    if len(query_text) > 80:
        show_invalid_cb("Search text must be 80 characters or fewer.")
        return

    existing_items = app.customer_tree.get_children()
    if existing_items:
        app.customer_tree.delete(*existing_items)

    rows = db.get_customers_with_truck_count(q=query_text if query_text else None, limit=200)
    contracts = db.get_contracts_for_grid(limit=5000)
    as_of = today()
    paid_rows = db.get_paid_totals_by_contract_as_of(as_of.isoformat())
    paid_by_contract = {int(row["contract_id"]): float(row["paid_total"]) for row in paid_rows}

    outstanding_by_customer_id: dict[int, float] = {}
    for contract in contracts:
        customer_id = int(contract["customer_id"])
        start_date = parse_ymd(str(contract["start_date"]))
        if not start_date:
            continue
        contract_id = int(contract["contract_id"])
        end_date = parse_ymd(str(contract["end_date"])) if contract["end_date"] else None
        effective_end = min(end_date, as_of) if end_date else as_of
        expected = float(contract["monthly_rate"]) * elapsed_months_inclusive(start_date, effective_end)
        outstanding = expected - paid_by_contract.get(contract_id, 0.0)
        outstanding_by_customer_id[customer_id] = outstanding_by_customer_id.get(customer_id, 0.0) + outstanding

    for row_index, row in enumerate(rows):
        customer_outstanding = outstanding_by_customer_id.get(int(row["id"]), 0.0)
        app.customer_tree.insert(
            "",
            "end",
            values=(
                row["id"],
                row["name"],
                row["phone"] or "",
                row["company"] or "",
                row["notes"] or "",
                f"${customer_outstanding:.2f}",
                int(row["truck_count"]),
            ),
            tags=(row_stripe_tag_cb(row_index), outstanding_tag_from_amount_cb(customer_outstanding)),
        )

    app._reapply_tree_sort(app.customer_tree)
    app._reload_customer_dropdowns()


@safe_ui_action("Refresh Trucks")
def refresh_trucks_action(
    app: Any,
    db: "DatabaseService",
    show_invalid_cb: Callable[[str], None],
    row_stripe_tag_cb: Callable[[int], str],
    get_contract_outstanding_as_of_cb: Callable[[int, date], float],
    outstanding_tag_from_text_cb: Callable[[str], str],
    truck_search_mode: str = "all",
    customer_filter_id: int | None = None,
) -> None:
    query_text = app.truck_search.get().strip()
    if len(query_text) > 80:
        show_invalid_cb("Search text must be 80 characters or fewer.")
        return

    existing_items = app.truck_tree.get_children()
    if existing_items:
        app.truck_tree.delete(*existing_items)

    rows = db.get_trucks_with_customer(
        q=query_text if query_text else None,
        limit=300,
        customer_id=customer_filter_id,
        search_mode=truck_search_mode,
    )
    as_of = today()
    paid_rows = db.get_paid_totals_by_contract_as_of(as_of.isoformat())
    paid_by_contract = {int(row["contract_id"]): float(row["paid_total"]) for row in paid_rows}

    for row_index, row in enumerate(rows):
        outstanding_text = "NO CONTRACT"
        contract_row = db.get_preferred_contract_for_truck(int(row["id"]))
        if contract_row:
            contract_id = int(contract_row["contract_id"])
            start_date = parse_ymd(str(contract_row["start_date"]))
            end_date = parse_ymd(str(contract_row["end_date"])) if contract_row["end_date"] else None
            if start_date:
                effective_end = min(end_date, as_of) if end_date else as_of
                expected = float(contract_row["monthly_rate"]) * elapsed_months_inclusive(start_date, effective_end)
                outstanding_amt = expected - paid_by_contract.get(contract_id, 0.0)
            else:
                outstanding_amt = 0.0
            outstanding_text = f"${outstanding_amt:.2f}"

        app.truck_tree.insert(
            "",
            "end",
            values=(
                row["id"],
                row["plate"],
                row["state"] or "",
                row["make"] or "",
                row["model"] or "",
                row["customer_name"] or "",
                outstanding_text,
            ),
            tags=(row_stripe_tag_cb(row_index), outstanding_tag_from_text_cb(outstanding_text)),
        )

    app._reapply_tree_sort(app.truck_tree)
    app._reload_truck_dropdowns()


@safe_ui_action("Show Customer Ledger")
def show_customer_ledger_action(
    app: Any,
    db: "DatabaseService",
    tag_colors: dict[str, dict[str, str]],
    log_action_cb: Callable[[str, str], None],
    export_customer_ledger_xlsx_cb: Callable[..., None],
) -> None:
    sel = app.customer_tree.selection()
    if not sel:
        messagebox.showwarning("No Selection", "Select a customer row first.")
        return
    cvals = app.customer_tree.item(sel[0], "values")
    if not cvals:
        return

    customer_id = int(cvals[0])
    customer_name = cvals[1]
    customer_phone = cvals[2] if len(cvals) > 2 else ""
    customer_company = cvals[3] if len(cvals) > 3 else ""

    contracts = db.get_contracts_for_customer_ledger(customer_id)

    win = tk.Toplevel(app)
    win.title(f"Customer Ledger — {customer_name} (ID {customer_id})")
    win.geometry("1460x900")
    win.minsize(1320, 780)
    win.resizable(True, True)
    win.transient(app)
    win.grab_set()
    win.columnconfigure(0, weight=1)
    win.rowconfigure(2, weight=1)

    hdr = ttk.LabelFrame(win, text="Customer")
    hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
    for col, (lbl, val) in enumerate(
        [
            ("ID", str(customer_id)),
            ("Name", customer_name),
            ("Phone", customer_phone or "—"),
            ("Company", customer_company or "—"),
        ]
    ):
        ttk.Label(hdr, text=f"{lbl}:", font=FONTS.get("label_bold")).grid(
            row=0,
            column=col * 2,
            sticky="e",
            padx=(10, 2),
            pady=6,
        )
        ttk.Label(hdr, text=val).grid(
            row=0,
            column=col * 2 + 1,
            sticky="w",
            padx=(0, 16),
            pady=6,
        )

    actions = ttk.Frame(win)
    actions.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 4))
    ttk.Label(actions, text="Ledger Entries", font=FONTS.get("label_bold")).pack(side="left")

    tbl = ttk.Frame(win)
    tbl.grid(row=2, column=0, sticky="nsew", padx=12, pady=4)
    tbl.columnconfigure(0, weight=1)
    tbl.rowconfigure(0, weight=1)

    cols = ("entry", "period", "billed", "paid", "balance", "detail", "notes")
    headings = {
        "entry": "Entry",
        "period": "Date / Period",
        "billed": "Billed",
        "paid": "Paid",
        "balance": "Outstanding",
        "detail": "Scope / Method",
        "notes": "Notes / Reference",
    }
    widths = {
        "entry": 190,
        "period": 185,
        "billed": 90,
        "paid": 90,
        "balance": 90,
        "detail": 140,
        "notes": 220,
    }

    tree = ttk.Treeview(tbl, columns=cols, show="headings", height=22)
    for col_name in cols:
        tree.heading(col_name, text=headings[col_name], anchor="center")
        tree.column(col_name, width=widths[col_name], anchor="center")
    tree.column("entry", anchor="w")
    tree.column("notes", anchor="w")

    vsb = ttk.Scrollbar(tbl, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    palette = tag_colors.get("_palette", {})
    is_dark_mode = bool(getattr(app, "theme_mode", "light") == "dark")

    if is_dark_mode:
        contract_active_bg = palette.get("stripe_odd", "#243142")
        contract_active_fg = palette.get("text", "#f4f8ff")
        contract_inactive_bg = palette.get("tree_bg", "#1d2632")
        contract_inactive_fg = palette.get("muted_text", "#d5deea")
    else:
        contract_active_bg = tag_colors["contract_active"]["background"]
        contract_active_fg = palette.get("text", "#111111")
        contract_inactive_bg = tag_colors["contract_inactive"]["background"]
        contract_inactive_fg = tag_colors["contract_inactive"]["foreground"]

    tree.tag_configure(
        "contract_active",
        background=contract_active_bg,
        foreground=contract_active_fg,
        font=tag_colors["contract_active"]["font"],
    )
    tree.tag_configure(
        "contract_inactive",
        background=contract_inactive_bg,
        foreground=contract_inactive_fg,
        font=tag_colors["contract_inactive"]["font"],
    )

    payment_row_bg = palette.get("stripe_even", "#ffffff")
    payment_row_fg = palette.get("text", "#111111")
    no_payments_fg = palette.get("muted_text", "#aaaaaa")

    tree.tag_configure("payment_row", background=payment_row_bg, foreground=payment_row_fg)
    tree.tag_configure("no_payments", background=payment_row_bg, foreground=no_payments_fg)

    grand_billed = 0.0
    grand_paid = 0.0
    as_of = today()

    for contract in contracts:
        contract_id = int(contract["id"])
        is_active = bool(contract["is_active"])
        rate = float(contract["monthly_rate"])
        scope = contract["scope"]
        truck_info = contract["truck_info"] or ""
        start_d = parse_ymd(contract["start_d"])
        end_d = parse_ymd(contract["end_d"]) if contract["end_d"] else None
        start_raw = contract["start_raw"] or ""
        end_raw = contract["end_raw"] or "ongoing"
        contract_notes = contract["notes"] or ""
        status_lbl = "Active" if is_active else "Inactive"

        if start_d:
            effective_end = min(end_d, as_of) if end_d else as_of
            months_elapsed = elapsed_months_inclusive(start_d, effective_end)
            billed = rate * months_elapsed
        else:
            billed = 0.0

        payments = db.get_payments_for_contract(contract_id)
        total_paid = sum(float(payment["amount"]) for payment in payments)
        outstanding = billed - total_paid

        grand_billed += billed
        grand_paid += total_paid

        detail_str = f"{scope}" + (f"  {truck_info}" if truck_info else "")
        contract_iid = tree.insert(
            "",
            "end",
            values=(
                f"📋 Contract #{contract_id}  [{status_lbl}]",
                f"{start_raw} → {end_raw}",
                f"${billed:.2f}",
                f"${total_paid:.2f}",
                f"${outstanding:.2f}",
                detail_str,
                contract_notes,
            ),
            open=True,
            tags=("contract_active" if is_active else "contract_inactive",),
        )

        if not payments:
            tree.insert(
                contract_iid,
                "end",
                values=("   └ (no payments)", "", "", "", "", "", ""),
                tags=("no_payments",),
            )
        else:
            for idx, payment in enumerate(payments, start=1):
                ref_notes = " | ".join(filter(None, [payment["reference"], payment["notes"]]))
                tree.insert(
                    contract_iid,
                    "end",
                    values=(
                        f"   └ Payment #{idx}",
                        payment["paid_at"],
                        "",
                        f"${float(payment['amount']):.2f}",
                        "",
                        payment["method"],
                        ref_notes,
                    ),
                    tags=("payment_row",),
                )

    ftr = ttk.Frame(win)
    ftr.grid(row=3, column=0, sticky="ew", padx=12, pady=(4, 10))

    grand_outstanding = grand_billed - grand_paid
    summary = (
        f"Contracts: {len(contracts)}     "
        f"Total Billed: ${grand_billed:.2f}     "
        f"Total Paid: ${grand_paid:.2f}     "
        f"Total Outstanding: ${grand_outstanding:.2f}"
    )
    ttk.Label(ftr, text=summary, font=("TkDefaultFont", 10, "bold")).pack(side="left")

    def _export_ledger() -> None:
        export_customer_ledger_xlsx_cb(
            parent=win,
            tree=tree,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_company=customer_company,
            summary_text=summary,
            log_action=log_action_cb,
            default_date=today().isoformat(),
        )

    ttk.Button(actions, text="⬇ Export XLSX", command=_export_ledger).pack(side="right")
    ttk.Button(ftr, text="Close", command=win.destroy).pack(side="right")

    lang = getattr(app, "current_language", "en")
    if lang != "en":
        translate_widget_tree(win, lang)
        mapping = EN_TO_ZH
        for col_name in cols:
            if headings[col_name] in mapping:
                tree.heading(col_name, text=mapping[headings[col_name]])


@safe_ui_action("Refresh Overdue")
def refresh_overdue_action(
    app: Any,
    db: "DatabaseService",
    parse_ymd_cb: Callable[[str], date | None],
    ym_cb: Callable[[date], str],
    row_stripe_tag_cb: Callable[[int], str],
    outstanding_tag_from_amount_cb: Callable[[float], str],
    search_query: str = "",
) -> None:
    if not hasattr(app, "overdue_tree"):
        return
    existing_items = app.overdue_tree.get_children()
    if existing_items:
        app.overdue_tree.delete(*existing_items)

    as_of_text = app.overdue_as_of.get().strip() if hasattr(app, "overdue_as_of") else today().isoformat()
    as_of = parse_ymd_cb(as_of_text)
    if not as_of:
        messagebox.showerror("Date format error", "As-of date format must be YYYY-MM-DD.")
        return

    rows = db.get_contracts_with_customer_plate_for_overdue()
    as_of_month = ym_cb(as_of)
    paid_rows = db.get_paid_totals_by_contract_as_of(as_of.isoformat())
    paid_by_contract = {int(row["contract_id"]): float(row["paid_total"]) for row in paid_rows}
    query_l = normalize_whitespace(search_query).lower()
    visible_row_index = 0

    for row in rows:
        customer_name = str(row["customer_name"] or "")
        plate = str(row["plate"] or "")
        if query_l and query_l not in customer_name.lower() and query_l not in plate.lower():
            continue

        start_date = parse_ymd_cb(row["start_date"])
        if not start_date or start_date > as_of:
            continue

        end_date = parse_ymd_cb(row["end_date"]) if row["end_date"] else None
        if int(row["is_active"]) != 1 and end_date is None:
            continue

        effective_end = min(end_date, as_of) if end_date else as_of
        months_elapsed = elapsed_months_inclusive(start_date, effective_end)
        expected = float(row["monthly_rate"]) * months_elapsed
        paid = paid_by_contract.get(int(row["contract_id"]), 0.0)
        bal = expected - paid

        if bal > 0.01:
            scope = plate if plate else "(customer-level)"
            app.overdue_tree.insert(
                "",
                "end",
                values=(
                    as_of_month,
                    as_of.isoformat(),
                    int(row["contract_id"]),
                    customer_name,
                    scope,
                    f"${expected:.2f}",
                    f"${paid:.2f}",
                    f"${bal:.2f}",
                ),
                tags=(row_stripe_tag_cb(visible_row_index), outstanding_tag_from_amount_cb(bal)),
            )
            visible_row_index += 1

    app._reapply_tree_sort(app.overdue_tree)


@safe_ui_action("Refresh Statement")
def refresh_statement_action(
    app: Any,
    db: "DatabaseService",
    ym_cb: Callable[[date], str],
    parse_ym_cb: Callable[[str], tuple[int, int] | None],
    add_months_cb: Callable[[int, int, int], tuple[int, int]],
    parse_ymd_cb: Callable[[str], date | None],
) -> None:
    if not hasattr(app, "statement_month"):
        return

    target = app.statement_month.get().strip() or ym_cb(today())
    parsed_month = parse_ym_cb(target)
    if len(target) > 7 or not parsed_month:
        app.statement_expected_var.set("Invalid month")
        app.statement_paid_var.set("Invalid month")
        app.statement_balance_var.set("Invalid month")
        return

    year, month = parsed_month
    month_start = date(year, month, 1)
    next_year, next_month = add_months_cb(year, month, 1)
    month_end = date(next_year, next_month, 1) - timedelta(days=1)
    prev_month_end = month_start - timedelta(days=1)

    contracts = db.get_contracts_for_statement()

    payment_rows = db.get_paid_totals_by_contract()
    paid_by_contract = {int(row["contract_id"]): float(row["paid_total"]) for row in payment_rows}

    def _expected_for_month(month_start_local: date, month_end_local: date) -> float:
        prev_month_end_local = month_start_local - timedelta(days=1)
        expected_local = 0.0

        for local_row in contracts:
            start_date_local = parse_ymd_cb(local_row["start_date"])
            if not start_date_local:
                continue

            contract_end_local = parse_ymd_cb(local_row["end_date"]) if local_row["end_date"] else None
            if int(local_row["is_active"]) != 1 and contract_end_local is None:
                continue

            effective_end_month_local = month_end_local if contract_end_local is None else min(contract_end_local, month_end_local)
            effective_end_prev_local = prev_month_end_local if contract_end_local is None else min(contract_end_local, prev_month_end_local)

            months_through_month_local = elapsed_months_inclusive(start_date_local, effective_end_month_local)
            months_through_prev_local = elapsed_months_inclusive(start_date_local, effective_end_prev_local)

            rate_local = float(local_row["monthly_rate"])
            expected_through_month_local = rate_local * months_through_month_local
            expected_through_prev_local = rate_local * months_through_prev_local
            expected_for_month_local = max(0.0, expected_through_month_local - expected_through_prev_local)
            expected_local += expected_for_month_local

        return expected_local

    expected_total = 0.0
    paid_total = 0.0
    for row in contracts:
        start_date = parse_ymd_cb(row["start_date"])
        if not start_date:
            continue

        contract_end = parse_ymd_cb(row["end_date"]) if row["end_date"] else None
        if int(row["is_active"]) != 1 and contract_end is None:
            continue

        effective_end_month = month_end if contract_end is None else min(contract_end, month_end)
        effective_end_prev = prev_month_end if contract_end is None else min(contract_end, prev_month_end)

        months_through_month = elapsed_months_inclusive(start_date, effective_end_month)
        months_through_prev = elapsed_months_inclusive(start_date, effective_end_prev)

        rate = float(row["monthly_rate"])
        expected_through_month = rate * months_through_month
        expected_through_prev = rate * months_through_prev
        expected_for_month = max(0.0, expected_through_month - expected_through_prev)
        expected_total += expected_for_month

        contract_paid = paid_by_contract.get(int(row["contract_id"]), 0.0)
        allocated_through_month = min(contract_paid, expected_through_month)
        allocated_through_prev = min(contract_paid, expected_through_prev)
        allocated_for_month = max(0.0, allocated_through_month - allocated_through_prev)
        if allocated_for_month > expected_for_month:
            allocated_for_month = expected_for_month
        paid_total += allocated_for_month

    if hasattr(app, "statement_expected_chart_canvas"):
        chart_mode = "combo"
        if hasattr(app, "statement_chart_mode"):
            chart_mode = str(app.statement_chart_mode.get() or "combo").strip().lower()
        if chart_mode not in {"bar", "line", "combo"}:
            chart_mode = "combo"

        chart_points: list[tuple[str, float]] = []
        for offset in range(11, -1, -1):
            y_i, m_i = add_months_cb(year, month, -offset)
            m_start_i = date(y_i, m_i, 1)
            n_y_i, n_m_i = add_months_cb(y_i, m_i, 1)
            m_end_i = date(n_y_i, n_m_i, 1) - timedelta(days=1)
            chart_points.append((f"{y_i:04d}-{m_i:02d}", _expected_for_month(m_start_i, m_end_i)))

        canvas = app.statement_expected_chart_canvas
        canvas.update_idletasks()
        width = max(int(canvas.winfo_width()), 640)
        height = max(int(canvas.winfo_height()), 300)
        canvas.delete("all")
        canvas.configure(bg="#ffffff")

        pad_l, pad_r, pad_t, pad_b = 64, 24, 26, 52
        x0, y0 = pad_l, pad_t
        x1, y1 = width - pad_r, height - pad_b

        canvas.create_line(x0, y1, x1, y1, fill="#2b2b2b", width=2)
        canvas.create_line(x0, y0, x0, y1, fill="#2b2b2b", width=2)

        max_val = max((val for _, val in chart_points), default=0.0)
        if max_val <= 0:
            max_val = 1.0
        max_val *= 1.08

        y_ticks = 4
        for i in range(y_ticks + 1):
            v = max_val * (i / y_ticks)
            y_px = y1 - (i / y_ticks) * (y1 - y0)
            canvas.create_line(x0, y_px, x1, y_px, fill="#d6dbe3", width=1)
            canvas.create_text(x0 - 8, y_px, text=f"${v:,.0f}", anchor="e", fill="#1f2937", font=("TkDefaultFont", 9, "bold"))

        span = max(1, len(chart_points) - 1)
        poly_coords: list[float] = []
        slot_w = (x1 - x0) / max(1, len(chart_points))
        bar_w = max(8.0, min(30.0, slot_w * 0.55))

        for idx, (label, val) in enumerate(chart_points):
            x_px = x0 + (idx / span) * (x1 - x0)
            y_px = y1 - (val / max_val) * (y1 - y0)
            bar_left = x_px - (bar_w / 2)
            bar_right = x_px + (bar_w / 2)
            if chart_mode in {"bar", "combo"}:
                canvas.create_rectangle(
                    bar_left,
                    y_px,
                    bar_right,
                    y1,
                    fill="#9fc4ff",
                    outline="#7eaaf5",
                    width=1,
                )

            poly_coords.extend([x_px, y_px])
            if chart_mode in {"line", "combo"}:
                canvas.create_oval(x_px - 3, y_px - 3, x_px + 3, y_px + 3, fill="#1148a8", outline="#1148a8")
            if idx in {0, len(chart_points) - 1} or idx % 2 == 0:
                canvas.create_text(x_px, y1 + 16, text=label[5:], anchor="n", fill="#1f2937", font=("TkDefaultFont", 9, "bold"))

            if idx in {len(chart_points) - 1, max(0, len(chart_points) - 4), 0}:
                canvas.create_text(
                    x_px,
                    max(y0 + 10, y_px - 10),
                    text=f"${val:,.0f}",
                    anchor="s",
                    fill="#0f2f75",
                    font=("TkDefaultFont", 9, "bold"),
                )

        if chart_mode in {"line", "combo"} and len(poly_coords) >= 4:
            canvas.create_line(*poly_coords, fill="#1148a8", width=3, smooth=True)

        latest_label, latest_val = chart_points[-1]
        canvas.create_text(
            x1,
            y0,
            anchor="ne",
            text=f"{latest_label}: ${latest_val:,.2f}",
            fill="#111827",
            font=("TkDefaultFont", 10, "bold"),
        )

        canvas.create_text(
            x0,
            y0,
            anchor="nw",
            text=f"12-Month Expected Revenue Trend ({chart_mode.title()})",
            fill="#111827",
            font=("TkDefaultFont", 10, "bold"),
        )

    outstanding = expected_total - paid_total
    app.statement_expected_var.set(f"${expected_total:.2f}")
    app.statement_paid_var.set(f"${paid_total:.2f}")
    app.statement_balance_var.set(f"${outstanding:.2f}")


@safe_ui_action("Refresh History")
def refresh_histories_action(
    app: Any,
    ensure_history_log_exists_cb: Callable[[], None],
    history_log_file: str,
) -> None:
    ensure_history_log_exists_cb()
    try:
        with open(history_log_file, "r", encoding="utf-8") as file_handle:
            log = file_handle.read()
    except Exception as exc:
        logger.warning(f"Failed to read history log file: {exc}")
        log = "(No log file found)\n"
    app.histories_text.configure(state="normal")
    app.histories_text.delete("1.0", tk.END)
    app.histories_text.insert("1.0", log)
    app.histories_text.see(tk.END)
    app.histories_text.configure(state="disabled")


@safe_ui_action("Generate Invoice PDF")
def generate_customer_invoice_pdf_for_customer_id_action(
    app: Any,
    db: "DatabaseService",
    customer_id: int,
    build_pdf_invoice_data_cb: Callable[..., Any],
    reportlab_available_cb: Callable[[], bool],
    render_invoice_pdf_cb: Callable[[str, Any], None],
) -> None:
    if not reportlab_available_cb():
        messagebox.showerror("Missing Dependency", "reportlab is required to generate PDFs.\nInstall with: pip install reportlab")
        return

    try:
        customer_name = f"customer_{customer_id}"
        customer_row = db.get_customer_basic_by_id(customer_id)
        if customer_row and customer_row["name"]:
            customer_name = str(customer_row["name"])

        file_path = filedialog.asksaveasfilename(
            title=f"Save Invoice PDF for {customer_name}",
            defaultextension=".pdf",
            initialfile=f"invoice_{customer_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            filetypes=[("PDF Document", "*.pdf"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        if getattr(app, "_pdf_export_in_progress", False):
            messagebox.showinfo("PDF Generation", "A PDF is already being generated. Please wait.")
            return

        app._pdf_export_in_progress = True

        def _on_complete(success: bool, message: str) -> None:
            app._pdf_export_in_progress = False
            if success:
                messagebox.showinfo("Success", message)
                app.refresh_histories()
            else:
                messagebox.showerror("Error", message)

        def _worker() -> None:
            worker_db = None
            try:
                from data.database_service import DatabaseService

                worker_db = DatabaseService(db.db_path)

                t0 = perf_counter()
                invoice_data = build_pdf_invoice_data_cb(worker_db, customer_id, datetime.now().date(), payments_limit=5)
                build_ms = (perf_counter() - t0) * 1000

                if not invoice_data:
                    app.after(0, lambda: _on_complete(False, f"Customer ID {customer_id} not found."))
                    return

                t1 = perf_counter()
                render_invoice_pdf_cb(file_path, invoice_data)
                render_ms = (perf_counter() - t1) * 1000
                total_ms = (perf_counter() - t0) * 1000

                trace_logger.debug(
                    "PDF_TIMING customer_id=%s build_ms=%.2f render_ms=%.2f total_ms=%.2f contracts=%s payments=%s",
                    customer_id,
                    build_ms,
                    render_ms,
                    total_ms,
                    len(invoice_data.contracts),
                    len(invoice_data.recent_payments),
                )

                app.after(0, lambda: _on_complete(True, f"Invoice PDF saved to:\n{file_path}"))
            except Exception as exc:
                error_msg = f"Could not generate PDF:\n{exc}"
                app.after(0, lambda: _on_complete(False, error_msg))
            finally:
                if worker_db is not None:
                    try:
                        worker_db.close()
                    except Exception:
                        pass

        threading.Thread(target=_worker, daemon=True).start()
    except Exception as exc:
        app._pdf_export_in_progress = False
        messagebox.showerror("Error", f"Could not generate PDF:\n{exc}")


@safe_ui_action("Generate Invoice PDF")
def generate_customer_invoice_pdf_action(
    app: Any,
    generate_customer_invoice_pdf_for_customer_id_cb: Callable[[int], None],
) -> None:
    sel = app.customer_tree.selection()
    if not sel:
        messagebox.showwarning("No Selection", "Select a customer first.")
        return
    values = app.customer_tree.item(sel[0], "values")
    if not values:
        return
    customer_id = int(values[0])
    generate_customer_invoice_pdf_for_customer_id_cb(customer_id)


@safe_ui_action("Generate Invoice PDF from Billing")
def generate_invoice_pdf_from_billing_selection_action(
    app: Any,
    db: "DatabaseService",
    generate_customer_invoice_pdf_for_customer_id_cb: Callable[[int], None],
) -> None:
    sel = app.invoice_tree.selection()
    if not sel:
        messagebox.showwarning("No Selection", "Select an invoice row first.")
        return

    values = app.invoice_tree.item(sel[0], "values")
    if not values:
        messagebox.showerror("Invalid selection", "Could not read selected invoice row.")
        return

    customer_id = None
    contract_id_str = str(values[0]).strip()
    try:
        contract_id = int(contract_id_str)
        customer_id = db.get_customer_id_by_contract(contract_id)
    except (ValueError, TypeError):
        customer_name = str(values[1]).strip() if len(values) > 1 else ""
        if not customer_name:
            messagebox.showwarning("No customer", "Could not determine customer from selected row.")
            return
        customer_id = db.get_first_customer_id_by_name(customer_name)
        if not customer_id:
            messagebox.showerror("Not found", f"Customer '{customer_name}' not found.")
            return

    if not customer_id:
        messagebox.showwarning("No customer", "Could not determine customer for invoice generation.")
        return

    generate_customer_invoice_pdf_for_customer_id_cb(customer_id)


@safe_ui_action("Refresh Invoices")
def refresh_invoices_action(
    app: Any,
    db: "DatabaseService",
    build_invoice_groups_cb: Callable[["DatabaseService", date], tuple[Any, float]],
    invoice_group_label_cb: Callable[[int, bool], str],
    status_badge_cb: Callable[[str], str],
    refresh_invoice_parent_labels_cb: Callable[[], None],
    outstanding_tag_from_amount_cb: Callable[[float], str],
) -> None:
    as_of_text = app.invoice_date.get().strip() or today().isoformat()
    as_of_date = parse_ymd(as_of_text)

    customer_query = ""
    if hasattr(app, "invoice_customer_search"):
        customer_query = normalize_whitespace(app.invoice_customer_search.get()).lower()

    expanded_customers = set()
    selected_contract_id = None
    for item in app.invoice_tree.get_children():
        try:
            values = app.invoice_tree.item(item, "values")
            if app.invoice_tree.item(item, "open") and values and len(values) > 1:
                expanded_customers.add(str(values[1]))
        except Exception as exc:
            logger.debug(f"Failed to get expanded customer state: {exc}")

    sel = app.invoice_tree.selection()
    if sel:
        try:
            sel_values = app.invoice_tree.item(sel[0], "values")
            selected_contract_id = int(str(sel_values[0]).strip())
        except Exception as exc:
            logger.debug(f"Failed to get selected invoice contract ID: {exc}")
            selected_contract_id = None

    if not as_of_date:
        for item in app.invoice_tree.get_children():
            app.invoice_tree.delete(item)
        app.invoice_total_balance_var.set("$0.00")
        messagebox.showerror("Date format error", "As-of date format must be YYYY-MM-DD.")
        return

    for item in app.invoice_tree.get_children():
        app.invoice_tree.delete(item)

    groups, total_outstanding = build_invoice_groups_cb(db, as_of_date)
    selected_child_iid = None

    for group in groups:
        if customer_query and customer_query not in group.customer_name.lower():
            continue

        cust_row_tag = outstanding_tag_from_amount_cb(float(group.total_outstanding))
        parent_is_open = group.customer_name in expanded_customers
        cust_parent_id = app.invoice_tree.insert(
            "",
            "end",
            values=(
                "",
                group.customer_name,
                invoice_group_label_cb(len(group.contracts), parent_is_open),
                "",
                "",
                "",
                "",
                f"${group.total_expected:.2f}",
                f"${group.total_paid:.2f}",
                f"${group.total_outstanding:.2f}",
                status_badge_cb(group.status),
            ),
            tags=(cust_row_tag,),
        )

        if parent_is_open:
            app.invoice_tree.item(cust_parent_id, open=True)

        for contract_line in group.contracts:
            row_tag = outstanding_tag_from_amount_cb(float(contract_line.outstanding))

            child_iid = app.invoice_tree.insert(
                cust_parent_id,
                "end",
                values=(
                    contract_line.contract_id,
                    "",
                    contract_line.scope,
                    f"${contract_line.monthly_rate:.2f}",
                    contract_line.start_date,
                    contract_line.end_date,
                    contract_line.months_elapsed,
                    f"${contract_line.expected_amount:.2f}",
                    f"${contract_line.paid_total:.2f}",
                    f"${contract_line.outstanding:.2f}",
                    status_badge_cb(contract_line.status),
                ),
                tags=(row_tag,),
            )

            if selected_contract_id is not None and contract_line.contract_id == selected_contract_id:
                selected_child_iid = child_iid

    app.invoice_total_balance_var.set(f"${total_outstanding:.2f}")
    refresh_invoice_parent_labels_cb()
    if hasattr(app, "_apply_invoice_tree_visual_tags"):
        app._apply_invoice_tree_visual_tags()

    app._reapply_tree_sort(app.invoice_tree)
    if hasattr(app, "_reapply_invoice_tree_sort"):
        app._reapply_invoice_tree_sort()
    if selected_child_iid:
        app.invoice_tree.selection_set(selected_child_iid)
        app.invoice_tree.focus(selected_child_iid)


@safe_ui_action("Reset Contract Payments")
def reset_contract_payments_action(
    app: Any,
    db: "DatabaseService",
    log_action_cb: Callable[[str, str], None],
) -> None:
    sel = app.invoice_tree.selection()
    if not sel:
        messagebox.showwarning("No Selection", "Select a contract row in the invoice table first.")
        return
    values = app.invoice_tree.item(sel[0], "values")
    if not values:
        return

    try:
        contract_id = int(str(values[0]).strip())
    except (ValueError, TypeError):
        messagebox.showinfo("Select a contract", "Please select a contract row (not a customer group).")
        return

    customer = values[1]
    if not customer:
        customer = db.get_customer_name_by_contract(contract_id) or ""

    paid_str = str(values[8]).replace("$", "").strip()
    try:
        paid_amt = float(paid_str)
    except ValueError:
        paid_amt = 0.0

    payment_count = db.get_payment_count_by_contract(contract_id)
    if payment_count == 0:
        messagebox.showinfo("Nothing to Reset", "This contract has no recorded payments.")
        return

    confirmed = messagebox.askyesno(
        "Confirm Reset Payments",
        (
            f"Reset ALL payments for Contract ID {contract_id}?\n"
            f"Customer: {customer}\n"
            f"Payments to delete: {payment_count}\n"
            f"Total paid amount to reverse: ${paid_amt:.2f}\n\n"
            "This cannot be undone."
        ),
        icon="warning",
    )
    if not confirmed:
        return

    db.delete_payments_by_contract(contract_id)
    db.commit()
    log_action_cb(
        "RESET_PAYMENTS",
        f"Contract ID: {contract_id}, Customer: {customer}, Deleted Payments: {payment_count}, Reversed Amount: ${paid_amt:.2f}",
    )

    app.refresh_customers()
    app.refresh_contracts()
    app.refresh_invoices()
    app.refresh_statement()
    app.refresh_overdue()
    app.refresh_dashboard()
    messagebox.showinfo("Done", f"All {payment_count} payment(s) for Contract {contract_id} have been removed.")


@safe_ui_action("Open Payment Form")
def open_payment_form_window_action(
    app: Any,
    open_payment_form_for_contract_cb: Callable[[int, str | None, date | None], None],
) -> None:
    sel = app.invoice_tree.selection()
    if not sel:
        messagebox.showwarning("No selection", "Please select an invoice first.")
        return

    try:
        values = app.invoice_tree.item(sel[0], "values")
        if not values or len(values) < 10:
            messagebox.showwarning("Invalid row", "Unable to read invoice data.")
            return

        contract_id_str = str(values[0]).strip()

        try:
            contract_id = int(contract_id_str)
        except (ValueError, TypeError):
            messagebox.showinfo("Parent row", "Please select a plate row (not a customer).")
            return

        plate_label = str(values[2]).strip() if len(values) > 2 else ""
        if not plate_label:
            plate_label = "(customer-level)"

        as_of_text = app.invoice_date.get().strip() if hasattr(app, "invoice_date") else ""
        as_of_date = parse_ymd(as_of_text) if as_of_text else None
        open_payment_form_for_contract_cb(contract_id, plate_label, as_of_date)
    except Exception as exc:
        messagebox.showerror("Error", f"Failed to open payment form: {exc}")


@safe_ui_action_returning("Get or Create Anchor Invoice", return_on_error=0, log_ux=False)
def get_or_create_anchor_invoice_action(
    db: "DatabaseService",
    contract_id: int,
    as_of_date: date,
) -> int:
    invoice_ym = ym(as_of_date)
    return db.get_or_create_anchor_invoice(
        contract_id,
        invoice_ym,
        as_of_date.isoformat(),
        now_iso(),
    )


@safe_ui_action_returning("Get Contract Outstanding", return_on_error=0.0, log_ux=False)
def get_contract_outstanding_as_of_action(
    db: "DatabaseService",
    contract_id: int,
    as_of_date: date,
) -> float:
    row = db.get_contract_snapshot(contract_id)
    if not row:
        return 0.0

    start_date = parse_ymd(row["start_date"])
    if not start_date:
        return 0.0

    effective_end = as_of_date
    if row["end_date"]:
        parsed_end = parse_ymd(row["end_date"])
        if parsed_end:
            effective_end = min(parsed_end, as_of_date)

    months_elapsed = elapsed_months_inclusive(start_date, effective_end)
    expected_amount = float(row["monthly_rate"]) * months_elapsed

    paid_total = db.get_paid_total_for_contract_as_of(contract_id, as_of_date.isoformat())
    return expected_amount - paid_total


@safe_ui_action("Clear Invoice Search")
def clear_invoice_customer_search_action(app: Any) -> None:
    if getattr(app, "_invoice_search_after_id", None) is not None:
        app.after_cancel(app._invoice_search_after_id)
        app._invoice_search_after_id = None
    if hasattr(app, "invoice_customer_search"):
        app.invoice_customer_search.delete(0, tk.END)
    app.refresh_invoices()


@safe_ui_action("Sync Customer to Forms")
def sync_selected_customer_to_forms_action(
    app: Any,
    set_selected_customer_cb: Callable[[int], None],
) -> None:
    sel = app.customer_tree.selection()
    if not sel:
        return
    values = app.customer_tree.item(sel[0], "values")
    if not values:
        return
    customer_id = int(values[0])
    set_selected_customer_cb(customer_id)


@safe_ui_action_returning("Check Unsaved Data", return_on_error=False)
def tab_has_unsaved_data_action(
    app: Any,
    tab_str: str,
    get_entry_value_cb: Callable[[Any], str],
) -> bool:
    try:
        if tab_str == str(app.tab_customers):
            return any(
                [
                    get_entry_value_cb(app.c_name),
                    get_entry_value_cb(app.c_phone),
                    get_entry_value_cb(app.c_company),
                    get_entry_value_cb(app.c_notes),
                ]
            )
        if tab_str == str(app.tab_trucks):
            return any(
                [
                    get_entry_value_cb(app.t_plate),
                    get_entry_value_cb(app.t_state),
                    get_entry_value_cb(app.t_make),
                    get_entry_value_cb(app.t_model),
                    get_entry_value_cb(app.t_notes),
                ]
            )
        if tab_str == str(app.tab_contracts):
            return any(
                [
                    get_entry_value_cb(app.contract_rate),
                    get_entry_value_cb(app.contract_notes),
                ]
            )
    except Exception:
        pass
    return False


@safe_ui_action("Handle Tab Change")
def on_tab_changed_action(
    app: Any,
    _event: Any,
    tab_has_unsaved_data_cb: Callable[[str], bool],
) -> None:
    current = app.main_notebook.select()
    previous = getattr(app, "_last_selected_tab", None)

    if previous and previous != current and tab_has_unsaved_data_cb(previous):
        leave = messagebox.askyesno(
            "Unsaved Form Data",
            "You have information typed in the form below that hasn't been saved yet.\n\n"
            "Leave this tab and lose what you typed?",
            icon="warning",
            default="no",
        )
        if not leave:
            app.main_notebook.select(previous)
            return

    app._last_selected_tab = current

    if current == str(app.tab_dashboard):
        app.refresh_dashboard()
    if current == str(app.tab_histories):
        app.refresh_histories()
