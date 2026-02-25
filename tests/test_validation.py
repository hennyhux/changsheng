#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for validation.py module."""

import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from validation import (
    normalize_whitespace,
    required_text,
    optional_text,
    optional_phone,
    required_plate,
    optional_state,
    positive_float,
    positive_int,
)


class TestNormalizeWhitespace(unittest.TestCase):
    """Test whitespace normalization."""

    def test_normalize_single_space(self):
        """Test that multiple spaces are reduced to single."""
        assert normalize_whitespace("hello  world") == "hello world"

    def test_normalize_leading_trailing(self):
        """Test that leading/trailing whitespace is removed."""
        assert normalize_whitespace("  hello world  ") == "hello world"

    def test_normalize_tabs_and_newlines(self):
        """Test that tabs and newlines are normalized."""
        assert normalize_whitespace("hello\t\tworld\n") == "hello world"

    def test_normalize_empty(self):
        """Test that empty string remains empty."""
        assert normalize_whitespace("") == ""


class TestRequiredText(unittest.TestCase):
    """Test required_text validation."""

    def test_valid_text(self):
        """Test valid text passes."""
        result = required_text("Name", "John Smith")
        assert result == "John Smith"

    def test_empty_string_raises(self):
        """Test that empty string raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            required_text("Name", "")
        assert "required" in str(cm.exception)

    def test_whitespace_only_raises(self):
        """Test that whitespace-only string raises ValueError."""
        with self.assertRaises(ValueError):
            required_text("Name", "   ")

    def test_max_length_enforced(self):
        """Test that max length is enforced."""
        with self.assertRaises(ValueError) as cm:
            required_text("Name", "a" * 101, max_len=100)
        assert "characters or fewer" in str(cm.exception)

    def test_max_length_boundary(self):
        """Test that exactly max_len is allowed."""
        result = required_text("Name", "a" * 100, max_len=100)
        assert result == "a" * 100


class TestOptionalText(unittest.TestCase):
    """Test optional_text validation."""

    def test_valid_text(self):
        """Test valid text passes."""
        result = optional_text("Notes", "Some notes here")
        assert result == "Some notes here"

    def test_empty_returns_none(self):
        """Test that empty string returns None."""
        assert optional_text("Notes", "") is None

    def test_whitespace_only_returns_none(self):
        """Test that whitespace-only string returns None."""
        assert optional_text("Notes", "   ") is None

    def test_max_length_enforced(self):
        """Test that max length is enforced."""
        with self.assertRaises(ValueError):
            optional_text("Notes", "a" * 201, max_len=200)


class TestOptionalPhone(unittest.TestCase):
    """Test optional_phone validation."""

    def test_empty_returns_none(self):
        """Test that empty string returns None."""
        assert optional_phone("") is None

    def test_valid_10_digit_phone(self):
        """Test valid 10-digit phone."""
        result = optional_phone("(555) 123-4567")
        assert result == "(555) 123-4567"

    def test_valid_phone_variations(self):
        """Test various valid phone formats."""
        valid_phones = [
            "555-123-4567",
            "5551234567",
            "(555)123-4567",
        ]
        for phone in valid_phones:
            result = optional_phone(phone)
            assert result is not None

    def test_invalid_phone_raises(self):
        """Test that invalid phone raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            optional_phone("invalid")
        assert "format" in str(cm.exception).lower()


class TestRequiredPlate(unittest.TestCase):
    """Test required_plate validation."""

    def test_empty_raises(self):
        """Test that empty string raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            required_plate("")
        assert "required" in str(cm.exception).lower()

    def test_valid_plate(self):
        """Test valid plate."""
        result = required_plate("ABC-1234")
        assert result == "ABC-1234"

    def test_plate_uppercase_conversion(self):
        """Test that plate is converted to uppercase."""
        result = required_plate("abc-1234")
        assert result == "ABC-1234"

    def test_plate_dash_normalization(self):
        """Test that special dashes are normalized."""
        result = required_plate("ABC—1234")  # em dash
        assert result == "ABC-1234"

    def test_plate_with_space(self):
        """Test plate with space."""
        result = required_plate("ABC 1234")
        assert result == "ABC 1234"

    def test_invalid_plate_too_long(self):
        """Test that plate longer than 15 chars raises."""
        with self.assertRaises(ValueError):
            required_plate("A" * 20)

    def test_invalid_plate_special_chars(self):
        """Test that special characters are rejected."""
        with self.assertRaises(ValueError):
            required_plate("ABC@1234")


class TestOptionalState(unittest.TestCase):
    """Test optional_state validation."""

    def test_empty_returns_none(self):
        """Test that empty string returns None."""
        assert optional_state("") is None

    def test_valid_state(self):
        """Test valid 2-letter state."""
        result = optional_state("TX")
        assert result == "TX"

    def test_lowercase_converted_to_upper(self):
        """Test that lowercase is converted to uppercase."""
        result = optional_state("tx")
        assert result == "TX"

    def test_invalid_state_too_short(self):
        """Test that 1-letter state raises."""
        with self.assertRaises(ValueError):
            optional_state("T")

    def test_invalid_state_too_long(self):
        """Test that 3+ letter state raises."""
        with self.assertRaises(ValueError):
            optional_state("TEX")

    def test_invalid_state_with_numbers(self):
        """Test that state with numbers raises."""
        with self.assertRaises(ValueError):
            optional_state("T1")


class TestPositiveFloat(unittest.TestCase):
    """Test positive_float validation."""

    def test_valid_float(self):
        """Test valid float."""
        result = positive_float("Price", "19.99")
        assert result == 19.99

    def test_float_with_dollar_sign(self):
        """Test float with dollar sign."""
        result = positive_float("Price", "$19.99")
        assert result == 19.99

    def test_float_with_comma_thousands(self):
        """Test float with comma thousands separator."""
        result = positive_float("Price", "$1,234.56")
        assert result == 1234.56

    def test_empty_raises(self):
        """Test that empty string raises."""
        with self.assertRaises(ValueError) as cm:
            positive_float("Price", "")
        assert "required" in str(cm.exception).lower()

    def test_zero_raises(self):
        """Test that zero raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            positive_float("Price", "0")
        assert "greater than 0" in str(cm.exception).lower()

    def test_negative_raises(self):
        """Test that negative number raises ValueError."""
        with self.assertRaises(ValueError):
            positive_float("Price", "-5.00")

    def test_non_numeric_raises(self):
        """Test that non-numeric raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            positive_float("Price", "abc")
        assert "numeric" in str(cm.exception).lower()


class TestPositiveInt(unittest.TestCase):
    """Test positive_int validation."""

    def test_valid_int(self):
        """Test valid integer."""
        result = positive_int("Count", "42")
        assert result == 42

    def test_empty_raises(self):
        """Test that empty string raises."""
        with self.assertRaises(ValueError) as cm:
            positive_int("Count", "")
        assert "required" in str(cm.exception).lower()

    def test_zero_raises(self):
        """Test that zero raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            positive_int("Count", "0")
        assert "greater than 0" in str(cm.exception).lower()

    def test_negative_raises(self):
        """Test that negative number raises ValueError."""
        with self.assertRaises(ValueError):
            positive_int("Count", "-5")

    def test_float_raises(self):
        """Test that float raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            positive_int("Count", "5.5")
        assert "whole number" in str(cm.exception).lower()

    def test_non_numeric_raises(self):
        """Test that non-numeric raises ValueError."""
        with self.assertRaises(ValueError):
            positive_int("Count", "abc")


if __name__ == "__main__":
    unittest.main()
