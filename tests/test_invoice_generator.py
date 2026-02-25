#!/usr/bin/env python3
"""Unit tests for invoice_generator.py helper functions."""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from invoice_generator import (
    _parse_ymd,
    _elapsed_months_inclusive,
    _add_months,
)


class TestInvoiceGeneratorParseYmd(unittest.TestCase):
    """Test invoice generator YMD parsing."""

    def test_parse_ymd_valid(self):
        """Test valid YMD parsing."""
        result = _parse_ymd("2024-03-15")
        assert result == date(2024, 3, 15)

    def test_parse_ymd_with_whitespace(self):
        """Test YMD parsing with whitespace."""
        result = _parse_ymd("  2024-03-15  ")
        assert result == date(2024, 3, 15)

    def test_parse_ymd_none_input(self):
        """Test YMD parsing with None input."""
        result = _parse_ymd(None)
        assert result is None

    def test_parse_ymd_empty_string(self):
        """Test YMD parsing with empty string."""
        result = _parse_ymd("")
        assert result is None

    def test_parse_ymd_invalid_format(self):
        """Test YMD parsing with invalid format."""
        result = _parse_ymd("03-15-2024")
        assert result is None

    def test_parse_ymd_leap_day(self):
        """Test YMD parsing with leap day."""
        result = _parse_ymd("2024-02-29")
        assert result == date(2024, 2, 29)

    def test_parse_ymd_invalid_leap_day(self):
        """Test YMD parsing with invalid leap day."""
        result = _parse_ymd("2023-02-29")
        assert result is None


class TestInvoiceGeneratorElapsedMonths(unittest.TestCase):
    """Test invoice generator elapsed months calculation."""

    def test_elapsed_months_same_day(self):
        """Test elapsed months for same day."""
        start = date(2024, 3, 15)
        end = date(2024, 3, 15)
        result = _elapsed_months_inclusive(start, end)
        assert result == 1

    def test_elapsed_months_one_month(self):
        """Test elapsed months for one month."""
        start = date(2024, 3, 15)
        end = date(2024, 4, 15)
        result = _elapsed_months_inclusive(start, end)
        assert result == 2

    def test_elapsed_months_six_months(self):
        """Test elapsed months for six months."""
        start = date(2024, 1, 15)
        end = date(2024, 6, 15)
        result = _elapsed_months_inclusive(start, end)
        assert result == 6

    def test_elapsed_months_one_year(self):
        """Test elapsed months for one year."""
        start = date(2024, 3, 15)
        end = date(2025, 3, 15)
        result = _elapsed_months_inclusive(start, end)
        assert result == 13

    def test_elapsed_months_end_before_start(self):
        """Test elapsed months when end is before start."""
        start = date(2024, 4, 15)
        end = date(2024, 3, 15)
        result = _elapsed_months_inclusive(start, end)
        assert result == 0

    def test_elapsed_months_day_boundary(self):
        """Test elapsed months at day boundary."""
        start = date(2024, 3, 31)
        end = date(2024, 4, 30)
        result = _elapsed_months_inclusive(start, end)
        # Day 30 < day 31, so doesn't count full month
        assert result == 1

    def test_elapsed_months_multiple_years(self):
        """Test elapsed months across multiple years."""
        start = date(2022, 1, 15)
        end = date(2024, 1, 15)
        result = _elapsed_months_inclusive(start, end)
        assert result == 25

    def test_elapsed_months_leap_year(self):
        """Test elapsed months across leap year."""
        start = date(2024, 2, 29)
        end = date(2024, 3, 29)
        result = _elapsed_months_inclusive(start, end)
        assert result == 2


class TestInvoiceGeneratorAddMonths(unittest.TestCase):
    """Test invoice generator month addition."""

    def test_add_months_positive(self):
        """Test adding positive months."""
        result = _add_months(2024, 3, 2)
        assert result == (2024, 5)

    def test_add_months_year_boundary(self):
        """Test adding months across year boundary."""
        result = _add_months(2024, 11, 2)
        assert result == (2025, 1)

    def test_add_months_negative(self):
        """Test subtracting months."""
        result = _add_months(2024, 3, -2)
        assert result == (2024, 1)

    def test_add_months_negative_year_boundary(self):
        """Test subtracting months across year boundary."""
        result = _add_months(2024, 1, -2)
        assert result == (2023, 11)

    def test_add_months_zero(self):
        """Test adding zero months."""
        result = _add_months(2024, 6, 0)
        assert result == (2024, 6)

    def test_add_months_large_offset(self):
        """Test adding large offset."""
        result = _add_months(2024, 1, 36)
        assert result == (2027, 1)

    def test_add_months_wraps_correctly(self):
        """Test month wrapping is correct."""
        # Add 12 months should stay same month
        result = _add_months(2024, 6, 12)
        assert result == (2025, 6)

    def test_add_months_to_december(self):
        """Test adding to December."""
        result = _add_months(2024, 12, 1)
        assert result == (2025, 1)

    def test_add_months_from_january(self):
        """Test subtracting from January."""
        result = _add_months(2024, 1, -1)
        assert result == (2023, 12)


if __name__ == "__main__":
    unittest.main()
