"""
Mixin for automatically detecting date rollover and refreshing time-sensitive data.

When running for extended periods, midnight may occur while the app is open.
This mixin detects that midnight has passed and refreshes all date-dependent
UI components (dashboard, statement, overdue list).
"""

from __future__ import annotations

from core.app_logging import get_app_logger, trace
from utils.billing_date_utils import today


logger = get_app_logger()

# Check for midnight rollover every 30 seconds (conservative to avoid overhead)
_MIDNIGHT_CHECK_INTERVAL_MS = 30_000


class DateChangeDetectionMixin:
    """Detect date changes and refresh date-dependent views."""

    def _init_date_change_detection(self) -> None:
        """Initialize date tracking. Call this in startup."""
        self._app_date = today()
        logger.debug(f"Date change detection initialized for {self._app_date}")
        self._schedule_midnight_check()

    def _schedule_midnight_check(self) -> None:
        """Schedule the next midnight check."""
        self._midnight_check_id = self.after(
            _MIDNIGHT_CHECK_INTERVAL_MS,
            self._check_for_midnight_rollover,
        )

    @trace
    def _check_for_midnight_rollover(self) -> None:
        """Check if the date has rolled over to a new day. Refresh if so."""
        current_date = today()
        if current_date != self._app_date:
            logger.info(
                f"Date rollover detected: {self._app_date} → {current_date}. "
                "Refreshing date-dependent views."
            )
            self._app_date = current_date
            self._refresh_for_date_change()
        # Reschedule next check
        self._schedule_midnight_check()

    def _refresh_for_date_change(self) -> None:
        """Refresh all views that depend on the current date."""
        try:
            # Refresh views that use today's date
            self.refresh_dashboard()
            self.refresh_statement()
            self.refresh_overdue()
            logger.info("Date-dependent views refreshed after midnight")
        except Exception as exc:
            logger.warning(f"Failed to refresh date-dependent views: {exc}")

    def on_close(self, force: bool = False) -> None:
        """Override on_close to clean up the midnight check timer."""
        # Cancel the scheduled timer if it exists
        if hasattr(self, "_midnight_check_id"):
            try:
                self.after_cancel(self._midnight_check_id)
            except Exception:
                pass
        # Call parent's on_close (will chain up through MRO)
        super().on_close(force=force)

