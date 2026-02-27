#!/usr/bin/env python3
"""Unit tests for error_handler.py module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from core.error_handler import (
    safe_ui_action,
    safe_ui_action_returning,
    wrap_action_with_error_handling,
    log_exception,
    _format_error_message,
)


class TestSafeUIActionDecorator(unittest.TestCase):
    """Test the @safe_ui_action decorator."""

    def test_decorator_succeeds_on_normal_function(self):
        """Test that decorator doesn't interfere with normal execution."""

        @safe_ui_action("Test Action")
        def normal_func(a, b):
            return a + b

        result = normal_func(2, 3)
        assert result == 5

    def test_decorator_catches_exception(self):
        """Test that decorator catches exceptions and returns None."""

        @safe_ui_action("Test Action", show_error_dialog=False)
        def failing_func():
            raise ValueError("Test error")

        result = failing_func()
        assert result is None

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves original function name."""

        @safe_ui_action("Test")
        def my_test_function():
            pass

        assert my_test_function.__name__ == "my_test_function"

    def test_decorator_with_args_and_kwargs(self):
        """Test that decorator works with multiple arguments and keyword arguments."""

        @safe_ui_action("Test", show_error_dialog=False)
        def complex_func(a, b, c=None, d=None):
            return f"{a}-{b}-{c}-{d}"

        result = complex_func(1, 2, c=3, d=4)
        assert result == "1-2-3-4"

    def test_decorator_catches_different_exception_types(self):
        """Test that decorator catches various exception types."""

        @safe_ui_action("Test", show_error_dialog=False)
        def raise_type_error():
            return 1 + "string"

        result = raise_type_error()
        assert result is None

    @patch("core.error_handler.messagebox.showerror")
    def test_decorator_shows_error_dialog_by_default(self, mock_show):
        """Test that error dialog is shown by default."""

        @safe_ui_action("Test Action")
        def failing_func():
            raise ValueError("Test error message")

        failing_func()
        mock_show.assert_called_once()
        args = mock_show.call_args[0]
        assert "Test Action" in args[0]
        assert "Test error message" in args[1]

    @patch("core.error_handler.messagebox.showerror")
    def test_decorator_respects_show_error_dialog_false(self, mock_show):
        """Test that error dialog is not shown when show_error_dialog=False."""

        @safe_ui_action("Test", show_error_dialog=False)
        def failing_func():
            raise ValueError("Test error")

        failing_func()
        mock_show.assert_not_called()

    def test_decorator_does_not_catch_keyboard_interrupt(self):
        """Test that decorator lets KeyboardInterrupt propagate."""

        @safe_ui_action("Test", show_error_dialog=False)
        def raise_keyboard_interrupt():
            raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            raise_keyboard_interrupt()


class TestSafeUIActionReturningDecorator(unittest.TestCase):
    """Test the @safe_ui_action_returning decorator."""

    def test_decorator_returns_normal_value(self):
        """Test that decorator returns value from successful function."""

        @safe_ui_action_returning("Test", return_on_error=False)
        def return_true_func():
            return True

        result = return_true_func()
        assert result is True

    def test_decorator_returns_error_value_on_exception(self):
        """Test that decorator returns specified error value on exception."""

        @safe_ui_action_returning("Test", return_on_error=False, show_error_dialog=False)
        def failing_func():
            raise ValueError("Test error")

        result = failing_func()
        assert result is False

    def test_decorator_with_numeric_return_on_error(self):
        """Test that decorator can return numeric values on error."""

        @safe_ui_action_returning("Test", return_on_error=0, show_error_dialog=False)
        def failing_func():
            raise ValueError("Test error")

        result = failing_func()
        assert result == 0

    def test_decorator_with_object_return_on_error(self):
        """Test that decorator can return objects on error."""
        default_dict = {}

        @safe_ui_action_returning("Test", return_on_error=default_dict, show_error_dialog=False)
        def failing_func():
            raise ValueError("Test error")

        result = failing_func()
        assert result is default_dict


class TestWrapActionWithErrorHandling(unittest.TestCase):
    """Test wrap_action_with_error_handling function."""

    def test_wrapper_succeeds_on_normal_execution(self):
        """Test that wrapper doesn't interfere with normal execution."""

        def normal_func(a, b):
            return a * b

        wrapped = wrap_action_with_error_handling(normal_func, "Test")
        result = wrapped(3, 4)
        assert result == 12

    def test_wrapper_returns_none_on_error(self):
        """Test that wrapper returns None on exception."""

        def failing_func():
            raise RuntimeError("Test error")

        wrapped = wrap_action_with_error_handling(
            failing_func,
            "Test",
            show_error_dialog=False,
        )
        result = wrapped()
        assert result is None

    def test_wrapper_preserves_function_name(self):
        """Test that wrapper preserves function name."""

        def my_func():
            pass

        wrapped = wrap_action_with_error_handling(my_func, "Test")
        assert wrapped.__name__ == "my_func"

    @patch("core.error_handler.messagebox.showerror")
    def test_wrapper_shows_error_dialog(self, mock_show):
        """Test that wrapper shows error dialog on exception."""

        def failing_func():
            raise ValueError("Test error")

        wrapped = wrap_action_with_error_handling(failing_func, "TestAction")
        wrapped()
        mock_show.assert_called_once()


class TestFormatErrorMessage(unittest.TestCase):
    """Test _format_error_message function."""

    def test_format_simple_error(self):
        """Test formatting of simple error message."""
        exc = ValueError("Something went wrong")
        msg = _format_error_message("Test Action", "Something went wrong", exc)

        assert "Test Action" in msg
        assert "Something went wrong" in msg
        assert "try again" in msg.lower()

    def test_format_truncates_long_message(self):
        """Test that very long error messages are truncated."""
        long_error = "x" * 1000
        exc = ValueError(long_error)
        msg = _format_error_message("Test", long_error, exc)

        assert len(msg) < len(long_error)
        assert "..." in msg

    def test_format_includes_contact_support(self):
        """Test that formatted message includes support suggestion."""
        exc = RuntimeError("Test error")
        msg = _format_error_message("Action", "Test error", exc)

        assert "contact support" in msg.lower()


class TestLogException(unittest.TestCase):
    """Test log_exception function."""

    @patch("core.error_handler.logger.exception")
    def test_log_exception_calls_logger(self, mock_logger):
        """Test that log_exception calls the logger."""
        exc = ValueError("Test error")
        log_exception("Test Action", exc)

        mock_logger.assert_called_once()
        assert "Test Action" in mock_logger.call_args[0][0]

    @patch("core.error_handler.logger.exception")
    def test_log_exception_with_context(self, mock_logger):
        """Test that log_exception includes context information."""
        exc = ValueError("Test error")
        context = {"user_id": 123, "action": "test"}
        log_exception("Test Action", exc, context)

        mock_logger.assert_called_once()
        assert mock_logger.call_args[1]["extra"] == context


class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling system."""

    @patch("core.error_handler.messagebox.showerror")
    def test_multiple_exception_types_handled(self, mock_show):
        """Test that various exception types are handled gracefully."""
        test_exceptions = [
            ValueError("Value error"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
            IOError("IO error"),
            KeyError("Key error"),
            AttributeError("Attribute error"),
        ]

        for exc in test_exceptions:

            @safe_ui_action("Test", show_error_dialog=True)
            def raise_exception():
                raise exc

            result = raise_exception()
            assert result is None

            # Dialog should be called for each exception
            assert mock_show.called

    def test_decorator_chain_compatibility(self):
        """Test that decorator works well with other decorators."""

        def other_decorator(func):
            def wrapper(*args, **kwargs):
                kwargs["extra"] = "added"
                return func(*args, **kwargs)

            return wrapper

        @safe_ui_action("Test", show_error_dialog=False)
        @other_decorator
        def test_func(val, extra=None):
            return val + (len(extra) if extra else 0)

        result = test_func(5)
        assert result == 5 + len("added")

    @patch("core.error_handler.messagebox.showerror")
    def test_error_handling_with_database_operations(self, mock_show):
        """Test error handling with database-like operations."""

        @safe_ui_action("Database Operation")
        def simulate_db_error():
            raise Exception("Database connection failed")

        result = simulate_db_error()
        assert result is None
        mock_show.assert_called_once()
        error_title = mock_show.call_args[0][0]
        assert "Database Operation" in error_title

    @patch("core.error_handler.messagebox.showerror")
    def test_error_handling_with_file_operations(self, mock_show):
        """Test error handling with file I/O-like operations."""

        @safe_ui_action("File Operation")
        def simulate_file_error():
            raise IOError("File not found: /invalid/path")

        result = simulate_file_error()
        assert result is None
        mock_show.assert_called_once()


if __name__ == "__main__":
    unittest.main()
