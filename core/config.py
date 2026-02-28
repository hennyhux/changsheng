"""
Configuration constants for Changsheng - Truck Lot Tracker.
Centralized configuration for easier maintenance and customization.
"""

import re

# ============================================================================
# FILE PATHS
# ============================================================================
DB_PATH = "monthly_lot.db"
HISTORY_LOG_FILE = "history_blackbox.txt"
EXCEPTIONS_LOG_FILE = "exceptions.log"  # legacy – new logs go to log/ folder
SETTINGS_FILE = "app_settings.json"
BACKUP_REMINDER_DAYS = 7
AUTO_BACKUP_MAX_COPIES = 20

# Log directory and files (managed by app_logging.py)
LOG_DIR = "log"
LOG_EXCEPTIONS_FILE = "log/exceptions.log"
LOG_UX_ACTIONS_FILE = "log/ux_actions.log"
LOG_TRACE_FILE = "log/trace.log"


# ============================================================================
# VALIDATION PATTERNS
# ============================================================================
PHONE_PATTERN = re.compile(r"^[0-9()+\-.\s]{7,20}$")
PLATE_PATTERN = re.compile(r"^[A-Z0-9\-\s]{2,15}$")
STATE_PATTERN = re.compile(r"^[A-Z]{2}$")
SEARCH_PLATE_PATTERN = re.compile(r"^[A-Z0-9\-\s]*$")


# ============================================================================
# WINDOW & UI GEOMETRY
# ============================================================================
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 820
TREE_ROW_HEIGHT = 48
TREE_ALT_ROW_COLORS = ("#ffffff", "#eef4ff")


# ============================================================================
# FONTS
# ============================================================================
FONTS = {
    "base": ("Segoe UI", 15),
    "heading": ("Segoe UI", 16, "bold"),
    "dashboard_title": ("Segoe UI", 52, "bold"),
    "label_bold": ("Segoe UI", 12, "bold"),
    "label_normal": ("Segoe UI", 11),
    "hint_gray": ("", 10),  # foreground="gray"
    "tree_default": ("TkDefaultFont", 12),
    "tree_bold": ("TkDefaultFont", 12, "bold"),
    "tree_large": ("Segoe UI", 14),
    "tree_large_bold": ("Segoe UI", 14, "bold"),
    "tree_payment_history": ("Segoe UI", 14, "bold"),
}


# ============================================================================
# COLORS & TAGS
# ============================================================================
TAG_COLORS = {
    "status_due": {
        "foreground": "#b00020",
        "background": "#ffe8ea",
        "font": ("Segoe UI", 12, "bold"),
    },
    "status_paid": {
        "foreground": "#1b5e20",
        "background": "#e8f5e9",
    },
    "contract_active": {
        "background": "#dff0d8",
        "font": ("Segoe UI", 11, "bold"),
    },
    "contract_inactive": {
        "background": "#f5f5f5",
        "font": ("Segoe UI", 11, "bold"),
        "foreground": "#666666",
    },
}

FORM_BALANCE_COLOR_ERROR = "#b00020"

# Button warning colors for delete operations
DELETE_BUTTON_BG = "#c62828"  # Bold red
DELETE_BUTTON_FG = "#ffffff"  # White text
DELETE_BUTTON_HOVER_BG = "#b71c1c"  # Darker red on hover

# Selection highlight color (stronger than default)
SELECTION_BG = "#1565c0"  # Deeper blue
SELECTION_FG = "#ffffff"  # White text

EXCEL_FILL_COLORS = {
    "green": "DDFFDD",
    "gray": "EEEEEE",
    "header": "D9E1F2",
}


# ============================================================================
# THEMES
# ============================================================================
THEME_PALETTES = {
    "light": {
        "root_bg": "#f6f8fb",
        "surface_bg": "#ffffff",
        "panel_bg": "#ffffff",
        "text": "#111111",
        "muted_text": "#666666",
        "border": "#d7dde6",
        "entry_bg": "#ffffff",
        "entry_text": "#111111",
        "entry_disabled_bg": "#edf1f6",
        "tab_selected_bg": "#ffffff",
        "tab_active_bg": "#f1f5fb",
        "tab_idle_bg": "#e6ebf2",
        "tab_selected_text": "#111111",
        "tab_idle_text": "#333333",
        "tree_bg": "#ffffff",
        "tree_fg": "#111111",
        "tree_heading_bg": "#e9eef5",
        "tree_heading_fg": "#111111",
        "stripe_even": "#ffffff",
        "stripe_odd": "#eef4ff",
        "invoice_parent_expanded": "#dff0ff",
        "invoice_child_even": "#ffffff",
        "invoice_child_odd": "#f9fbff",
        "text_widget_bg": "#ffffff",
        "text_widget_fg": "#111111",
        "menu_bg": "#ffffff",
        "menu_fg": "#111111",
        "menu_active_bg": "#e8effa",
        "menu_active_fg": "#111111",
        "payment_button_fg": "#2e7d32",
        "payment_button_active_fg": "#1b5e20",
        "create_button_fg": "#2e7d32",
        "create_button_active_fg": "#1b5e20",
        "view_trucks_button_fg": "#2e7d32",
        "view_trucks_button_active_fg": "#1b5e20",
        "status_bal_zero": "#2e7d32",
        "status_bal_no_contract": "#b58900",
        "status_bal_due": "#b00020",
    },
    "dark": {
        "root_bg": "#141a22",
        "surface_bg": "#1b2430",
        "panel_bg": "#1f2a37",
        "text": "#f4f8ff",
        "muted_text": "#d5deea",
        "border": "#2e3a4a",
        "entry_bg": "#223041",
        "entry_text": "#f4f8ff",
        "entry_disabled_bg": "#2a3442",
        "tab_selected_bg": "#253447",
        "tab_active_bg": "#2c3d52",
        "tab_idle_bg": "#1f2b39",
        "tab_selected_text": "#f2f6fb",
        "tab_idle_text": "#dce6f3",
        "tree_bg": "#1d2632",
        "tree_fg": "#f2f7ff",
        "tree_heading_bg": "#2a3647",
        "tree_heading_fg": "#f4f8ff",
        "stripe_even": "#1d2632",
        "stripe_odd": "#243142",
        "invoice_parent_expanded": "#2a3a4f",
        "invoice_child_even": "#1d2632",
        "invoice_child_odd": "#223041",
        "text_widget_bg": "#0f1720",
        "text_widget_fg": "#f1f7ff",
        "menu_bg": "#1b2430",
        "menu_fg": "#f4f8ff",
        "menu_active_bg": "#32445b",
        "menu_active_fg": "#ffffff",
        "payment_button_fg": "#72d08e",
        "payment_button_active_fg": "#8fe3a8",
        "create_button_fg": "#72d08e",
        "create_button_active_fg": "#8fe3a8",
        "view_trucks_button_fg": "#72d08e",
        "view_trucks_button_active_fg": "#8fe3a8",
        "status_bal_zero": "#7ef29a",
        "status_bal_no_contract": "#ffd56a",
        "status_bal_due": "#ff6b8a",
    },
}


# ============================================================================
# PDF INVOICE STYLES & LABELS
# ============================================================================
PDF_TEXT = {
    "title": "Invoice Summary",
    "subtitle_prefix": "Customer Invoice",
    "section_contracts": "Contracts",
    "section_payments": "Recent Payments",
    "no_contracts": "<i>No active contracts found for this customer.</i>",
    "footer_prefix": "Generated on",
    "dash": "—",
    "label_customer": "Customer:",
    "label_phone": "Phone:",
    "label_company": "Company:",
    "label_invoice_uuid": "Invoice UUID:",
    "outstanding_as_of": "as of",
}

PDF_HEADERS = {
    "contracts": ["Contract ID", "Plate", "Rate", "Start", "End", "Expected", "Paid", "Outstanding"],
    "payments": ["Date", "Amount", "Method", "Contract", "Reference/Notes"],
    "summary": ["Total Expected", "Total Paid", "Total Outstanding", "Next Due Date"],
}

PDF_COLORS = {
    "title": "#1a1a1a",
    "subtitle": "#666666",
    "section": "#1f1f1f",
    "contracts_header_bg": "#0f3d5e",
    "payments_header_bg": "#2f4858",
    "header_text": "#ffffff",
    "grid": "#d0d4d8",
    "summary_bg": "#f0f4f8",
    "summary_text": "#1f1f1f",
    "summary_outstanding": "#b00020",
    "summary_outstanding_bg": "#fff3cd",
    "summary_border": "#c6ccd2",
    "row_alt": "#f7f8fa",
    "footer": "#808080",
}

PDF_FONTS = {
    "title_size": 18,
    "subtitle_size": 10,
    "section_size": 12,
    "table_header_size": 10,
    "table_body_size": 10,
    "footer_size": 9,
}

PDF_LAYOUT = {
    "margin_top": 0.6,
    "margin_bottom": 0.6,
    "margin_left": 0.7,
    "margin_right": 0.7,
    "contracts_col_widths": [0.9, 1.3, 0.9, 0.95, 0.95, 1.1, 1.0, 1.2],
    "payments_col_widths": [1.0, 1.0, 1.0, 0.9, 2.6],
    "summary_col_widths": [1.6, 2.4],
    "section_spacer": 0.2,
    "summary_spacer": 0.25,
    "footer_spacer": 0.3,
}


# ============================================================================
# COLUMN CONFIGURATIONS
# ============================================================================
COLUMN_CONFIGS = {
    "customers": {
        "id": {"width": 70, "anchor": "center"},
        "name": {"width": 240, "anchor": "center"},
        "phone": {"width": 160, "anchor": "center"},
        "company": {"width": 220, "anchor": "center"},
        "trucks": {"width": 180, "anchor": "center"},
    },
    "trucks": {
        "id": {"width": 150, "anchor": "center"},
        "plate": {"width": 150, "anchor": "center"},
        "state": {"width": 150, "anchor": "center"},
        "make": {"width": 150, "anchor": "center"},
        "model": {"width": 150, "anchor": "center"},
        "customer": {"width": 280, "anchor": "center"},
    },
    "contracts": {
        "contract_id": {"width": 160, "anchor": "center"},
        "status": {"width": 150, "anchor": "center"},
        "customer": {"width": 280, "anchor": "center"},
        "scope": {"width": 280, "anchor": "center"},
        "rate": {"width": 150, "anchor": "center"},
        "start": {"width": 140, "anchor": "center"},
        "end": {"width": 140, "anchor": "center"},
    },
    "invoices": {
        "contract_id": {"width": 160, "anchor": "center"},
        "customer": {"width": 280, "anchor": "center"},
        "scope": {"width": 280, "anchor": "center"},
        "rate": {"width": 150, "anchor": "center"},
        "start": {"width": 140, "anchor": "center"},
        "end": {"width": 140, "anchor": "center"},
        "months": {"width": 180, "anchor": "center"},
        "expected": {"width": 160, "anchor": "center"},
        "paid": {"width": 160, "anchor": "center"},
        "balance": {"width": 160, "anchor": "center"},
        "status": {"width": 150, "anchor": "center"},
    },
    "overdue": {
        "month": {"width": 150, "anchor": "center"},
        "date": {"width": 140, "anchor": "center"},
        "invoice_id": {"width": 160, "anchor": "center"},
        "customer": {"width": 300, "anchor": "center"},
        "scope": {"width": 300, "anchor": "center"},
        "amount": {"width": 160, "anchor": "center"},
        "paid": {"width": 160, "anchor": "center"},
        "balance": {"width": 160, "anchor": "center"},
    },
    "payment_history": {
        "num": {"width": 40, "anchor": "center"},
        "paid_at": {"width": 120, "anchor": "center"},
        "amount": {"width": 90, "anchor": "center"},
        "method": {"width": 90, "anchor": "center"},
        "reference": {"width": 110, "anchor": "center"},
        "invoice_ym": {"width": 110, "anchor": "center"},
        "notes": {"width": 220, "anchor": "w"},
    },
}

COLUMN_ORDER = {
    "customers": ("id", "name", "phone", "company", "trucks"),
    "trucks": ("id", "plate", "state", "make", "model", "customer"),
    "contracts": ("contract_id", "status", "customer", "scope", "rate", "start", "end"),
    "invoices": ("contract_id", "customer", "scope", "rate", "start", "end", "months", "expected", "paid", "balance", "status"),
    "overdue": ("month", "date", "invoice_id", "customer", "scope", "amount", "paid", "balance"),
    "payment_history": ("num", "paid_at", "amount", "method", "reference", "invoice_ym", "notes"),
}


# ============================================================================
# COLUMN HEADERS (for language switching)
# ============================================================================
COLUMN_HEADINGS_EN = {
    "customers": {"id": "ID", "name": "Name", "phone": "Phone", "company": "Company", "trucks": "Trucks Parked"},
    "trucks": {"id": "ID", "plate": "Plate", "state": "State", "make": "Make", "model": "Model", "customer": "Customer"},
    "contracts": {"contract_id": "Contract ID", "status": "Status", "customer": "Customer", "scope": "Scope", "rate": "Rate", "start": "Start", "end": "End"},
    "invoices": {"contract_id": "Contract ID", "customer": "Customer", "scope": "Scope", "rate": "Rate", "start": "Start", "end": "End", "months": "Elapsed Months", "expected": "Expected", "paid": "Paid", "balance": "Outstanding", "status": "Status"},
    "overdue": {"month": "Month", "date": "Date", "invoice_id": "Invoice ID", "customer": "Customer", "scope": "Scope", "amount": "Amount", "paid": "Paid", "balance": "Balance"},
    "payment_history": {"num": "#", "paid_at": "Paid Date", "amount": "Amount", "method": "Method", "reference": "Reference", "invoice_ym": "Invoice Month", "notes": "Notes"},
}

COLUMN_HEADINGS_ZH = {
    "customers": {"id": "编号", "name": "姓名", "phone": "电话", "company": "公司", "trucks": "停放车辆"},
    "trucks": {"id": "编号", "plate": "车牌", "state": "州", "make": "品牌", "model": "型号", "customer": "客户"},
    "contracts": {"contract_id": "合同编号", "status": "状态", "customer": "客户", "scope": "范围", "rate": "费率", "start": "开始", "end": "结束"},
    "invoices": {"contract_id": "合同编号", "customer": "客户", "scope": "范围", "rate": "费率", "start": "开始", "end": "结束", "months": "累计月数", "expected": "应收", "paid": "已付", "balance": "余额", "status": "状态"},
    "overdue": {"month": "月份", "date": "日期", "invoice_id": "发票编号", "customer": "客户", "scope": "范围", "amount": "金额", "paid": "已付", "balance": "余额"},
    "payment_history": {"num": "序号", "paid_at": "付款日期", "amount": "金额", "method": "方式", "reference": "参考", "invoice_ym": "发票月份", "notes": "备注"},
}


# ============================================================================
# INPUT FIELD WIDTHS
# ============================================================================
INPUT_WIDTHS = {
    "customer_search": 30,
    "customer_name": 25,
    "customer_phone": 18,
    "customer_company": 22,
    "customer_notes": 80,
    
    "truck_search": 20,
    "truck_plate": 14,
    "truck_state": 6,
    "truck_make": 10,
    "truck_model": 10,
    "truck_customer": 40,
    "truck_notes": 42,
    
    "contract_customer": 40,
    "contract_truck": 30,
    "contract_rate": 12,
    "contract_date": 12,
    "contract_notes": 80,
    
    "invoice_date": 12,
    "invoice_month": 12,
    
    "payment_amount": 28,
    "payment_reference": 20,
    "payment_notes": 40,
    
    "language_selector": 6,
}


# ============================================================================
# PAYMENT METHODS
# ============================================================================
PAYMENT_METHODS = ["cash", "card", "zelle", "venmo", "other"]


# ============================================================================
# TAB NAMES & LABELS
# ============================================================================
TAB_LABELS_EN = {
    "dashboard": "📈 Dashboard",
    "customers": "👥 Customers",
    "trucks": "🚚 Trucks",
    "contracts": "📝 Contracts",
    "billing": "💵 Billing",
    "invoices": "🧾 Invoices & Payments",
    "statement": "📊 Monthly Statement",
    "overdue": "⏰ Overdue",
    "histories": "🕑 Histories",
}

TAB_LABELS_ZH = {
    "dashboard": "📈 仪表板",
    "customers": "👥 客户",
    "trucks": "🚚 车辆",
    "contracts": "📝 合同",
    "billing": "💵 账单",
    "invoices": "🧾 发票和付款",
    "statement": "📊 月度报表",
    "overdue": "⏰ 逾期",
    "histories": "🕑 历史",
}


# ============================================================================
# FORM LABELS & TOOLTIPS
# ============================================================================
FORM_LABELS_EN = {
    "name": "Name*",
    "phone": "Phone",
    "company": "Company",
    "notes": "Notes",
    "plate": "Plate*",
    "state": "State",
    "make": "Make",
    "model": "Model",
    "rate": "Monthly Rate*",
    "start_date": "Start Date",
    "end_date": "End Date (optional)",
    "customer": "Customer",
    "truck": "Truck",
    "amount": "Amount",
    "method": "Method",
    "reference": "Reference",
    "enter_hint": "(Enter in any field)",
}

FORM_LABELS_ZH = {
    "name": "姓名*",
    "phone": "电话",
    "company": "公司",
    "notes": "备注",
    "plate": "车牌*",
    "state": "州",
    "make": "品牌",
    "model": "型号",
    "rate": "月费率*",
    "start_date": "开始日期",
    "end_date": "结束日期（可选）",
    "customer": "客户",
    "truck": "车辆",
    "amount": "金额",
    "method": "方式",
    "reference": "参考",
    "enter_hint": "（在任何字段中按Enter）",
}


# ============================================================================
# BUTTON LABELS & COMMANDS
# ============================================================================
BUTTON_LABELS_EN = {
    "add": "Add",
    "edit": "Edit",
    "delete": "Delete Selected",
    "refresh": "Refresh",
    "export_csv": "Export CSV",
    "import_csv": "Import CSV",
    "generate_pdf": "Generate PDF Invoice",
    "toggle_status": "Toggle Active/Inactive",
    "view_history": "View Payment History",
    "fill_payment": "Fill Payment Form",
    "recalculate": "Recalculate",
    "collapse_all": "Collapse All",
    "expand_all": "Expand All",
    "ok": "OK",
    "cancel": "Cancel",
    "save": "Save",
}

BUTTON_LABELS_ZH = {
    "add": "添加",
    "edit": "编辑",
    "delete": "删除选中",
    "refresh": "刷新",
    "export_csv": "导出CSV",
    "import_csv": "导入CSV",
    "generate_pdf": "生成PDF发票",
    "toggle_status": "切换激活/停用",
    "view_history": "查看付款历史",
    "fill_payment": "填写付款表单",
    "recalculate": "重新计算",
    "collapse_all": "全部收起",
    "expand_all": "全部展开",
    "ok": "确定",
    "cancel": "取消",
    "save": "保存",
}


# ============================================================================
# HELPER FUNCTION
# ============================================================================
def get_column_config(section: str, search_lang: str = "en") -> dict:
    """
    Get complete column configuration for a specific section.
    
    Args:
        section: Section name (e.g., "customers", "trucks", "invoices")
        search_lang: Language for headers ("en" or "zh")
    
    Returns:
        Dictionary with column names and their configuration including headers
    """
    if section not in COLUMN_CONFIGS:
        raise ValueError(f"Unknown section: {section}")
    
    headings = COLUMN_HEADINGS_EN if search_lang == "en" else COLUMN_HEADINGS_ZH
    
    config = {}
    for col_name, col_config in COLUMN_CONFIGS[section].items():
        config[col_name] = {
            **col_config,
            "header": headings[section].get(col_name, col_name),
        }
    
    return config
