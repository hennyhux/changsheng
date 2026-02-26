from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from data.database_service import DatabaseService
from tabs.billing_tab import build_billing_tab
from tabs.contracts_tab import build_contracts_tab
from tabs.customers_tab import build_customers_tab
from tabs.dashboard_tab import build_dashboard_tab
from tabs.histories_tab import build_histories_tab
from tabs.trucks_tab import build_trucks_tab
from core.config import DB_PATH, WINDOW_HEIGHT, WINDOW_WIDTH, THEME_PALETTES


class StartupLayoutMixin:
    def __init__(self):
        super().__init__()
        self._init_state()
        if not self._init_database():
            return
        self._post_database_bootstrap()
        self._build_layout()
        self._bind_events()
        self._initial_loads()

    def _init_state(self):
        self.current_language = "en"
        self.language_selectors: list[ttk.Combobox] = []
        self.theme_selectors: list[ttk.Combobox] = []
        self.theme_mode = "light"
        self._theme_palette = THEME_PALETTES["light"]
        self.date_entry_cls = getattr(self, "date_entry_cls_default", None)
        self._customer_search_after_id = None
        self._contract_search_after_id = None
        self._truck_search_after_id = None
        self._invoice_search_after_id = None
        self._overdue_search_after_id = None
        self.title("Changsheng - Truck Lot Tracker")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self._set_startup_fullscreen()
        self._configure_ui_rendering()

    def _set_startup_fullscreen(self):
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-fullscreen", True)
                self.bind("<Escape>", lambda _event: self.attributes("-fullscreen", False))
            except Exception:
                return

    def _init_database(self) -> bool:
        try:
            self.db = DatabaseService(DB_PATH)
            return True
        except Exception as exc:
            messagebox.showerror(
                "Database Integrity Error",
                "Integrity checks failed or migration could not be completed.\n\n"
                f"Details:\n{exc}",
            )
            self.destroy()
            return False

    def _post_database_bootstrap(self):
        self._app_settings = self._load_app_settings()
        self.theme_mode = self._normalize_theme_mode(self._app_settings.get("theme_mode", "light"))
        self._ensure_history_log_exists()
        self._log_action = getattr(self, "_log_action_callback", lambda *_args, **_kwargs: None)
        self._openpyxl_module = getattr(self, "_openpyxl_runtime", None)

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top_bar = ttk.Frame(self)
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=4)
        top_bar.columnconfigure(0, weight=1)

        ttk.Label(top_bar, text="Language:").grid(row=0, column=1, sticky="e", padx=(12, 4))
        self.global_lang_selector = self._create_language_selector(top_bar, width=6)
        self.global_lang_selector.grid(row=0, column=2, sticky="e")

        ttk.Label(top_bar, text="Theme:").grid(row=0, column=3, sticky="e", padx=(14, 4))
        self.global_theme_selector = self._create_theme_selector(top_bar, width=8)
        self.global_theme_selector.grid(row=0, column=4, sticky="e")

        notebook = ttk.Notebook(self, style="MainTabs.TNotebook")
        notebook.grid(row=1, column=0, sticky="nsew")
        self.main_notebook = notebook

        self.tab_dashboard = ttk.Frame(notebook)
        self.tab_customers = ttk.Frame(notebook)
        self.tab_trucks = ttk.Frame(notebook)
        self.tab_contracts = ttk.Frame(notebook)
        self.tab_billing = ttk.Frame(notebook)
        self.tab_histories = ttk.Frame(notebook)

        notebook.add(self.tab_dashboard, text="📈 Dashboard")
        notebook.add(self.tab_customers, text="👥 Customers")
        notebook.add(self.tab_trucks, text="🚚 Trucks")
        notebook.add(self.tab_contracts, text="📝 Contracts")
        notebook.add(self.tab_billing, text="💵 Billing")
        notebook.add(self.tab_histories, text="🕑 Histories")

        build_dashboard_tab(self, self.tab_dashboard)
        build_customers_tab(self, self.tab_customers)
        build_trucks_tab(self, self.tab_trucks)
        build_contracts_tab(self, self.tab_contracts)
        build_billing_tab(self, self.tab_billing)
        build_histories_tab(self, self.tab_histories)

        self._setup_right_click_menus()
        self._set_theme(self.theme_mode, persist=False)

    def _bind_events(self):
        self.main_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._bind_global_shortcuts()
        self.after(100, self._focus_current_tab_primary_input)

    def _initial_loads(self):
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
