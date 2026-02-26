"""
Centralized logging configuration for Changsheng - Truck Lot Tracker.

Provides three dedicated log streams:
    1. Exception log   – log/exceptions.log  – All exceptions with full tracebacks
    2. UX Action log   – log/ux_actions.log  – Every user-initiated UI action
    3. Trace log       – log/trace.log       – Method entry/exit for all key functions

Each log is written to its own rotating file inside the ``log/`` directory and
(optionally) echoed to the console at a configurable level.

Usage
-----
    from core.app_logging import setup_all_loggers, get_exception_logger, get_ux_logger, get_trace_logger, trace

    # Call once at application startup (changsheng.py)
    setup_all_loggers()

    # Obtain the individual loggers wherever needed
    exc_log   = get_exception_logger()
    ux_log    = get_ux_logger()
    trace_log = get_trace_logger()

    # Decorator for automatic trace logging
    @trace
    def my_function(arg1, arg2):
        ...
"""

from __future__ import annotations

import functools
import logging
import logging.handlers
import os
import sys
import time
from typing import Any, Callable, TypeVar

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")

# Rotating-file settings
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file
_BACKUP_COUNT = 5              # keep 5 rotated copies

# Logger names (also used as identifiers in getLogger)
EXCEPTION_LOGGER_NAME = "changsheng.exception"
UX_ACTION_LOGGER_NAME = "changsheng.ux_action"
TRACE_LOGGER_NAME = "changsheng.trace"

# Also maintain backwards-compat with the old single logger name
APP_LOGGER_NAME = "changsheng_app"

F = TypeVar("F", bound=Callable[..., Any])

# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

_EXCEPTION_FMT = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_UX_ACTION_FMT = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_TRACE_FMT = logging.Formatter(
    "[%(asctime)s.%(msecs)03d] %(levelname)-8s | %(funcName)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_CONSOLE_FMT = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_log_dir() -> None:
    """Create the ``log/`` directory if it does not exist."""
    os.makedirs(_LOG_DIR, exist_ok=True)


def _rotating_handler(filename: str, formatter: logging.Formatter, level: int) -> logging.Handler:
    """Create a RotatingFileHandler inside ``log/``."""
    path = os.path.join(_LOG_DIR, filename)
    handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def _console_handler(level: int = logging.WARNING) -> logging.Handler:
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(_CONSOLE_FMT)
    return handler


# ---------------------------------------------------------------------------
# Logger factories
# ---------------------------------------------------------------------------

def _clear_logger_handlers(logger: logging.Logger) -> None:
    """Close and remove all existing handlers to avoid resource leaks."""
    for handler in logger.handlers[:]:
        try:
            handler.close()
        except Exception:
            pass
    logger.handlers.clear()


def _setup_exception_logger() -> logging.Logger:
    """
    Exception logger — captures WARNING+ with full tracebacks.

    File: log/exceptions.log
    """
    logger = logging.getLogger(EXCEPTION_LOGGER_NAME)
    _clear_logger_handlers(logger)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_rotating_handler("exceptions.log", _EXCEPTION_FMT, logging.WARNING))
    logger.addHandler(_console_handler(logging.ERROR))
    logger.propagate = False
    return logger


def _setup_ux_action_logger() -> logging.Logger:
    """
    UX Action logger — records every user-initiated action at INFO+.

    File: log/ux_actions.log
    """
    logger = logging.getLogger(UX_ACTION_LOGGER_NAME)
    _clear_logger_handlers(logger)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_rotating_handler("ux_actions.log", _UX_ACTION_FMT, logging.INFO))
    logger.propagate = False
    return logger


def _setup_trace_logger() -> logging.Logger:
    """
    Trace logger — logs method entry/exit with timing at DEBUG+.

    File: log/trace.log
    """
    logger = logging.getLogger(TRACE_LOGGER_NAME)
    _clear_logger_handlers(logger)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_rotating_handler("trace.log", _TRACE_FMT, logging.DEBUG))
    logger.propagate = False
    return logger


def _setup_app_logger() -> logging.Logger:
    """
    Backward-compatible ``changsheng_app`` logger used by error_handler.py
    and legacy code.  Routes to exception log file + console.
    """
    logger = logging.getLogger(APP_LOGGER_NAME)
    _clear_logger_handlers(logger)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_rotating_handler("exceptions.log", _EXCEPTION_FMT, logging.WARNING))
    logger.addHandler(_console_handler(logging.WARNING))
    logger.propagate = False
    return logger


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_all_loggers() -> None:
    """
    Initialize **all** application loggers.  Call once at startup.

    Creates the ``log/`` directory and configures:
        - changsheng.exception  → log/exceptions.log
        - changsheng.ux_action  → log/ux_actions.log
        - changsheng.trace      → log/trace.log
        - changsheng_app        → log/exceptions.log  (backward compat)
    """
    _ensure_log_dir()
    _setup_exception_logger()
    _setup_ux_action_logger()
    _setup_trace_logger()
    _setup_app_logger()


def get_exception_logger() -> logging.Logger:
    """Return the exception logger (``changsheng.exception``)."""
    return logging.getLogger(EXCEPTION_LOGGER_NAME)


def get_ux_logger() -> logging.Logger:
    """Return the UX-action logger (``changsheng.ux_action``)."""
    return logging.getLogger(UX_ACTION_LOGGER_NAME)


def get_trace_logger() -> logging.Logger:
    """Return the trace logger (``changsheng.trace``)."""
    return logging.getLogger(TRACE_LOGGER_NAME)


def get_app_logger() -> logging.Logger:
    """Return the backward-compatible app logger (``changsheng_app``)."""
    return logging.getLogger(APP_LOGGER_NAME)


# ---------------------------------------------------------------------------
# UX-action logging helpers
# ---------------------------------------------------------------------------

def log_ux_action(action_name: str, details: str = "", user_context: str = "") -> None:
    """
    Log a user-initiated action to the UX action log.

    Args:
        action_name: Short verb phrase, e.g. "Add Customer", "Record Payment".
        details: Free-form detail string.
        user_context: Optional extra context (e.g. customer ID, contract ID).
    """
    ux = get_ux_logger()
    parts = [f"ACTION={action_name}"]
    if user_context:
        parts.append(f"CTX={user_context}")
    if details:
        parts.append(f"DETAILS={details}")
    ux.info(" | ".join(parts))


def log_ux_action_result(action_name: str, success: bool, details: str = "") -> None:
    """
    Log the result (success/failure) of a user-initiated action.

    Args:
        action_name: Action name matching a previous ``log_ux_action`` call.
        success: Whether the action succeeded.
        details: Optional extra detail (error message on failure, etc.).
    """
    ux = get_ux_logger()
    status = "SUCCESS" if success else "FAILURE"
    msg = f"RESULT={status} | ACTION={action_name}"
    if details:
        msg += f" | DETAILS={details}"
    if success:
        ux.info(msg)
    else:
        ux.warning(msg)


# ---------------------------------------------------------------------------
# Exception logging helpers
# ---------------------------------------------------------------------------

def log_exception(action: str, exc: Exception, context: str = "") -> None:
    """
    Log an exception with full traceback to the exception log.

    Args:
        action: Human-readable action name where the error occurred.
        exc: The exception object.
        context: Optional extra context string.
    """
    exc_log = get_exception_logger()
    msg = f"EXCEPTION in {action}: {exc}"
    if context:
        msg += f" | CTX={context}"
    exc_log.error(msg, exc_info=True)


# ---------------------------------------------------------------------------
# Trace decorator & helpers
# ---------------------------------------------------------------------------

def trace(func: F) -> F:
    """
    Decorator that logs method entry and exit with arguments and duration.

    Writes to the trace log (``changsheng.trace`` / ``log/trace.log``).

    Example::

        @trace
        def add_customer(name, phone):
            ...

    Produces trace entries like::

        [2026-02-25 18:00:00.123] DEBUG | add_customer | ENTER args=(name='Alice', phone='555-0100')
        [2026-02-25 18:00:00.125] DEBUG | add_customer | EXIT  duration=0.002s result=<Customer id=42>
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tlog = get_trace_logger()
        func_name = func.__qualname__

        # Build a compact argument summary (truncate long reprs)
        arg_parts: list[str] = []
        for i, a in enumerate(args):
            r = repr(a)
            if len(r) > 120:
                r = r[:117] + "..."
            arg_parts.append(r)
        for k, v in kwargs.items():
            r = repr(v)
            if len(r) > 120:
                r = r[:117] + "..."
            arg_parts.append(f"{k}={r}")
        arg_str = ", ".join(arg_parts)
        if len(arg_str) > 500:
            arg_str = arg_str[:497] + "..."

        tlog.debug("ENTER %s(%s)", func_name, arg_str)
        t0 = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - t0
            result_repr = repr(result)
            if len(result_repr) > 200:
                result_repr = result_repr[:197] + "..."
            tlog.debug("EXIT  %s -> %s  [%.4fs]", func_name, result_repr, elapsed)
            return result
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            tlog.debug("RAISE %s -> %s: %s  [%.4fs]", func_name, type(exc).__name__, exc, elapsed)
            raise

    return wrapper  # type: ignore


def trace_method(func: F) -> F:
    """Alias for ``trace`` — use on class methods for clarity."""
    return trace(func)
