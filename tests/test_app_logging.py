"""
Tests for the centralized logging infrastructure (app_logging.py).

Verifies:
    - Log directory creation
    - Exception log (log/exceptions.log)
    - UX Action log (log/ux_actions.log)
    - Trace log (log/trace.log)
    - Decorator behaviour (@trace)
    - Rotating file handler configuration
"""

import logging
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.app_logging import (
    EXCEPTION_LOGGER_NAME,
    UX_ACTION_LOGGER_NAME,
    TRACE_LOGGER_NAME,
    APP_LOGGER_NAME,
    setup_all_loggers,
    get_exception_logger,
    get_ux_logger,
    get_trace_logger,
    get_app_logger,
    log_ux_action,
    log_ux_action_result,
    log_exception,
    trace,
    trace_method,
    _ensure_log_dir,
    _LOG_DIR,
)


class TestLogDirectoryCreation(unittest.TestCase):
    """Test that the log/ directory is created on setup."""

    def test_log_dir_exists_after_setup(self):
        setup_all_loggers()
        self.assertTrue(os.path.isdir(_LOG_DIR))

    def test_ensure_log_dir_creates_missing_dir(self):
        """_ensure_log_dir should not raise even if dir already exists."""
        _ensure_log_dir()
        self.assertTrue(os.path.isdir(_LOG_DIR))


class TestLoggerInstances(unittest.TestCase):
    """Test that all loggers are properly configured."""

    @classmethod
    def setUpClass(cls):
        setup_all_loggers()

    def test_exception_logger_name(self):
        logger = get_exception_logger()
        self.assertEqual(logger.name, EXCEPTION_LOGGER_NAME)

    def test_ux_logger_name(self):
        logger = get_ux_logger()
        self.assertEqual(logger.name, UX_ACTION_LOGGER_NAME)

    def test_trace_logger_name(self):
        logger = get_trace_logger()
        self.assertEqual(logger.name, TRACE_LOGGER_NAME)

    def test_app_logger_name(self):
        logger = get_app_logger()
        self.assertEqual(logger.name, APP_LOGGER_NAME)

    def test_exception_logger_has_handlers(self):
        logger = get_exception_logger()
        self.assertGreater(len(logger.handlers), 0)

    def test_ux_logger_has_handlers(self):
        logger = get_ux_logger()
        self.assertGreater(len(logger.handlers), 0)

    def test_trace_logger_has_handlers(self):
        logger = get_trace_logger()
        self.assertGreater(len(logger.handlers), 0)

    def test_loggers_do_not_propagate(self):
        self.assertFalse(get_exception_logger().propagate)
        self.assertFalse(get_ux_logger().propagate)
        self.assertFalse(get_trace_logger().propagate)
        self.assertFalse(get_app_logger().propagate)

    def test_exception_logger_level(self):
        self.assertEqual(get_exception_logger().level, logging.DEBUG)

    def test_ux_logger_level(self):
        self.assertEqual(get_ux_logger().level, logging.DEBUG)

    def test_trace_logger_level(self):
        self.assertEqual(get_trace_logger().level, logging.DEBUG)


class TestLogFileCreation(unittest.TestCase):
    """Test that log files are created when messages are written."""

    @classmethod
    def setUpClass(cls):
        setup_all_loggers()

    def test_exception_log_file_written(self):
        exc_log = get_exception_logger()
        exc_log.warning("test_exception_log_file_written")
        exc_log.handlers[0].flush()
        path = os.path.join(_LOG_DIR, "exceptions.log")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("test_exception_log_file_written", content)

    def test_ux_log_file_written(self):
        log_ux_action("TestAction", details="detail123")
        ux_log = get_ux_logger()
        ux_log.handlers[0].flush()
        path = os.path.join(_LOG_DIR, "ux_actions.log")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("TestAction", content)
        self.assertIn("detail123", content)

    def test_trace_log_file_written(self):
        @trace
        def _test_traced():
            return 42

        _test_traced()
        tlog = get_trace_logger()
        tlog.handlers[0].flush()
        path = os.path.join(_LOG_DIR, "trace.log")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("_test_traced", content)
        self.assertIn("ENTER", content)
        self.assertIn("EXIT", content)


class TestUXActionLogging(unittest.TestCase):
    """Test UX action log helper functions."""

    @classmethod
    def setUpClass(cls):
        setup_all_loggers()

    def test_log_ux_action_with_context(self):
        log_ux_action("Add Customer", details="name=Alice", user_context="cid=42")
        ux = get_ux_logger()
        ux.handlers[0].flush()
        path = os.path.join(_LOG_DIR, "ux_actions.log")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("ACTION=Add Customer", content)
        self.assertIn("CTX=cid=42", content)
        self.assertIn("DETAILS=name=Alice", content)

    def test_log_ux_action_result_success(self):
        log_ux_action_result("Save Contract", success=True)
        ux = get_ux_logger()
        ux.handlers[0].flush()
        path = os.path.join(_LOG_DIR, "ux_actions.log")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("RESULT=SUCCESS", content)
        self.assertIn("ACTION=Save Contract", content)

    def test_log_ux_action_result_failure(self):
        log_ux_action_result("Delete Truck", success=False, details="not found")
        ux = get_ux_logger()
        ux.handlers[0].flush()
        path = os.path.join(_LOG_DIR, "ux_actions.log")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("RESULT=FAILURE", content)
        self.assertIn("Delete Truck", content)
        self.assertIn("not found", content)


class TestExceptionLogging(unittest.TestCase):
    """Test exception logging helpers."""

    @classmethod
    def setUpClass(cls):
        setup_all_loggers()

    def test_log_exception_with_traceback(self):
        try:
            raise ValueError("test_exception_value")
        except Exception as e:
            log_exception("Test Op", e, context="ctx=unit_test")

        exc = get_exception_logger()
        exc.handlers[0].flush()
        path = os.path.join(_LOG_DIR, "exceptions.log")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("EXCEPTION in Test Op", content)
        self.assertIn("test_exception_value", content)
        self.assertIn("ctx=unit_test", content)
        # Should include traceback
        self.assertIn("Traceback", content)


class TestTraceDecorator(unittest.TestCase):
    """Test the @trace decorator."""

    @classmethod
    def setUpClass(cls):
        setup_all_loggers()
        # Clear trace log for clean tests
        path = os.path.join(_LOG_DIR, "trace.log")
        if os.path.exists(path):
            open(path, "w").close()

    def _get_trace_content(self):
        tlog = get_trace_logger()
        tlog.handlers[0].flush()
        path = os.path.join(_LOG_DIR, "trace.log")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_trace_logs_entry_and_exit(self):
        @trace
        def add(a, b):
            return a + b

        result = add(3, 4)
        self.assertEqual(result, 7)
        content = self._get_trace_content()
        self.assertIn("ENTER", content)
        self.assertIn("add", content)
        self.assertIn("EXIT", content)

    def test_trace_logs_exception(self):
        @trace
        def fail():
            raise RuntimeError("trace_boom")

        with self.assertRaises(RuntimeError):
            fail()

        content = self._get_trace_content()
        self.assertIn("RAISE", content)
        self.assertIn("trace_boom", content)
        self.assertIn("RuntimeError", content)

    def test_trace_preserves_return_value(self):
        @trace
        def multiply(x, y):
            return x * y

        self.assertEqual(multiply(5, 6), 30)

    def test_trace_preserves_function_name(self):
        @trace
        def my_named_func():
            pass

        self.assertEqual(my_named_func.__name__, "my_named_func")

    def test_trace_truncates_long_args(self):
        @trace
        def long_arg_func(data):
            return len(data)

        long_str = "x" * 500
        result = long_arg_func(long_str)
        self.assertEqual(result, 500)
        content = self._get_trace_content()
        self.assertIn("ENTER", content)
        # Should have truncated the arg repr
        self.assertIn("...", content)

    def test_trace_method_works_same_as_trace(self):
        @trace_method
        def my_method():
            return 99

        result = my_method()
        self.assertEqual(result, 99)
        content = self._get_trace_content()
        self.assertIn("my_method", content)

    def test_trace_with_kwargs(self):
        @trace
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = greet("Alice", greeting="Hi")
        self.assertEqual(result, "Hi, Alice!")
        content = self._get_trace_content()
        self.assertIn("Alice", content)

    def test_trace_records_duration(self):
        import time

        @trace
        def slow_func():
            time.sleep(0.05)
            return "done"

        slow_func()
        content = self._get_trace_content()
        self.assertIn("EXIT", content)
        # Duration should be logged
        self.assertIn("s]", content)


class TestSetupIdempotent(unittest.TestCase):
    """Test that calling setup_all_loggers multiple times doesn't duplicate handlers."""

    def test_no_duplicate_handlers(self):
        setup_all_loggers()
        h1 = len(get_exception_logger().handlers)
        setup_all_loggers()
        h2 = len(get_exception_logger().handlers)
        self.assertEqual(h1, h2)

    def test_no_duplicate_ux_handlers(self):
        setup_all_loggers()
        h1 = len(get_ux_logger().handlers)
        setup_all_loggers()
        h2 = len(get_ux_logger().handlers)
        self.assertEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()
