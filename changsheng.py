#!/usr/bin/env python3

from __future__ import annotations

try:
    import openpyxl
except ImportError:
    openpyxl = None

import tkinter as tk

from app.widgets import DateEntry


from app.action_wrappers import ActionWrappersMixin
from app.mixins import (
    BaseAppMixin,
    DashboardMixin,
    BillingMixin,
    ThemeLanguageMixin,
    NavigationMixin,
    ContextMenuMixin,
    TreeSortMixin,
    SettingsMixin,
    StartupLayoutMixin,
    BackupStartupMixin,
    LifecycleMixin,
    DropdownCacheMixin,
    CustomersTabMixin,
    TrucksTabMixin,
    ContractsTabMixin,
)
from core.app_logging import setup_all_loggers, get_app_logger
from core.runtime_utils import enable_windows_dpi_awareness, log_action

# Initialize all loggers (exception, ux_action, trace) at import time
setup_all_loggers()
logger = get_app_logger()

class App(
    StartupLayoutMixin,
    SettingsMixin,
    NavigationMixin,
    ContextMenuMixin,
    TreeSortMixin,
    BackupStartupMixin,
    LifecycleMixin,
    DropdownCacheMixin,
    CustomersTabMixin,
    TrucksTabMixin,
    ContractsTabMixin,
    BaseAppMixin,
    DashboardMixin,
    BillingMixin,
    ThemeLanguageMixin,
    ActionWrappersMixin,
    tk.Tk,
):
    date_entry_cls_default = DateEntry
    _log_action_callback = staticmethod(log_action)
    _openpyxl_runtime = openpyxl


if __name__ == "__main__":
    enable_windows_dpi_awareness()
    app = App()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, closing application gracefully.")
        app.on_close(force=True)