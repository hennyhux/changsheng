from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from core.app_logging import get_app_logger
from core.config import (
    DELETE_BUTTON_BG,
    FONTS,
    SELECTION_BG,
    SELECTION_FG,
    THEME_PALETTES,
    TREE_ROW_HEIGHT,
)
from data.language_map import EN_TO_ZH, ZH_TO_EN
from ui.combo_helpers import make_searchable_combo
from utils.validation import normalize_whitespace

logger = get_app_logger()


class ThemeLanguageMixin:
    def _configure_ui_rendering(self):
        try:
            self.tk.call("tk", "scaling", self.winfo_fpixels("1i") / 72.0)
        except Exception as e:
            logger.warning(f"Failed to configure TK scaling: {e}")

        palette = THEME_PALETTES.get(self.theme_mode, THEME_PALETTES["light"])
        self._theme_palette = palette

        base_font = FONTS["base"]
        heading_font = FONTS["heading"]
        self.option_add("*Font", base_font)
        self.option_add("*TCombobox*Listbox*Font", base_font)
        self.option_add("*TCombobox*Listbox*Background", palette["entry_bg"])
        self.option_add("*TCombobox*Listbox*Foreground", palette["entry_text"])
        self.option_add("*TCombobox*Listbox*selectBackground", SELECTION_BG)
        self.option_add("*TCombobox*Listbox*selectForeground", SELECTION_FG)
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", font=base_font, background=palette["surface_bg"], foreground=palette["text"])
        style.configure("TFrame", background=palette["surface_bg"])
        style.configure("TLabel", background=palette["surface_bg"], foreground=palette["text"])
        style.configure("TLabelframe", background=palette["surface_bg"], bordercolor=palette["border"])
        style.configure("TLabelframe.Label", font=heading_font, background=palette["surface_bg"], foreground=palette["text"])
        style.configure("TNotebook.Tab", font=base_font, padding=(24, 14, 24, 14), anchor="center")
        style.configure("TNotebook", tabmargins=(8, 4, 8, 0), background=palette["surface_bg"], bordercolor=palette["border"])
        style.configure("MainTabs.TNotebook", tabmargins=(8, 4, 8, 0), borderwidth=2, relief="solid", background=palette["surface_bg"], bordercolor=palette["border"])
        style.configure("MainTabs.TNotebook.Tab", font=base_font, padding=(24, 14, 24, 14), borderwidth=1)
        style.map(
            "MainTabs.TNotebook.Tab",
            background=[("selected", palette["tab_selected_bg"]), ("active", palette["tab_active_bg"]), ("!selected", palette["tab_idle_bg"])],
            foreground=[("selected", palette["tab_selected_text"]), ("!selected", palette["tab_idle_text"])],
        )
        style.configure("BillingTabs.TNotebook", tabmargins=(6, 4, 6, 0), borderwidth=2, relief="solid", background=palette["surface_bg"], bordercolor=palette["border"])
        style.configure("BillingTabs.TNotebook.Tab", font=base_font, padding=(20, 12, 20, 12), borderwidth=1)
        style.map(
            "BillingTabs.TNotebook.Tab",
            background=[("selected", palette["tab_selected_bg"]), ("active", palette["tab_active_bg"]), ("!selected", palette["tab_idle_bg"])],
            foreground=[("selected", palette["tab_selected_text"]), ("!selected", palette["tab_idle_text"])],
        )
        style.configure("TEntry", font=base_font, padding=(6, 6, 6, 6), fieldbackground=palette["entry_bg"], foreground=palette["entry_text"])
        style.map("TEntry", fieldbackground=[("disabled", palette["entry_disabled_bg"]), ("!disabled", palette["entry_bg"])])
        style.configure("TCombobox", font=base_font, padding=(6, 4, 6, 4), fieldbackground=palette["entry_bg"], foreground=palette["entry_text"], background=palette["panel_bg"])
        style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", palette["entry_bg"]),
                ("disabled", palette["entry_disabled_bg"]),
                ("!disabled", palette["entry_bg"]),
            ],
            foreground=[
                ("readonly", palette["entry_text"]),
                ("disabled", palette["muted_text"]),
                ("!disabled", palette["entry_text"]),
            ],
            selectbackground=[("readonly", SELECTION_BG), ("!readonly", SELECTION_BG)],
            selectforeground=[("readonly", SELECTION_FG), ("!readonly", SELECTION_FG)],
            arrowcolor=[("disabled", palette["muted_text"]), ("!disabled", palette["text"])],
        )
        style.configure("TButton", font=base_font, padding=(12, 8), background=palette["panel_bg"], foreground=palette["text"])
        style.map("TButton", background=[("active", palette["tab_active_bg"]), ("pressed", palette["tab_selected_bg"])], foreground=[("disabled", palette["muted_text"]), ("!disabled", palette["text"])])
        style.configure("Treeview", font=base_font, rowheight=TREE_ROW_HEIGHT, background=palette["tree_bg"], fieldbackground=palette["tree_bg"], foreground=palette["tree_fg"])
        style.configure("Treeview.Heading", font=heading_font, padding=(8, 8, 8, 8), background=palette["tree_heading_bg"], foreground=palette["tree_heading_fg"])
        style.map("Treeview.Heading", background=[("active", palette["tab_active_bg"])], foreground=[("active", palette["tab_selected_text"])])
        style.configure("Billing.Treeview", font=(base_font[0], base_font[1] + 1), rowheight=max(TREE_ROW_HEIGHT + 2, 46))
        style.configure("Billing.Treeview.Heading", font=(heading_font[0], heading_font[1] + 1, "bold"), padding=(10, 10, 10, 10))
        style.configure("BillingControls.TLabelframe", borderwidth=2, relief="solid", background=palette["surface_bg"], bordercolor=palette["border"])
        style.configure("BillingControls.TLabelframe.Label", font=(heading_font[0], heading_font[1], "bold"), background=palette["surface_bg"], foreground=palette["text"])
        style.configure("BillingAction.TFrame", borderwidth=2, relief="solid", background=palette["surface_bg"], bordercolor=palette["border"])
        style.map(
            "Treeview",
            foreground=[("selected", SELECTION_FG)],
            background=[("selected", SELECTION_BG)],
        )
        style.configure("Warning.TButton", font=(base_font[0], base_font[1], "bold"),
                       padding=(14, 10), foreground=DELETE_BUTTON_BG)
        style.map("Warning.TButton",
                 foreground=[("active", "#bf360c"), ("pressed", "#a52714")])
        style.configure("Payment.TButton", font=(base_font[0], base_font[1] + 1, "bold"),
                       padding=(18, 12), foreground=palette["payment_button_fg"])
        style.map("Payment.TButton",
                 foreground=[("active", palette["payment_button_active_fg"]), ("pressed", palette["payment_button_active_fg"])])
        style.configure("CreateContract.TButton", font=(base_font[0], base_font[1] + 2, "bold"),
                   padding=(20, 12), foreground=palette["create_button_fg"])
        style.map("CreateContract.TButton",
             foreground=[("active", palette["create_button_active_fg"]), ("pressed", palette["create_button_active_fg"])])
        style.configure("ViewTrucks.TButton", font=(base_font[0], base_font[1] + 6, "bold"),
                   padding=(26, 24), foreground=palette["view_trucks_button_fg"])
        style.map("ViewTrucks.TButton",
             foreground=[("active", palette["view_trucks_button_active_fg"]), ("pressed", palette["view_trucks_button_active_fg"])])

    def _normalize_theme_mode(self, value: str) -> str:
        candidate = str(value or "light").strip().lower()
        return candidate if candidate in THEME_PALETTES else "light"

    def _set_theme(self, mode: str, persist: bool = True):
        new_mode = self._normalize_theme_mode(mode)
        self.theme_mode = new_mode
        self._theme_palette = THEME_PALETTES[new_mode]
        self._configure_ui_rendering()
        self.configure(background=self._theme_palette["root_bg"])
        self._apply_theme_to_widget_tree(self)
        self._refresh_tree_theme_tags()
        self._apply_menu_theme()
        if hasattr(self, "_apply_invoice_tree_visual_tags"):
            self._apply_invoice_tree_visual_tags()
        if persist and hasattr(self, "_app_settings"):
            self._app_settings["theme_mode"] = new_mode
            self._save_app_settings()

        if hasattr(self, "theme_selectors"):
            selector_value = "Dark" if new_mode == "dark" else "Light"
            for selector in list(self.theme_selectors):
                if not selector.winfo_exists():
                    self.theme_selectors.remove(selector)
                    continue
                if selector.get().strip() != selector_value:
                    selector.set(selector_value)

    def _apply_theme_to_widget_tree(self, root: tk.Widget):
        palette = self._theme_palette
        try:
            if isinstance(root, tk.Text):
                root.configure(bg=palette["text_widget_bg"], fg=palette["text_widget_fg"], insertbackground=palette["text_widget_fg"])
            elif isinstance(root, ttk.Label) and self.theme_mode == "dark":
                try:
                    fg = str(root.cget("foreground")).strip().lower()
                except Exception:
                    fg = ""
                if fg in {"#777777", "#666666", "#888888", "#999999", "#aaaaaa", "gray", "grey"}:
                    root.configure(foreground=palette["muted_text"])
            elif isinstance(root, (tk.Frame, tk.Label, tk.LabelFrame, tk.Toplevel, tk.Tk)) and not isinstance(root, ttk.Widget):
                config_kwargs = {"bg": palette["surface_bg"]}
                try:
                    root.cget("fg")
                    config_kwargs["fg"] = palette["text"]
                except Exception:
                    pass
                root.configure(**config_kwargs)
        except Exception as exc:
            logger.debug(f"Failed to apply theme on widget {root}: {exc}")

        for child in root.winfo_children():
            self._apply_theme_to_widget_tree(child)

    def _apply_menu_theme(self):
        palette = self._theme_palette
        for menu_name in ("customer_menu", "truck_menu", "contract_menu", "invoice_menu", "overdue_menu"):
            if not hasattr(self, menu_name):
                continue
            menu_widget = getattr(self, menu_name)
            try:
                menu_widget.configure(
                    background=palette["menu_bg"],
                    foreground=palette["menu_fg"],
                    activebackground=palette["menu_active_bg"],
                    activeforeground=palette["menu_active_fg"],
                )
            except Exception as exc:
                logger.debug(f"Failed to apply menu theme on {menu_name}: {exc}")

    def _refresh_tree_theme_tags(self):
        for tree_name in ("customer_tree", "truck_tree", "contract_tree", "invoice_tree", "overdue_tree"):
            if hasattr(self, tree_name):
                self._init_tree_striping(getattr(self, tree_name))

        if hasattr(self, "invoice_tree"):
            palette = self._theme_palette
            self.invoice_tree.tag_configure("invoice_parent_expanded", background=palette["invoice_parent_expanded"])
            self.invoice_tree.tag_configure("invoice_child_even", background=palette["invoice_child_even"])
            self.invoice_tree.tag_configure("invoice_child_odd", background=palette["invoice_child_odd"])

    def _init_tree_striping(self, tree: ttk.Treeview):
        palette = self._theme_palette
        tree.tag_configure("row_even", background=palette["stripe_even"])
        tree.tag_configure("row_odd", background=palette["stripe_odd"])
        tree.tag_configure("bal_zero", foreground=palette["status_bal_zero"], font=FONTS["tree_bold"])
        tree.tag_configure("bal_no_contract", foreground=palette["status_bal_no_contract"], font=FONTS["tree_bold"])
        tree.tag_configure("bal_due", foreground=palette["status_bal_due"], font=FONTS["tree_bold"])

    def _row_stripe_tag(self, index: int) -> str:
        return "row_even" if index % 2 == 0 else "row_odd"

    def _status_badge(self, status: str) -> str:
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
        make_searchable_combo(combo)

    def _language_maps(self):
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
        zh = language == "zh"

        if hasattr(self, "customer_menu"):
            self.customer_menu.entryconfigure(0, label=("查看账本" if zh else "View Ledger"))
            self.customer_menu.entryconfigure(2, label=("生成PDF发票" if zh else "Generate PDF Invoice"))
            self.customer_menu.entryconfigure(4, label=("删除选中" if zh else "Delete Selected"))
            self.customer_menu.entryconfigure(6, label=("刷新" if zh else "Refresh"))

        if hasattr(self, "truck_menu"):
            self.truck_menu.entryconfigure(0, label=("查看合同历史" if zh else "View Contract History"))
            self.truck_menu.entryconfigure(2, label=("删除选中" if zh else "Delete Selected"))
            self.truck_menu.entryconfigure(4, label=("刷新" if zh else "Refresh"))

        if hasattr(self, "contract_menu"):
            self.contract_menu.entryconfigure(0, label=("查看付款历史" if zh else "View Payment History"))
            self.contract_menu.entryconfigure(2, label=("编辑合同" if zh else "Edit Contract"))
            self.contract_menu.entryconfigure(3, label=("切换启用/停用" if zh else "Toggle Active/Inactive"))
            self.contract_menu.entryconfigure(4, label=("删除选中" if zh else "Delete Selected"))
            self.contract_menu.entryconfigure(6, label=("刷新" if zh else "Refresh"))

        if hasattr(self, "invoice_menu"):
            self.invoice_menu.entryconfigure(0, label=("填写收款表单" if zh else "Fill Payment Form"))
            self.invoice_menu.entryconfigure(1, label=("生成PDF发票" if zh else "Generate PDF Invoice"))
            self.invoice_menu.entryconfigure(3, label=("重置付款" if zh else "Reset Payments"))
            self.invoice_menu.entryconfigure(5, label=("重新计算" if zh else "Recalculate"))

        if hasattr(self, "overdue_menu"):
            self.overdue_menu.entryconfigure(0, label=("记录收款" if zh else "Record Payment"))
            self.overdue_menu.entryconfigure(1, label=("生成PDF发票" if zh else "Generate PDF Invoice"))
            self.overdue_menu.entryconfigure(3, label=("刷新" if zh else "Refresh"))

    def _on_language_changed(self, _event=None):
        if _event is not None and hasattr(_event, "widget") and _event.widget:
            selection = _event.widget.get().strip()
        elif self.language_selectors:
            selection = self.language_selectors[0].get().strip()
        else:
            selection = "EN"
        self._set_language("zh" if selection == "中文" else "en")

    def _on_theme_changed(self, _event=None):
        if _event is not None and hasattr(_event, "widget") and _event.widget:
            selection = _event.widget.get().strip()
        elif self.theme_selectors:
            selection = self.theme_selectors[0].get().strip()
        else:
            selection = "Light"
        self._set_theme("dark" if selection.lower() == "dark" else "light")

    def _create_language_selector(self, parent: tk.Misc, width: int = 6) -> ttk.Combobox:
        selector = ttk.Combobox(parent, state="readonly", values=["EN", "中文"], width=width)
        selector.set("中文" if self.current_language == "zh" else "EN")
        selector.bind("<<ComboboxSelected>>", self._on_language_changed)
        self.language_selectors.append(selector)
        return selector

    def _create_theme_selector(self, parent: tk.Misc, width: int = 8) -> ttk.Combobox:
        selector = ttk.Combobox(parent, state="readonly", values=["Light", "Dark"], width=width)
        selector.set("Dark" if self.theme_mode == "dark" else "Light")
        selector.bind("<<ComboboxSelected>>", self._on_theme_changed)
        self.theme_selectors.append(selector)
        return selector
