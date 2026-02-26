from __future__ import annotations

from tkinter import messagebox

from core.app_logging import get_app_logger, trace
from ui.ui_actions import on_tab_changed_action


logger = get_app_logger()


class LifecycleMixin:
    def _on_tab_changed(self, event):
        on_tab_changed_action(
            app=self,
            _event=event,
            tab_has_unsaved_data_cb=self._tab_has_unsaved_data,
        )
        if self.main_notebook.select() == str(self.tab_contracts):
            self._sync_search_boxes_from_truck_search()
            self.refresh_contracts(refresh_dependents=False)
        self.after_idle(self._focus_current_tab_primary_input)

    @trace
    def on_close(self, force: bool = False):
        if not force:
            should_close = messagebox.askyesno(
                "Exit Application",
                "Close Changsheng now?\n\nAny open changes are saved immediately in this app.",
            )
            if not should_close:
                return
        try:
            self.db.close()
        except Exception as e:
            logger.warning(f"Failed to close database connection: {e}")
        self.destroy()
