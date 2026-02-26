from __future__ import annotations

import ctypes
from datetime import datetime

from core.app_logging import get_app_logger, log_ux_action, trace
from core.config import HISTORY_LOG_FILE


logger = get_app_logger()


@trace
def log_action(event_type: str, details: str):
    """Append immutable action to history log file and UX action log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_ux_action(event_type, details=details)
    try:
        with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as file_handle:
            file_handle.write(f"[{timestamp}] {event_type} | {details}\n")
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
