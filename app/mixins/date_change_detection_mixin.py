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
        self._date_change_detection_active = True
        self._app_date = today()
        logger.debug(f"Date change detection initialized for {self._app_date}")
        self._schedule_midnight_check()

    def _cancel_midnight_check(self) -> None:
        """Cancel the scheduled midnight check if one is pending."""
        midnight_check_id = getattr(self, "_midnight_check_id", None)
        if midnight_check_id is None:
            return
        try:
            self.after_cancel(midnight_check_id)
        except Exception:
            pass
        self._midnight_check_id = None

    def _schedule_midnight_check(self) -> None:
        """Schedule the next midnight check."""
        if not getattr(self, "_date_change_detection_active", False):
            return
        self._cancel_midnight_check()
        self._midnight_check_id = self.after(
            _MIDNIGHT_CHECK_INTERVAL_MS,
            self._check_for_midnight_rollover,
        )

    @trace
    def _check_for_midnight_rollover(self) -> None:
        """Check if the date has rolled over to a new day. Refresh if so."""
        if not getattr(self, "_date_change_detection_active", False):
            return
        self._midnight_check_id = None
        current_date = today()
        if current_date != self._app_date:
            logger.info(
                f"Date rollover detected: {self._app_date} → {current_date}. "
                "Refreshing date-dependent views."
            )
            self._app_date = current_date
            self._refresh_for_date_change()
        # Reschedule next check
        if getattr(self, "_date_change_detection_active", False):
            self._schedule_midnight_check()

    def _refresh_for_date_change(self) -> None:
        """Refresh all views that depend on the current date."""
        refresh_methods = (
            ("customers", self.refresh_customers),
            ("trucks", self.refresh_trucks),
            ("contracts", self.refresh_contracts),
            ("invoices", self.refresh_invoices),
            ("dashboard", self.refresh_dashboard),
            ("statement", self.refresh_statement),
            ("overdue", self.refresh_overdue),
        )
        failures: list[str] = []
        for name, refresh_method in refresh_methods:
            try:
                refresh_method()
            except Exception as exc:
                failures.append(name)
                logger.warning(f"Failed to refresh {name} after midnight: {exc}")

        if failures:
            logger.warning(
                "Date-dependent refresh completed with failures: %s",
                ", ".join(failures),
            )
            return

        logger.info("Date-dependent views refreshed after midnight")

    def on_close(self, force: bool = False) -> None:
        """Override on_close to clean up the midnight check timer."""
        self._date_change_detection_active = False
        self._cancel_midnight_check()
        # Call parent's on_close (will chain up through MRO)
        super().on_close(force=force)

