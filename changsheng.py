#!/usr/bin/env python3
"""
Changsheng - Truck Lot Tracker (Tkinter + SQLite)

GUI features:
- Add customer
- Add truck
- Create contract (per-truck OR customer-level)
- Generate invoices for a month
- View invoices for a month
- Record payment
- Overdue report (last 6 months)

Run:
  python changsheng.py

DB:
  changsheng.db (created automatically)
"""
from __future__ import annotations

import sqlite3
import ctypes
import json
import logging
import logging.handlers
import importlib
try:
    import openpyxl
except ImportError:
    openpyxl = None

from data.language_map import EN_TO_ZH, ZH_TO_EN
from data.database_service import DatabaseService
from dialogs.customer_picker import open_customer_picker
from dialogs.payment_history_dialog import show_contract_payment_history
from ui.ui_actions import on_tab_changed_action
from utils.billing_date_utils import (
    today,
    ym,
    parse_ym,
    parse_ymd,
    add_months,
)
from utils.validation import (
    normalize_whitespace,
)
from core.config import (
    DB_PATH, HISTORY_LOG_FILE, SETTINGS_FILE,
    WINDOW_WIDTH, WINDOW_HEIGHT, TREE_ROW_HEIGHT, TREE_ALT_ROW_COLORS, FONTS,
    DELETE_BUTTON_BG, SELECTION_BG, SELECTION_FG,
)
from dataclasses import dataclass
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
try:
    _DateEntryBase = importlib.import_module("tkcalendar").DateEntry

    class SmartDateEntry(_DateEntryBase):
        """DateEntry that opens the calendar upward when too close to the bottom of the screen."""

        def drop_down(self):
            super().drop_down()
            self.after_idle(self._reposition_popup)

        def _reposition_popup(self):
            top = getattr(self, "_top_cal", None)
            if top is None:
                return
            try:
                if not top.winfo_exists():
                    return
            except Exception as e:
                logger.debug(f"SmartDateEntry popup check failed: {e}")
                return
            self.update_idletasks()
            screen_h = self.winfo_screenheight()
            cal_h = top.winfo_reqheight()
            entry_root_y = self.winfo_rooty()
            entry_h = self.winfo_height()
            x = self.winfo_rootx()
            space_below = screen_h - (entry_root_y + entry_h)
            if space_below < cal_h + 20:
                # Not enough room below — open above
                top.geometry("+%d+%d" % (x, entry_root_y - cal_h - 4))
            else:
                top.geometry("+%d+%d" % (x, entry_root_y + entry_h + 2))

    DateEntry = SmartDateEntry
except Exception:
    DateEntry = None


from tabs.customers_tab import build_customers_tab
from tabs.trucks_tab import build_trucks_tab
from tabs.contracts_tab import build_contracts_tab
from tabs.dashboard_tab import build_dashboard_tab
from tabs.histories_tab import build_histories_tab
from tabs.billing_tab import build_billing_tab
from app.action_wrappers import ActionWrappersMixin
from core.app_logging import (
    setup_all_loggers,
    get_app_logger,
    log_ux_action,
    trace,
)

# Initialize all loggers (exception, ux_action, trace) at import time
setup_all_loggers()
logger = get_app_logger()

@trace
def log_action(event_type: str, details: str):
    """Append immutable action to history log file and UX action log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Also log to UX action log
    log_ux_action(event_type, details=details)
    try:
        with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {event_type} | {details}\n")
    except Exception as e:
        logger.error(f"Failed to write to history log file: {e}", exc_info=True)


def enable_windows_dpi_awareness() -> None:
    if ctypes is None:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception as e:
        logger.debug(f"SetProcessDpiAwareness failed, trying SetProcessDPIAware: {e}")
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception as e2:
            logger.debug(f"SetProcessDPIAware also failed: {e2}")


def sum_payments(db: DatabaseService, invoice_id: int) -> float:
    return db.get_total_payments_for_invoice(invoice_id)


def invoice_balance(db: DatabaseService, invoice_row: sqlite3.Row) -> tuple[float, float, float]:
    amt = float(invoice_row["amount"])

    # Some queries alias the invoice id as "invoice_id" instead of "id"
    if "id" in invoice_row.keys():
        inv_id = int(invoice_row["id"])
    else:
        inv_id = int(invoice_row["invoice_id"])

    paid = sum_payments(db, inv_id)
    bal = amt - paid
    return amt, paid, bal

@dataclass
class Customer:
    id: int
    name: str
    phone: str | None
    company: str | None


@dataclass
class Truck:
    id: int
    plate: str
    state: str | None
    customer_id: int | None




class App(ActionWrappersMixin, tk.Tk):
    def __init__(self):
        super().__init__()
        self.current_language = "en"
        self.language_selectors: list[ttk.Combobox] = []
        self.date_entry_cls = DateEntry
        self.title("Changsheng - Truck Lot Tracker")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self._set_startup_fullscreen()
        self._configure_ui_rendering()

        try:
            self.db = DatabaseService(DB_PATH)
        except Exception as exc:
            messagebox.showerror(
                "Database Integrity Error",
                "Integrity checks failed or migration could not be completed.\n\n"
                f"Details:\n{exc}",
            )
            self.destroy()
            return
        self._app_settings = self._load_app_settings()
        self._ensure_history_log_exists()
        self._log_action = log_action
        self._openpyxl_module = openpyxl

        # Top-level layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top_bar = ttk.Frame(self)
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=4)
        top_bar.columnconfigure(0, weight=1)
        
        ttk.Label(top_bar, text="Language:").grid(row=0, column=1, sticky="e", padx=(12, 4))
        self.global_lang_selector = self._create_language_selector(top_bar, width=6)
        self.global_lang_selector.grid(row=0, column=2, sticky="e")

        nb = ttk.Notebook(self, style="MainTabs.TNotebook")
        nb.grid(row=1, column=0, sticky="nsew")
        self.main_notebook = nb

        # Tabs
        self.tab_dashboard = ttk.Frame(nb)
        self.tab_customers = ttk.Frame(nb)
        self.tab_trucks = ttk.Frame(nb)
        self.tab_contracts = ttk.Frame(nb)
        self.tab_billing = ttk.Frame(nb)
        self.tab_histories = ttk.Frame(nb)

        nb.add(self.tab_dashboard, text="📈 Dashboard")
        nb.add(self.tab_customers, text="👥 Customers")
        nb.add(self.tab_trucks, text="🚚 Trucks")
        nb.add(self.tab_contracts, text="📝 Contracts")
        nb.add(self.tab_billing, text="💵 Billing")
        nb.add(self.tab_histories, text="🕑 Histories")

        build_dashboard_tab(self, self.tab_dashboard)
        build_customers_tab(self, self.tab_customers)
        build_trucks_tab(self, self.tab_trucks)
        build_contracts_tab(self, self.tab_contracts)
        build_billing_tab(self, self.tab_billing)
        build_histories_tab(self, self.tab_histories)
        self._setup_right_click_menus()

        # Auto-refresh histories when its tab is selected
        nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Initial loads
        self.refresh_customers()
        self.refresh_trucks()
        self.refresh_contracts()
        self.refresh_invoices()
        self.refresh_statement()
        self.refresh_overdue()
        self.refresh_dashboard()
        self.refresh_histories()
        self._set_language("en")

        self.after(800, self._prompt_backup_on_startup)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_right_click_menus(self):
        self.customer_menu = tk.Menu(self, tearoff=0)
        self.customer_menu.add_command(label="View Ledger", command=self.show_customer_ledger)
        self.customer_menu.add_separator()
        self.customer_menu.add_command(label="Generate PDF Invoice", command=self.generate_customer_invoice_pdf)
        self.customer_menu.add_separator()
        self.customer_menu.add_command(label="Delete Selected", command=self.delete_customer)
        self.customer_menu.add_separator()
        self.customer_menu.add_command(label="Refresh", command=self.refresh_customers)

        self.truck_menu = tk.Menu(self, tearoff=0)
        self.truck_menu.add_command(label="View Contract History", command=self.view_selected_truck_contract_history)
        self.truck_menu.add_separator()
        self.truck_menu.add_command(label="Delete Selected", command=self.delete_truck)
        self.truck_menu.add_separator()
        self.truck_menu.add_command(label="Refresh", command=self.refresh_trucks)

        self.contract_menu = tk.Menu(self, tearoff=0)
        self.contract_menu.add_command(label="View Payment History", command=self.show_contract_payment_history)
        self.contract_menu.add_separator()
        self.contract_menu.add_command(label="Edit Contract", command=self.edit_contract)
        self.contract_menu.add_command(label="Toggle Active/Inactive", command=self.toggle_contract)

        self.invoice_menu = tk.Menu(self, tearoff=0)
        self.invoice_menu.add_command(label="Fill Payment Form", command=self._open_payment_form_window)
        self.invoice_menu.add_command(label="Generate PDF Invoice", command=self._generate_invoice_pdf_from_billing_selection)
        self.invoice_menu.add_separator()
        self.invoice_menu.add_command(label="Reset Payments", command=self.reset_contract_payments)
        self.invoice_menu.add_separator()
        self.invoice_menu.add_command(label="Recalculate", command=self.refresh_invoices)

        self.overdue_menu = tk.Menu(self, tearoff=0)
        self.overdue_menu.add_command(label="Record Payment", command=self._record_payment_for_selected_overdue)
        self.overdue_menu.add_command(label="Generate PDF Invoice", command=self._generate_invoice_pdf_for_selected_overdue)
        self.overdue_menu.add_separator()
        self.overdue_menu.add_command(label="Refresh", command=self.refresh_overdue)

        self.customer_tree.bind("<Button-3>", lambda e: self._show_tree_context_menu(e, self.customer_tree, self.customer_menu))
        self.truck_tree.bind("<Button-3>", lambda e: self._show_tree_context_menu(e, self.truck_tree, self.truck_menu))
        self.contract_tree.bind("<Button-3>", lambda e: self._show_tree_context_menu(e, self.contract_tree, self.contract_menu))
        self.invoice_tree.bind("<Button-3>", lambda e: self._show_tree_context_menu(e, self.invoice_tree, self.invoice_menu))
        self.overdue_tree.bind("<Button-3>", lambda e: self._show_tree_context_menu(e, self.overdue_tree, self.overdue_menu))

    def _show_tree_context_menu(self, event: tk.Event, tree: ttk.Treeview, menu: tk.Menu):
        row_id = tree.identify_row(event.y)
        if row_id:
            tree.selection_set(row_id)
            tree.focus(row_id)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _clear_dashboard_global_search(self):
        if self._dashboard_search_after_id is not None:
            self.after_cancel(self._dashboard_search_after_id)
            self._dashboard_search_after_id = None
        if hasattr(self, "dashboard_search_entry"):
            self.dashboard_search_entry.delete(0, tk.END)
            self.dashboard_search_entry.focus_set()
        if hasattr(self, "dashboard_search_tree"):
            for item in self.dashboard_search_tree.get_children():
                self.dashboard_search_tree.delete(item)
        self._dashboard_search_result_map = {}

    def _schedule_dashboard_global_search(self, delay_ms: int = 250):
        if self._dashboard_search_after_id is not None:
            self.after_cancel(self._dashboard_search_after_id)
        self._dashboard_search_after_id = self.after(delay_ms, self._run_dashboard_global_search)

    def _run_dashboard_global_search(self):
        self._dashboard_search_after_id = None
        if not hasattr(self, "dashboard_search_tree"):
            return

        query = normalize_whitespace(self.dashboard_search_entry.get())
        if not query:
            self._clear_dashboard_global_search()
            return

        query_l = query.lower()
        selected_label = self.dashboard_search_field.get().strip() if hasattr(self, "dashboard_search_field") else "All"
        selected_field = self.dashboard_search_fields.get(selected_label, "all")
        field = self._detect_dashboard_search_field(query) if selected_field == "all" else selected_field

        for item in self.dashboard_search_tree.get_children():
            self.dashboard_search_tree.delete(item)
        self._dashboard_search_result_map = {}

        def _matches(field_name: str, candidate: str) -> bool:
            candidate_l = normalize_whitespace(candidate).lower()
            if not candidate_l:
                return False
            if field == "name_or_company" and field_name in {"name", "company"}:
                return query_l in candidate_l
            return query_l in candidate_l and (field == "all" or field == field_name)

        results: list[tuple[str, str, str, dict[str, str | int]]] = []

        customer_rows = self.db.get_customers_with_truck_count(q=None, limit=5000)
        for row in customer_rows:
            name = str(row["name"] or "")
            phone = str(row["phone"] or "")
            company = str(row["company"] or "")
            if _matches("name", name) or _matches("phone", phone) or _matches("company", company):
                detail = f"Phone: {phone or '—'} | Company: {company or '—'}"
                results.append(("Customer", name, detail, {"tab": "customers", "id": int(row["id"]) }))

        truck_rows = self.db.get_trucks_with_customer(q=None, limit=5000)
        for row in truck_rows:
            plate = str(row["plate"] or "")
            customer = str(row["customer_name"] or "")
            if _matches("plate", plate) or (field == "all" and query_l in customer.lower()):
                detail = f"Customer: {customer or '—'} | {str(row['make'] or '—')} {str(row['model'] or '')}".strip()
                results.append(("Truck", plate, detail, {"tab": "trucks", "id": int(row["id"]) }))

        for result_type, match_text, detail, meta in results:
            iid = self.dashboard_search_tree.insert("", "end", values=(result_type, match_text, detail))
            self._dashboard_search_result_map[iid] = meta

    def _detect_dashboard_search_field(self, query: str) -> str:
        text = normalize_whitespace(query)
        if not text:
            return "all"

        lowered = text.lower()
        digit_count = sum(ch.isdigit() for ch in text)
        has_alpha = any(ch.isalpha() for ch in text)
        has_digit = digit_count > 0

        if lowered.startswith("#") and lowered[1:].isdigit():
            return "name_or_company"
        if lowered.startswith("contract ") and lowered.split(" ", 1)[1].isdigit():
            return "name_or_company"

        if has_alpha and has_digit:
            return "plate"

        phone_chars = set("0123456789-+() ")
        if set(text) <= phone_chars and digit_count >= 3:
            return "phone"

        return "name_or_company"

    def _select_tree_row_by_id(self, tree: ttk.Treeview, row_id: int) -> bool:
        target = str(row_id)
        for iid in tree.get_children(""):
            values = tree.item(iid, "values")
            if values and str(values[0]).strip() == target:
                tree.selection_set(iid)
                tree.focus(iid)
                tree.see(iid)
                return True
        return False

    def _open_dashboard_search_selection(self, _event=None):
        if not hasattr(self, "dashboard_search_tree"):
            return
        sel = self.dashboard_search_tree.selection()
        if not sel:
            return

        meta = self._dashboard_search_result_map.get(sel[0])
        if not meta:
            return

        target_tab = meta.get("tab")
        target_id = int(meta.get("id", 0))
        if target_id <= 0:
            return

        if target_tab == "customers":
            self.main_notebook.select(self.tab_customers)
            self.refresh_customers()
            self._select_tree_row_by_id(self.customer_tree, target_id)
            self._set_selected_customer(target_id)
        elif target_tab == "trucks":
            self.main_notebook.select(self.tab_trucks)
            self.refresh_trucks()
            self._select_tree_row_by_id(self.truck_tree, target_id)
        elif target_tab == "contracts":
            self.main_notebook.select(self.tab_contracts)
            self.refresh_contracts()
            self._select_tree_row_by_id(self.contract_tree, target_id)

    @trace
    def refresh_dashboard(self):
        if not hasattr(self, "dash_active_contracts_var"):
            return

        as_of_date = today()
        month_start = date(as_of_date.year, as_of_date.month, 1)
        next_y, next_m = add_months(as_of_date.year, as_of_date.month, 1)
        month_end = date(next_y, next_m, 1) - timedelta(days=1)

        contracts = self.db.get_active_contracts_for_dashboard()

        active_count = len(contracts)
        expected_month = 0.0
        total_outstanding = 0.0
        overdue_30_count = 0

        for r in contracts:
            start_d = parse_ymd(r["start_date"])
            if not start_d:
                continue

            end_d = parse_ymd(r["end_date"]) if r["end_date"] else None
            if start_d <= month_end and (end_d is None or end_d >= month_start):
                expected_month += float(r["monthly_rate"])

            outstanding = self._get_contract_outstanding_as_of(int(r["contract_id"]), as_of_date)
            total_outstanding += outstanding

            if outstanding > 0.01:
                paid_total = self.db.get_paid_total_for_contract_as_of(int(r["contract_id"]), as_of_date.isoformat())

                rate = float(r["monthly_rate"])
                paid_months = int(paid_total // rate) if rate > 0 else 0
                due_y, due_m = add_months(start_d.year, start_d.month, paid_months)
                next_y2, next_m2 = add_months(due_y, due_m, 1)
                last_day = (date(next_y2, next_m2, 1) - timedelta(days=1)).day
                due_day = min(start_d.day, last_day)
                oldest_due = date(due_y, due_m, due_day)

                if oldest_due <= (as_of_date - timedelta(days=30)):
                    overdue_30_count += 1

        self.dash_active_contracts_var.set(str(active_count))
        self.dash_expected_month_var.set(f"${expected_month:.2f}")
        self.dash_total_outstanding_var.set(f"${total_outstanding:.2f}")
        self.dash_overdue_30_var.set(str(overdue_30_count))

    def _set_startup_fullscreen(self):
        try:
            self.state("zoomed")
        except Exception as e:
            logger.debug(f"Failed to maximize window with zoomed state: {e}")
            try:
                self.attributes("-fullscreen", True)
                self.bind("<Escape>", lambda _e: self.attributes("-fullscreen", False))
            except Exception as e2:
                logger.warning(f"Failed to set fullscreen mode: {e2}")

    def _open_overdue_tab_from_dashboard(self):
        self.main_notebook.select(self.tab_billing)
        if hasattr(self, "billing_notebook") and hasattr(self, "sub_overdue"):
            self.billing_notebook.select(self.sub_overdue)
        self.refresh_overdue()

    def _configure_ui_rendering(self):
        try:
            self.tk.call("tk", "scaling", self.winfo_fpixels("1i") / 72.0)
        except Exception as e:
            logger.warning(f"Failed to configure TK scaling: {e}")

        base_font = FONTS["base"]
        heading_font = FONTS["heading"]
        self.option_add("*Font", base_font)
        self.option_add("*TCombobox*Listbox*Font", base_font)
        style = ttk.Style(self)
        style.configure(".", font=base_font)
        style.configure("TNotebook.Tab", font=base_font, padding=(24, 14, 24, 14), anchor="center")
        style.configure("TNotebook", tabmargins=(8, 4, 8, 0))
        style.configure("MainTabs.TNotebook", tabmargins=(8, 4, 8, 0), borderwidth=2, relief="solid")
        style.configure("MainTabs.TNotebook.Tab", font=base_font, padding=(24, 14, 24, 14), borderwidth=1)
        style.map(
            "MainTabs.TNotebook.Tab",
            background=[("selected", "#ffffff"), ("active", "#f1f5fb"), ("!selected", "#e6ebf2")],
            foreground=[("selected", "#111111"), ("!selected", "#333333")],
        )
        style.configure("BillingTabs.TNotebook", tabmargins=(6, 4, 6, 0), borderwidth=2, relief="solid")
        style.configure("BillingTabs.TNotebook.Tab", font=base_font, padding=(20, 12, 20, 12), borderwidth=1)
        style.map(
            "BillingTabs.TNotebook.Tab",
            background=[("selected", "#ffffff"), ("active", "#f1f5fb"), ("!selected", "#e6ebf2")],
            foreground=[("selected", "#111111"), ("!selected", "#333333")],
        )
        style.configure("TEntry", font=base_font, padding=(6, 6, 6, 6))
        style.configure("TCombobox", font=base_font, padding=(6, 4, 6, 4))
        style.configure("TButton", font=base_font, padding=(12, 8))
        style.configure("TLabelframe.Label", font=heading_font)
        style.configure("Treeview", font=base_font, rowheight=TREE_ROW_HEIGHT)
        style.configure("Treeview.Heading", font=heading_font, padding=(8, 8, 8, 8))
        style.configure("Billing.Treeview", font=(base_font[0], base_font[1] + 1), rowheight=max(TREE_ROW_HEIGHT + 2, 46))
        style.configure("Billing.Treeview.Heading", font=(heading_font[0], heading_font[1] + 1, "bold"), padding=(10, 10, 10, 10))
        style.configure("BillingControls.TLabelframe", borderwidth=2, relief="solid")
        style.configure("BillingControls.TLabelframe.Label", font=(heading_font[0], heading_font[1], "bold"))
        style.configure("BillingAction.TFrame", borderwidth=2, relief="solid")
        style.map(
            "Treeview",
            foreground=[("selected", SELECTION_FG)],
            background=[("selected", SELECTION_BG)],
        )
        # Warning button style for delete operations
        style.configure("Warning.TButton", font=(base_font[0], base_font[1], "bold"),
                       padding=(14, 10), foreground=DELETE_BUTTON_BG)
        style.map("Warning.TButton",
                 foreground=[("active", "#bf360c"), ("pressed", "#a52714")])
        # Prominent green button used for Record Payment
        style.configure("Payment.TButton", font=(base_font[0], base_font[1] + 1, "bold"),
                       padding=(18, 12), foreground="#2e7d32")
        style.map("Payment.TButton",
                 foreground=[("active", "#1b5e20"), ("pressed", "#1b5e20")])
        style.configure("CreateContract.TButton", font=(base_font[0], base_font[1] + 2, "bold"),
                   padding=(20, 12), foreground="#2e7d32")
        style.map("CreateContract.TButton",
             foreground=[("active", "#1b5e20"), ("pressed", "#1b5e20")])
        style.configure("ViewTrucks.TButton", font=(base_font[0], base_font[1] + 6, "bold"),
                   padding=(26, 24), foreground="#2e7d32")
        style.map("ViewTrucks.TButton",
             foreground=[("active", "#1b5e20"), ("pressed", "#1b5e20")])

    def _init_tree_striping(self, tree: ttk.Treeview):
        tree.tag_configure("row_even", background=TREE_ALT_ROW_COLORS[0])
        tree.tag_configure("row_odd", background=TREE_ALT_ROW_COLORS[1])
        tree.tag_configure("bal_zero", foreground="#2e7d32")
        tree.tag_configure("bal_no_contract", foreground="#b58900")
        tree.tag_configure("bal_due", foreground="#b00020")

    def _row_stripe_tag(self, index: int) -> str:
        return "row_even" if index % 2 == 0 else "row_odd"
    
    def _status_badge(self, status: str) -> str:
        """Add colored emoji badge to status text for easier visual recognition."""
        status_upper = status.upper()
        if status_upper == "PAID":
            return "🟢 " + status
        elif status_upper in ("DUE", "OUTSTANDING"):
            return "🟡 " + status
        elif status_upper == "OVERDUE":
            return "🔴 " + status
        elif status_upper == "ACTIVE":
            return "🟢 " + status
        elif status_upper == "INACTIVE":
            return "⚫ " + status
        return status

    def _outstanding_tag_from_amount(self, amount: float) -> str:
        rounded_amount = round(float(amount), 2)
        return "bal_zero" if rounded_amount == 0.0 else "bal_due"

    def _outstanding_tag_from_text(self, value: str) -> str:
        text = normalize_whitespace(value).upper()
        if text == "NO CONTRACT":
            return "bal_no_contract"
        numeric_text = text.replace("$", "").replace(",", "")
        try:
            return self._outstanding_tag_from_amount(float(numeric_text))
        except ValueError:
            return "bal_due"

    def _show_invalid(self, message: str):
        messagebox.showerror("Invalid input", message)

    def _make_searchable_combo(self, combo: ttk.Combobox):
        """Allow typing to filter a Combobox's dropdown list."""
        combo.configure(state="normal")
        combo._search_all_values = list(combo["values"])

        def _on_key(event):
            # Leave navigation / selection keys alone
            if event.keysym in ("Return", "KP_Enter", "Escape", "Tab",
                                "Up", "Down", "Left", "Right"):
                return
            typed = combo.get().strip().lower()
            all_vals = getattr(combo, "_search_all_values", list(combo["values"]))
            filtered = [v for v in all_vals if typed in v.lower()] if typed else all_vals
            combo["values"] = filtered

        def _on_focus_out(event):
            val = combo.get().strip()
            all_vals = getattr(combo, "_search_all_values", list(combo["values"]))
            if val and val not in all_vals:
                # Clear invalid free-text so ID resolution doesn't silently fail
                combo.set("")
                combo["values"] = all_vals

        combo.bind("<KeyRelease>", _on_key)
        combo.bind("<FocusOut>", _on_focus_out)

    def _language_maps(self):
        """Return language mapping dictionaries (imported from language_map.py)."""
        return EN_TO_ZH, ZH_TO_EN

    def _translate_widget_tree(self, root: tk.Widget, mapping: dict[str, str]):
        for child in root.winfo_children():
            try:
                text_value = child.cget("text")
            except Exception as e:
                logger.debug(f"Failed to get text from widget {child}: {e}")
                text_value = None
            if isinstance(text_value, str) and text_value in mapping:
                try:
                    child.configure(text=mapping[text_value])
                except Exception as e:
                    logger.warning(f"Failed to update widget text from {text_value}: {e}")
            self._translate_widget_tree(child, mapping)

    def _apply_tree_headings_language(self):
        if self.current_language == "zh":
            customer_headings = {"id": "编号", "name": "姓名", "phone": "电话", "company": "公司", "notes": "备注", "outstanding": "欠款", "trucks": "车辆数"}
            truck_headings = {"id": "编号", "plate": "车牌", "state": "州", "make": "品牌", "model": "型号", "customer": "客户", "outstanding": "欠款"}
            contract_headings = {"contract_id": "合同编号", "status": "状态", "customer": "客户", "scope": "车牌", "rate": "费率", "start": "开始", "end": "结束", "outstanding": "欠款"}
            invoice_headings = {"contract_id": "", "customer": "客户", "scope": "车牌", "rate": "费率", "start": "开始", "end": "结束", "months": "累计月数", "expected": "应收", "paid": "已付", "balance": "余额", "status": "状态"}
            overdue_headings = {"month": "月份", "date": "日期", "invoice_id": "合同编号", "customer": "客户", "scope": "范围", "amount": "金额", "paid": "已付", "balance": "余额"}
        else:
            customer_headings = {"id": "ID", "name": "Name", "phone": "Phone", "company": "Company", "notes": "Notes", "outstanding": "Outstanding", "trucks": "Trucks Parked"}
            truck_headings = {"id": "ID", "plate": "Plate", "state": "State", "make": "Make", "model": "Model", "customer": "Customer", "outstanding": "Outstanding"}
            contract_headings = {"contract_id": "Contract ID", "status": "Status", "customer": "Customer", "scope": "Plate", "rate": "Rate", "start": "Start", "end": "End", "outstanding": "Outstanding"}
            invoice_headings = {"contract_id": "", "customer": "Customer", "scope": "Plate", "rate": "Rate", "start": "Start", "end": "End", "months": "Elapsed Months", "expected": "Expected", "paid": "Paid", "balance": "Outstanding", "status": "Status"}
            overdue_headings = {"month": "Month", "date": "Date", "invoice_id": "Contract ID", "customer": "Customer", "scope": "Scope", "amount": "Amount", "paid": "Paid", "balance": "Balance"}

        def apply_headings(tree: ttk.Treeview, headings: dict[str, str]):
            available = set(tree["columns"])
            for key, val in headings.items():
                if key in available:
                    tree.heading(key, text=val)

        apply_headings(self.customer_tree, customer_headings)
        apply_headings(self.truck_tree, truck_headings)
        apply_headings(self.contract_tree, contract_headings)
        apply_headings(self.invoice_tree, invoice_headings)
        if hasattr(self, "overdue_tree"):
            apply_headings(self.overdue_tree, overdue_headings)

    def _set_language(self, language: str):
        en_to_zh, zh_to_en = self._language_maps()
        if language not in ("en", "zh"):
            return

        mapping = en_to_zh if language == "zh" else zh_to_en
        self.current_language = language

        self._translate_widget_tree(self, mapping)
        self._apply_tree_headings_language()

        if hasattr(self, "main_notebook"):
            self.main_notebook.tab(self.tab_dashboard, text=("📈 仪表盘" if language == "zh" else "📈 Dashboard"))
            self.main_notebook.tab(self.tab_customers, text=("👥 客户" if language == "zh" else "👥 Customers"))
            self.main_notebook.tab(self.tab_trucks, text=("🚚 卡车" if language == "zh" else "🚚 Trucks"))
            self.main_notebook.tab(self.tab_contracts, text=("📝 合同" if language == "zh" else "📝 Contracts"))
            self.main_notebook.tab(self.tab_billing, text=("💵 账务" if language == "zh" else "💵 Billing"))
            self.main_notebook.tab(self.tab_histories, text=("🕑 历史记录" if language == "zh" else "🕑 Histories"))
        if hasattr(self, "billing_notebook"):
            self.billing_notebook.tab(self.sub_invoices, text=("🧾 发票与收款" if language == "zh" else "🧾 Invoices & Payments"))
            self.billing_notebook.tab(self.sub_statement, text=("📊 月度报表" if language == "zh" else "📊 Monthly Statement"))
            self.billing_notebook.tab(self.sub_overdue, text=("⏰ 逾期" if language == "zh" else "⏰ Overdue"))

        selector_value = "中文" if language == "zh" else "EN"
        if hasattr(self, "language_selectors"):
            for selector in list(self.language_selectors):
                if not selector.winfo_exists():
                    self.language_selectors.remove(selector)
                    continue
                if selector.get().strip() != selector_value:
                    selector.set(selector_value)

        self._apply_menu_language(language)
        self.title("长生 - 卡车停车场管理" if language == "zh" else "Changsheng - Truck Lot Tracker")

    def _apply_menu_language(self, language: str):
        """Explicitly retranslate all tk.Menu items (cannot be reached by widget-tree walk)."""
        zh = language == "zh"

        if hasattr(self, "customer_menu"):
            self.customer_menu.entryconfigure(0, label=("查看账本" if zh else "View Ledger"))
            # index 1 = separator
            self.customer_menu.entryconfigure(2, label=("生成PDF发票" if zh else "Generate PDF Invoice"))
            # index 3 = separator
            self.customer_menu.entryconfigure(4, label=("删除选中" if zh else "Delete Selected"))
            # index 5 = separator
            self.customer_menu.entryconfigure(6, label=("刷新" if zh else "Refresh"))

        if hasattr(self, "truck_menu"):
            self.truck_menu.entryconfigure(0, label=("查看合同历史" if zh else "View Contract History"))
            # index 1 = separator
            self.truck_menu.entryconfigure(2, label=("删除选中" if zh else "Delete Selected"))
            # index 3 = separator
            self.truck_menu.entryconfigure(4, label=("刷新" if zh else "Refresh"))

        if hasattr(self, "contract_menu"):
            self.contract_menu.entryconfigure(0, label=("查看付款历史" if zh else "View Payment History"))
            # index 1 = separator
            self.contract_menu.entryconfigure(2, label=("编辑合同" if zh else "Edit Contract"))
            self.contract_menu.entryconfigure(3, label=("切换启用/停用" if zh else "Toggle Active/Inactive"))
            self.contract_menu.entryconfigure(4, label=("删除选中" if zh else "Delete Selected"))
            # index 5 = separator
            self.contract_menu.entryconfigure(6, label=("刷新" if zh else "Refresh"))

        if hasattr(self, "invoice_menu"):
            self.invoice_menu.entryconfigure(0, label=("填写收款表单" if zh else "Fill Payment Form"))
            self.invoice_menu.entryconfigure(1, label=("生成PDF发票" if zh else "Generate PDF Invoice"))
            # index 2 = separator
            self.invoice_menu.entryconfigure(3, label=("重置付款" if zh else "Reset Payments"))
            # index 4 = separator
            self.invoice_menu.entryconfigure(5, label=("重新计算" if zh else "Recalculate"))

        if hasattr(self, "overdue_menu"):
            self.overdue_menu.entryconfigure(0, label=("记录收款" if zh else "Record Payment"))
            self.overdue_menu.entryconfigure(1, label=("生成PDF发票" if zh else "Generate PDF Invoice"))
            # index 2 = separator
            self.overdue_menu.entryconfigure(3, label=("刷新" if zh else "Refresh"))

    def _on_language_changed(self, _event=None):
        if _event is not None and hasattr(_event, "widget") and _event.widget:
            selection = _event.widget.get().strip()
        elif self.language_selectors:
            selection = self.language_selectors[0].get().strip()
        else:
            selection = "EN"
        self._set_language("zh" if selection == "中文" else "en")

    def _create_language_selector(self, parent: tk.Misc, width: int = 6) -> ttk.Combobox:
        selector = ttk.Combobox(parent, state="readonly", values=["EN", "中文"], width=width)
        selector.set("中文" if self.current_language == "zh" else "EN")
        selector.bind("<<ComboboxSelected>>", self._on_language_changed)
        self.language_selectors.append(selector)
        return selector

    # ---------------------------
    # Customers tab
    # ---------------------------
    def _clear_customer_search(self):
        self.customer_search.delete(0, tk.END)
        self.refresh_customers()

    def _on_customer_tree_select(self, _event=None):
        self._sync_selected_customer_to_forms()
        self._update_view_trucks_button_state()

    def _update_view_trucks_button_state(self):
        if not hasattr(self, "view_trucks_btn"):
            return
        has_selection = bool(self.customer_tree.selection()) if hasattr(self, "customer_tree") else False
        self.view_trucks_btn.configure(state=("normal" if has_selection else "disabled"))

    def _view_selected_customer_trucks(self):
        sel = self.customer_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a customer row first.")
            self._update_view_trucks_button_state()
            return

        values = self.customer_tree.item(sel[0], "values")
        if not values:
            return

        customer_id = int(values[0])
        customer_name = str(values[1])

        self.main_notebook.select(self.tab_trucks)
        self.truck_search.delete(0, tk.END)
        self.truck_search.insert(0, customer_name)
        self.truck_search.focus_set()
        self.truck_search.icursor(tk.END)
        self._sync_search_boxes_from_truck_search()
        self._truck_search_mode = "customer_name"
        self._truck_filter_customer_id = customer_id
        self.refresh_trucks()

        if hasattr(self, "truck_customer_combo"):
            self._set_combo_by_customer_id(self.truck_customer_combo, customer_id)

        truck_rows = self.truck_tree.get_children("")
        if truck_rows:
            first_iid = truck_rows[0]
            self.truck_tree.selection_set(first_iid)
            self.truck_tree.focus(first_iid)
            self.truck_tree.see(first_iid)
        else:
            messagebox.showinfo("No Trucks", f"No trucks found for customer '{customer_name}'.")

    def _ensure_history_log_exists(self) -> None:
        try:
            with open(HISTORY_LOG_FILE, "a+", encoding="utf-8") as f:
                f.seek(0, 2)
                if f.tell() == 0:
                    f.write("# Truck Lot History Log (auto-created)\n")
        except Exception as exc:
            logger.warning(f"Failed to ensure history log exists: {exc}")

    def _load_app_settings(self) -> dict:
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_app_settings(self) -> None:
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._app_settings, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning(f"Failed to save app settings: {exc}")

    def _get_last_backup_dir(self) -> str | None:
        value = self._app_settings.get("last_backup_dir")
        return value if isinstance(value, str) and value else None

    def _set_last_backup_dir(self, file_path: str) -> None:
        try:
            last_dir = str(file_path).rsplit("/", 1)[0].rsplit("\\", 1)[0]
        except Exception:
            last_dir = None
        if last_dir:
            self._app_settings["last_backup_dir"] = last_dir
            self._save_app_settings()

    def _get_last_backup_date(self) -> date | None:
        self._ensure_history_log_exists()
        try:
            with open(HISTORY_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except Exception as exc:
            logger.warning(f"Failed to read history log for backup check: {exc}")
            return None

        for line in reversed(lines):
            if "BACKUP_DB" not in line:
                continue
            try:
                timestamp_str = line.split("]", 1)[0].lstrip("[")
                backup_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                backup_date = backup_dt.date()
                logger.info(f"Last backup date parsed: {backup_date.isoformat()}")
                return backup_date
            except Exception:
                continue
        return None

    def _prompt_backup_on_startup(self):
        last_backup = self._get_last_backup_date()
        if last_backup:
            days_since = (today() - last_backup).days
            msg = f"距离上次备份已经过去 {days_since} 天。\n现在备份数据库吗？"
            logger.info(f"Startup backup reminder: {days_since} days since last backup.")
        else:
            msg = "还没有备份记录。\n现在备份数据库吗？"
            logger.info("Startup backup reminder: no previous backup found.")

        do_backup = messagebox.askyesno("备份提示", msg)
        logger.info(f"Startup backup prompt response: {'yes' if do_backup else 'no'}")
        if do_backup:
            self.backup_database()

    def _set_selected_customer(self, customer_id: int):
        # Set on truck tab + contract tab
        if hasattr(self, "truck_customer_combo"):
            self._set_combo_by_customer_id(self.truck_customer_combo, customer_id)
        if hasattr(self, "contract_customer_combo"):
            self._set_combo_by_customer_id(self.contract_customer_combo, customer_id)

    # ---------------------------
    # Trucks tab
    # ---------------------------
    def _clear_truck_search(self):
        self.truck_search.delete(0, tk.END)
        self._sync_search_boxes_from_truck_search()
        self._truck_search_mode = "all"
        self._truck_filter_customer_id = None
        self.refresh_trucks()

    def _on_truck_search_keyrelease(self, _event=None):
        self._sync_search_boxes_from_truck_search()
        self._truck_search_mode = "all"
        self._truck_filter_customer_id = None

    def _sync_search_boxes_from_truck_search(self):
        if not hasattr(self, "truck_search"):
            return
        text = normalize_whitespace(self.truck_search.get())
        if hasattr(self, "contract_search"):
            self.contract_search.delete(0, tk.END)
            self.contract_search.insert(0, text)
        if hasattr(self, "invoice_customer_search"):
            self.invoice_customer_search.delete(0, tk.END)
            self.invoice_customer_search.insert(0, text)

    def _open_truck_customer_picker(self):
        if not hasattr(self, "_customers_cache") or not self._customers_cache:
            self._reload_customer_dropdowns()

        customers = list(getattr(self, "_customers_cache", []))
        def on_select(customer_id: int) -> None:
            self._set_combo_by_customer_id(self.truck_customer_combo, customer_id)
            self.t_notes.focus()

        open_customer_picker(self, customers, normalize_whitespace, on_select)

    @trace
    def view_selected_truck_contract_history(self):
        sel = self.truck_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a truck row first.")
            return

        values = self.truck_tree.item(sel[0], "values")
        if not values:
            messagebox.showerror("Invalid selection", "Could not read selected truck.")
            return

        try:
            truck_id = int(values[0])
        except (ValueError, TypeError):
            messagebox.showerror("Invalid selection", "Selected truck ID is invalid.")
            return

        contract_row = self.db.get_preferred_contract_for_truck(truck_id)
        if not contract_row:
            messagebox.showinfo("No Contract", "No contract was found for this truck.")
            return

        contract_id = int(contract_row["contract_id"])
        rows = self.db.get_contract_payment_history(contract_id)
        status = "ACTIVE" if int(contract_row["is_active"]) == 1 else "INACTIVE"

        scope = str(contract_row["scope"])
        plate = str(contract_row["plate"] or "").strip()
        if plate and scope == "Per-truck":
            scope = f"{scope} ({plate})"

        contract_info = {
            "contract_id": contract_id,
            "status": status,
            "customer": str(contract_row["customer_name"]),
            "scope": scope,
            "rate": f"${float(contract_row['monthly_rate']):.2f}/mo",
            "start": str(contract_row["start_date"]),
            "end": str(contract_row["end_date"] or "—"),
            "outstanding": f"${self._get_contract_outstanding_as_of(contract_id, today()):.2f}",
        }
        show_contract_payment_history(self, contract_info, rows)

    # ---------------------------
    # Contracts tab
    # ---------------------------
    def _on_scope_change(self):
        if self.contract_scope.get() == "customer_level":
            self.contract_truck_combo.configure(state="disabled")
        else:
            self.contract_truck_combo.configure(state="normal")

    def _open_contract_customer_picker(self):
        if not hasattr(self, "_customers_cache") or not self._customers_cache:
            self._reload_customer_dropdowns()

        customers = list(getattr(self, "_customers_cache", []))

        def on_select(customer_id: int) -> None:
            self._set_combo_by_customer_id(self.contract_customer_combo, customer_id)
            self._on_contract_customer_changed()
            self.contract_rate.focus()

        open_customer_picker(self, customers, normalize_whitespace, on_select)

    def _on_contract_customer_changed(self, _event=None):
        if not hasattr(self, "contract_truck_combo"):
            return
        customer_id = self._get_selected_customer_id_from_combo(self.contract_customer_combo)
        self._filter_contract_trucks(customer_id)

    def _clear_contract_search(self):
        if hasattr(self, "contract_search"):
            self.contract_search.delete(0, tk.END)
        if hasattr(self, "truck_search"):
            self.truck_search.delete(0, tk.END)
        if hasattr(self, "invoice_customer_search"):
            self.invoice_customer_search.delete(0, tk.END)
        self._truck_search_mode = "all"
        self._truck_filter_customer_id = None
        self.refresh_contracts()

    def _select_contract_in_invoice_tree(self, contract_id: int) -> bool:
        target = str(contract_id)
        found_iid = None

        for parent_iid in self.invoice_tree.get_children(""):
            for child_iid in self.invoice_tree.get_children(parent_iid):
                values = self.invoice_tree.item(child_iid, "values")
                if values and str(values[0]).strip() == target:
                    self.invoice_tree.item(parent_iid, open=True)
                    self._update_invoice_parent_label(parent_iid)
                    found_iid = child_iid
                    break
            if found_iid:
                break

        if not found_iid:
            for iid in self.invoice_tree.get_children(""):
                values = self.invoice_tree.item(iid, "values")
                if values and str(values[0]).strip() == target:
                    found_iid = iid
                    break

        if not found_iid:
            return False

        self.invoice_tree.selection_set(found_iid)
        self.invoice_tree.focus(found_iid)
        self.invoice_tree.see(found_iid)
        return True

    # ---------------------------
    # Invoices tab
    # ---------------------------
    def _invoice_group_label(self, contract_count: int, is_open: bool) -> str:
        arrow = "▼" if is_open else "▶"
        noun = "Contract" if contract_count == 1 else "Contracts"
        return f"{arrow} {contract_count} {noun}"

    def _update_invoice_parent_label(self, parent_iid: str):
        children_count = len(self.invoice_tree.get_children(parent_iid))
        is_open = bool(self.invoice_tree.item(parent_iid, "open"))
        values = list(self.invoice_tree.item(parent_iid, "values"))
        if not values:
            return
        values[2] = self._invoice_group_label(children_count, is_open)
        self.invoice_tree.item(parent_iid, values=values)

    def _refresh_invoice_parent_labels(self):
        for parent_iid in self.invoice_tree.get_children(""):
            self._update_invoice_parent_label(parent_iid)

    def _apply_invoice_tree_visual_tags(self):
        for parent_index, parent_iid in enumerate(self.invoice_tree.get_children("")):
            parent_values = self.invoice_tree.item(parent_iid, "values")
            if not parent_values:
                continue

            parent_balance = parent_values[9] if len(parent_values) > 9 else ""
            parent_balance_tag = self._outstanding_tag_from_text(str(parent_balance))
            parent_stripe_tag = self._row_stripe_tag(parent_index)
            is_open = bool(self.invoice_tree.item(parent_iid, "open"))
            if is_open:
                self.invoice_tree.item(
                    parent_iid,
                    tags=("invoice_parent_expanded", parent_balance_tag),
                )
            else:
                self.invoice_tree.item(
                    parent_iid,
                    tags=(parent_stripe_tag, parent_balance_tag),
                )

            for child_index, child_iid in enumerate(self.invoice_tree.get_children(parent_iid)):
                child_values = self.invoice_tree.item(child_iid, "values")
                child_balance = child_values[9] if child_values and len(child_values) > 9 else ""
                child_balance_tag = self._outstanding_tag_from_text(str(child_balance))
                child_stripe_tag = "invoice_child_even" if child_index % 2 == 0 else "invoice_child_odd"
                self.invoice_tree.item(child_iid, tags=(child_stripe_tag, child_balance_tag))

    def _on_invoice_tree_open_close(self, _event=None):
        self._refresh_invoice_parent_labels()
        self._apply_invoice_tree_visual_tags()

    def _toggle_invoice_parent_row(self, event: tk.Event):
        row_id = self.invoice_tree.identify_row(event.y)
        if not row_id:
            return
        if self.invoice_tree.parent(row_id):
            return
        is_open = bool(self.invoice_tree.item(row_id, "open"))
        self.invoice_tree.item(row_id, open=not is_open)
        self._update_invoice_parent_label(row_id)
        return "break"

    @trace
    def collapse_all_invoice_groups(self):
        current_selection = self.invoice_tree.selection()
        if current_selection:
            self.invoice_tree.selection_remove(*current_selection)

        for parent_iid in self.invoice_tree.get_children(""):
            self.invoice_tree.item(parent_iid, open=False)
            children_count = len(self.invoice_tree.get_children(parent_iid))
            values = list(self.invoice_tree.item(parent_iid, "values"))
            if values:
                values[0] = self._invoice_group_label(children_count, False)
                self.invoice_tree.item(parent_iid, values=values)

        self.invoice_tree.focus("")

    @trace
    def expand_all_invoice_groups(self):
        for parent_iid in self.invoice_tree.get_children(""):
            self.invoice_tree.item(parent_iid, open=True)
            children_count = len(self.invoice_tree.get_children(parent_iid))
            values = list(self.invoice_tree.item(parent_iid, "values"))
            if values:
                values[0] = self._invoice_group_label(children_count, True)
                self.invoice_tree.item(parent_iid, values=values)

    def _sort_invoice_tree(self, col: str):
        """Sort the invoice treeview by col (customers only); click again to reverse."""
        if getattr(self, "_invoice_sort_col", None) == col:
            self._invoice_sort_rev = not getattr(self, "_invoice_sort_rev", False)
        else:
            self._invoice_sort_col = col
            self._invoice_sort_rev = False

        tree = self.invoice_tree
        numeric_dollar = {"rate", "expected", "paid", "balance"}
        numeric_int    = {"contract_id", "months"}

        def sort_key(iid):
            val = tree.set(iid, col)
            if col in numeric_dollar:
                try:
                    return float(val.replace("$", "").replace(",", "").strip())
                except ValueError:
                    return 0.0
            if col in numeric_int:
                try:
                    return int(val)
                except ValueError:
                    return 0
            return val.lower()

        # Only sort parent (customer) rows; children stay with their parents
        items = list(tree.get_children(""))
        items.sort(key=sort_key, reverse=self._invoice_sort_rev)
        for idx, iid in enumerate(items):
            tree.move(iid, "", idx)

        invoice_headings = {
            "contract_id": "Contract ID",
            "customer": "Customer",
            "scope": "Scope",
            "rate": "Rate",
            "start": "Start",
            "end": "End",
            "months": "Elapsed Months",
            "expected": "Expected",
            "paid": "Paid",
            "balance": "Outstanding",
            "status": "Status",
        }
        for c in tree["columns"]:
            label = invoice_headings.get(c, c)
            if c == col:
                label += " ▼" if self._invoice_sort_rev else " ▲"
            tree.heading(c, text=label)

    @trace
    def generate_invoices(self):
        self.refresh_invoices()
        messagebox.showinfo("Recalculated", "Outstanding balances recalculated for selected date.")

    # ---------------------------
    # Overdue tab
    # ---------------------------
    def _on_overdue_search_keyrelease(self, _event=None):
        self.refresh_overdue()

    def _clear_overdue_search(self):
        if hasattr(self, "overdue_search"):
            self.overdue_search.delete(0, tk.END)
            self.overdue_search.focus_set()
        self.refresh_overdue()

    def _get_selected_overdue_contract_id(self) -> int | None:
        if not hasattr(self, "overdue_tree"):
            return None
        sel = self.overdue_tree.selection()
        if not sel:
            return None
        values = self.overdue_tree.item(sel[0], "values")
        if not values or len(values) < 3:
            return None
        try:
            return int(str(values[2]).strip())
        except (ValueError, TypeError):
            return None

    def _record_payment_for_selected_overdue(self):
        contract_id = self._get_selected_overdue_contract_id()
        if not contract_id:
            messagebox.showwarning("No Selection", "Select an overdue row first.")
            return
        self._open_payment_form_for_contract(contract_id)

    def _generate_invoice_pdf_for_selected_overdue(self):
        contract_id = self._get_selected_overdue_contract_id()
        if not contract_id:
            messagebox.showwarning("No Selection", "Select an overdue row first.")
            return
        customer_id = self.db.get_customer_id_by_contract(contract_id)
        if not customer_id:
            messagebox.showerror("Not found", f"Customer for contract {contract_id} was not found.")
            return
        self._generate_customer_invoice_pdf_for_customer_id(customer_id)

    def _on_billing_tab_changed(self, _event=None):
        if not hasattr(self, "billing_notebook"):
            return
        selected = self.billing_notebook.select()
        if selected == str(self.sub_overdue):
            self.refresh_overdue()
        elif selected == str(self.sub_invoices):
            self._sync_search_boxes_from_truck_search()
            self.refresh_invoices()

    # ---------------------------
    # Shared dropdown reloaders
    # ---------------------------
    def _reload_customer_dropdowns(self):
        customers = self.db.get_customer_dropdown_rows()
        self._customers_cache = [
            Customer(int(r["id"]), r["name"], r["phone"], r["company"]) for r in customers
        ]
        display = [self._fmt_customer(c) for c in self._customers_cache]

        for combo_name in ("truck_customer_combo", "contract_customer_combo"):
            if hasattr(self, combo_name):
                combo = getattr(self, combo_name)
                combo["values"] = display
                combo._search_all_values = display
                # Keep selection if possible
                if display and not combo.get():
                    combo.current(0)

    def _reload_truck_dropdowns(self):
        trucks = self.db.get_truck_dropdown_rows()
        self._trucks_cache = [
            Truck(int(r["id"]), r["plate"], r["state"], r["customer_id"]) for r in trucks
        ]
        if hasattr(self, "contract_truck_combo"):
            customer_id = None
            if hasattr(self, "contract_customer_combo"):
                customer_id = self._get_selected_customer_id_from_combo(self.contract_customer_combo)
            self._filter_contract_trucks(customer_id)

    def _fmt_customer(self, c: Customer) -> str:
        extras = []
        if c.company:
            extras.append(c.company)
        if c.phone:
            extras.append(c.phone)
        tail = f" ({' | '.join(extras)})" if extras else ""
        return f"{c.id}: {c.name}{tail}"

    def _fmt_truck(self, t: Truck) -> str:
        st = f"{t.state} " if t.state else ""
        return f"{t.id}: {t.plate} {st}".strip()

    def _filter_contract_trucks(self, customer_id: int | None) -> None:
        trucks = list(getattr(self, "_trucks_cache", []))
        if customer_id is not None:
            trucks = [t for t in trucks if t.customer_id == customer_id]

        display = [self._fmt_truck(t) for t in trucks]
        current = self.contract_truck_combo.get().strip() if hasattr(self, "contract_truck_combo") else ""
        if hasattr(self, "contract_truck_combo"):
            self.contract_truck_combo["values"] = display
            self.contract_truck_combo._search_all_values = display
            if current not in display:
                if display:
                    self.contract_truck_combo.current(0)
                else:
                    self.contract_truck_combo.set("")

    def _get_selected_customer_id_from_combo(self, combo: ttk.Combobox) -> int | None:
        val = combo.get().strip()
        if not val:
            return None
        all_vals = getattr(combo, "_search_all_values", list(combo["values"]))
        if val not in all_vals:
            return None
        try:
            return int(val.split(":")[0])
        except (ValueError, IndexError):
            return None

    def _get_selected_truck_id_from_combo(self, combo: ttk.Combobox) -> int | None:
        val = combo.get().strip()
        if not val:
            return None
        all_vals = getattr(combo, "_search_all_values", list(combo["values"]))
        if val not in all_vals:
            return None
        try:
            return int(val.split(":")[0])
        except (ValueError, IndexError):
            return None

    def _set_combo_by_customer_id(self, combo: ttk.Combobox, customer_id: int):
        vals = list(combo["values"])
        for i, v in enumerate(vals):
            if v.startswith(f"{customer_id}:"):
                combo.current(i)
                return

    def _on_tab_changed(self, event):
        on_tab_changed_action(
            app=self,
            _event=event,
            tab_has_unsaved_data_cb=self._tab_has_unsaved_data,
        )
        if self.main_notebook.select() == str(self.tab_contracts):
            self._sync_search_boxes_from_truck_search()
            self.refresh_contracts()

    @trace
    def on_close(self):
        try:
            self.db.close()
        except Exception as e:
            logger.warning(f"Failed to close database connection: {e}")
        self.destroy()


if __name__ == "__main__":
    enable_windows_dpi_awareness()
    app = App()
    app.mainloop()