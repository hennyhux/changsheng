from __future__ import annotations

import importlib

from core.app_logging import get_app_logger


logger = get_app_logger()


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
                top.geometry("+%d+%d" % (x, entry_root_y - cal_h - 4))
            else:
                top.geometry("+%d+%d" % (x, entry_root_y + entry_h + 2))

    DateEntry = SmartDateEntry
except Exception:
    DateEntry = None
