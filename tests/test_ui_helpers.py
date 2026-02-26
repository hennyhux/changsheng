#!/usr/bin/env python3
"""Unit tests for ui_helpers.py module."""

import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
import tkinter as tk
from tkinter import ttk

from ui.ui_helpers import (
    get_entry_value,
    clear_inline_errors,
)
from utils.billing_date_utils import today


class TestGetEntryValue(unittest.TestCase):
    """Test get_entry_value function."""

    def setUp(self):
        """Create a root window for testing."""
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        """Destroy the root window."""
        self.root.destroy()

    def test_get_entry_value_normal(self):
        """Test getting value from normal entry."""
        entry = ttk.Entry(self.root)
        entry.insert(0, "test value")
        entry._has_placeholder = False
        
        result = get_entry_value(entry)
        assert result == "test value"

    def test_get_entry_value_with_placeholder(self):
        """Test that placeholder text is not returned."""
        entry = ttk.Entry(self.root)
        entry.insert(0, "placeholder")
        entry._has_placeholder = True
        entry._placeholder_text = "placeholder"
        
        result = get_entry_value(entry)
        assert result == ""

    def test_get_entry_value_empty(self):
        """Test getting value from empty entry."""
        entry = ttk.Entry(self.root)
        entry._has_placeholder = False
        
        result = get_entry_value(entry)
        assert result == ""

    def test_get_entry_value_no_placeholder_attr(self):
        """Test entry without placeholder attribute."""
        entry = ttk.Entry(self.root)
        entry.insert(0, "value")
        # No _has_placeholder attribute
        
        result = get_entry_value(entry)
        assert result == "value"

    def test_get_entry_value_with_special_chars(self):
        """Test entry value with special characters."""
        entry = ttk.Entry(self.root)
        entry.insert(0, "Test@#$%^&*()")
        entry._has_placeholder = False
        
        result = get_entry_value(entry)
        assert result == "Test@#$%^&*()"

    def test_get_entry_value_with_unicode(self):
        """Test entry value with unicode characters."""
        entry = ttk.Entry(self.root)
        entry.insert(0, "你好世界")
        entry._has_placeholder = False
        
        result = get_entry_value(entry)
        assert result == "你好世界"


class TestClearInlineErrors(unittest.TestCase):
    """Test clear_inline_errors function."""

    def setUp(self):
        """Create a root window for testing."""
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        """Destroy the root window."""
        self.root.destroy()

    def test_clear_no_errors(self):
        """Test clearing when no errors exist."""
        frame = tk.Frame(self.root)
        frame.pack()
        
        # Should not raise
        clear_inline_errors(frame)

    def test_clear_error_labels(self):
        """Test clearing error labels."""
        frame = tk.Frame(self.root)
        frame.pack()
        
        # Create error labels
        error1 = tk.Label(frame, background="#ffebee")
        error1.grid()
        
        error2 = tk.Label(frame, background="#ffebee")
        error2.grid()
        
        # Create non-error label
        normal = tk.Label(frame, background="white")
        normal.grid()
        
        # Clear errors
        clear_inline_errors(frame)
        
        # Error labels should be hidden
        assert error1.grid_info() == {}
        assert error2.grid_info() == {}
        # Normal label should still be visible
        assert normal.grid_info() != {}

    def test_clear_preserves_non_error_widgets(self):
        """Test that non-error widgets are preserved."""
        frame = tk.Frame(self.root)
        frame.pack()
        
        # Create various widgets
        button = tk.Button(frame, text="Test")
        button.grid()
        
        entry = tk.Entry(frame)
        entry.grid()
        
        error = tk.Label(frame, background="#ffebee")
        error.grid()
        
        # Clear errors
        clear_inline_errors(frame)
        
        # Non-error widgets should still be visible
        assert button.grid_info() != {}
        assert entry.grid_info() != {}
        # Error should be hidden
        assert error.grid_info() == {}


class TestEntryValueExtraction(unittest.TestCase):
    """Test extraction of values from various entry configurations."""

    def setUp(self):
        """Create a root window for testing."""
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        """Destroy the root window."""
        self.root.destroy()

    def test_entry_value_long_string(self):
        """Test entry with long string value."""
        entry = ttk.Entry(self.root)
        long_string = "a" * 1000
        entry.insert(0, long_string)
        entry._has_placeholder = False
        
        result = get_entry_value(entry)
        assert result == long_string

    def test_entry_value_with_leading_trailing_spaces(self):
        """Test entry preserves leading/trailing spaces."""
        entry = ttk.Entry(self.root)
        entry.insert(0, "  spaced value  ")
        entry._has_placeholder = False
        
        result = get_entry_value(entry)
        assert result == "  spaced value  "

    def test_entry_value_numbers(self):
        """Test entry with numeric value."""
        entry = ttk.Entry(self.root)
        entry.insert(0, "123456789")
        entry._has_placeholder = False
        
        result = get_entry_value(entry)
        assert result == "123456789"

    def test_entry_value_empty_vs_placeholder(self):
        """Test distinction between empty and placeholder."""
        entry1 = ttk.Entry(self.root)
        entry1._has_placeholder = False
        
        entry2 = ttk.Entry(self.root)
        entry2.insert(0, "placeholder")
        entry2._has_placeholder = True
        
        assert get_entry_value(entry1) == ""
        assert get_entry_value(entry2) == ""
        assert get_entry_value(entry1) == get_entry_value(entry2)


if __name__ == "__main__":
    unittest.main()
