"""
Centralized error handling for UI actions.

Provides decorators and utilities to catch unhandled exceptions in UI actions
and display user-friendly error messages instead of crashing.
"""

import functools
import logging
import traceback
from typing import Any, Callable, Dict, Optional, TypeVar

from tkinter import messagebox

logger = logging.getLogger("changsheng_app")

# Type variable for decorating any callable
F = TypeVar("F", bound=Callable[..., Any])


def safe_ui_action(
    action_name: str = "",
    show_error_dialog: bool = True,
    log_full_traceback: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to safely wrap UI action functions with centralized error handling.

    Catches any unhandled exceptions, logs them, and displays a user-friendly error
    dialog instead of crashing the application.

    Args:
        action_name: Human-readable name of the action (for logging/error messages).
                     If not provided, uses function name.
        show_error_dialog: If True, shows an error messagebox to the user.
        log_full_traceback: If True, logs the full traceback for debugging.

    Returns:
        Decorated function that catches and handles exceptions gracefully.

    Example:
        @safe_ui_action("Backup Database")
        def backup_database_action(app, db):
            # Your code here
            pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            action = action_name or func.__name__
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                # Don't catch keyboard interrupt
                raise
            except Exception as exc:
                error_msg = str(exc)
                logger.error(
                    f"Error in {action}: {error_msg}",
                    exc_info=log_full_traceback,
                )

                if show_error_dialog:
                    # Create user-friendly error message
                    user_msg = _format_error_message(action, error_msg, exc)
                    try:
                        messagebox.showerror(
                            f"Error: {action}",
                            user_msg,
                        )
                    except Exception as dialog_exc:
                        # If messagebox itself fails, just log it
                        logger.exception(f"Failed to show error dialog: {dialog_exc}")

                return None

        return wrapper  # type: ignore

    return decorator


def safe_ui_action_returning(
    action_name: str = "",
    return_on_error: Any = False,
    show_error_dialog: bool = True,
    log_full_traceback: bool = True,
) -> Callable[[F], F]:
    """
    Decorator for UI actions that return a value.

    Similar to safe_ui_action but allows specifying a return value on error.

    Args:
        action_name: Human-readable name of the action (for logging/error messages).
        return_on_error: Value to return if an exception occurs.
        show_error_dialog: If True, shows an error messagebox to the user.
        log_full_traceback: If True, logs the full traceback for debugging.

    Returns:
        Decorated function that catches and handles exceptions gracefully.

    Example:
        @safe_ui_action_returning("Validate Input", return_on_error=False)
        def validate_input_action(data):
            # Your code here
            return True
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            action = action_name or func.__name__
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                # Don't catch keyboard interrupt
                raise
            except Exception as exc:
                error_msg = str(exc)
                logger.error(
                    f"Error in {action}: {error_msg}",
                    exc_info=log_full_traceback,
                )

                if show_error_dialog:
                    user_msg = _format_error_message(action, error_msg, exc)
                    try:
                        messagebox.showerror(
                            f"Error: {action}",
                            user_msg,
                        )
                    except Exception as dialog_exc:
                        logger.exception(f"Failed to show error dialog: {dialog_exc}")

                return return_on_error

        return wrapper  # type: ignore

    return decorator


def wrap_action_with_error_handling(
    func: Callable[..., Any],
    action_name: str = "",
    show_error_dialog: bool = True,
) -> Callable[..., Any]:
    """
    Wrap a function with error handling without using a decorator.

    Useful for wrapping partial functions or callbacks that can't use decorators easily.

    Args:
        func: The function to wrap.
        action_name: Human-readable name of the action.
        show_error_dialog: If True, shows an error messagebox to the user.

    Returns:
        Wrapped function that catches and handles exceptions.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        action = action_name or func.__name__
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            error_msg = str(exc)
            logger.error(
                f"Error in {action}: {error_msg}",
                exc_info=True,
            )

            if show_error_dialog:
                user_msg = _format_error_message(action, error_msg, exc)
                try:
                    messagebox.showerror(
                        f"Error: {action}",
                        user_msg,
                    )
                except Exception as dialog_exc:
                    logger.exception(f"Failed to show error dialog: {dialog_exc}")

            return None

    return wrapper


def _format_error_message(action: str, error_msg: str, exc: Exception) -> str:
    """
    Format an error message for user display.

    Args:
        action: Name of the action that failed.
        error_msg: The error message.
        exc: The exception object.

    Returns:
        Formatted user-friendly error message.
    """
    # Truncate very long error messages
    if len(error_msg) > 500:
        error_msg = error_msg[:497] + "..."

    # Build the message
    lines = [f"The following error occurred while {action}:"]
    lines.append("")
    lines.append(error_msg)
    lines.append("")
    lines.append("Please try again or contact support if the problem persists.")

    return "\n".join(lines)


def log_exception(
    action: str,
    exc: Exception,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Centralized exception logging.

    Args:
        action: Description of the action that caused the exception.
        exc: The exception that occurred.
        context: Additional contextual information (logged as extra fields).
    """
    extra = context or {}
    logger.exception(
        f"Exception in {action}",
        extra=extra,
    )


__all__ = [
    "safe_ui_action",
    "safe_ui_action_returning",
    "wrap_action_with_error_handling",
    "log_exception",
]
