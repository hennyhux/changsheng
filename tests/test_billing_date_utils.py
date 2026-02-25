#!/usr/bin/env python3
"""Unit tests for billing_date_utils.py module."""

import sys
from pathlib import Path
from datetime import date, datetime

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from billing_date_utils import (
    now_iso,
    today,
    ym,
    parse_ym,
    parse_ymd,
    add_months,
    elapsed_months_inclusive,
)


class TestNowIso(unittest.TestCase):
    """Test now_iso function."""

    def test_now_iso_format(self):
        """Test that now_iso returns ISO format without microseconds."""
        result = now_iso()
        # Should be able to parse as ISO
        dt = datetime.fromisoformat(result)
        assert dt is not None

    def test_now_iso_no_microseconds(self):
        """Test that microseconds are removed."""
        result = now_iso()
        assert "." not in result


class TestToday(unittest.TestCase):
    """Test today function."""

    def test_today_returns_date(self):
        """Test that today returns a date object."""
        result = today()
        assert isinstance(result, date)

    def test_today_is_current(self):
        """Test that today matches current date."""
        result = today()
        assert result == datetime.now().date()


class TestYm(unittest.TestCase):
    """Test ym (year-month) formatting function."""

    def test_ym_format(self):
        """Test that ym formats date as YYYY-MM."""
        d = date(2024, 3, 15)
        result = ym(d)
        assert result == "2024-03"

    def test_ym_single_digit_month(self):
        """Test that single digit months are zero-padded."""
        d = date(2024, 1, 15)
        result = ym(d)
        assert result == "2024-01"

    def test_ym_december(self):
        """Test December formatting."""
        d = date(2024, 12, 25)
        result = ym(d)
        assert result == "2024-12"


class TestParseYm(unittest.TestCase):
    """Test parse_ym (parse year-month) function."""

    def test_parse_ym_valid(self):
        """Test parsing valid YYYY-MM format."""
        result = parse_ym("2024-03")
        assert result == (2024, 3)

    def test_parse_ym_single_digit_month(self):
        """Test parsing with single digit month."""
        result = parse_ym("2024-01")
        assert result == (2024, 1)

    def test_parse_ym_december(self):
        """Test parsing December."""
        result = parse_ym("2024-12")
        assert result == (2024, 12)

    def test_parse_ym_invalid_format(self):
        """Test that invalid format returns None."""
        result = parse_ym("03-2024")
        assert result is None

    def test_parse_ym_invalid_month(self):
        """Test that invalid month returns None."""
        result = parse_ym("2024-13")
        assert result is None

    def test_parse_ym_empty_string(self):
        """Test that empty string returns None."""
        result = parse_ym("")
        assert result is None

    def test_parse_ym_with_whitespace(self):
        """Test that whitespace is handled."""
        result = parse_ym("  2024-03  ")
        assert result == (2024, 3)


class TestParseYmd(unittest.TestCase):
    """Test parse_ymd (parse year-month-day) function."""

    def test_parse_ymd_valid(self):
        """Test parsing valid YYYY-MM-DD format."""
        result = parse_ymd("2024-03-15")
        assert result == date(2024, 3, 15)

    def test_parse_ymd_jan_first(self):
        """Test parsing January 1st."""
        result = parse_ymd("2024-01-01")
        assert result == date(2024, 1, 1)

    def test_parse_ymd_leap_day(self):
        """Test parsing leap day."""
        result = parse_ymd("2024-02-29")
        assert result == date(2024, 2, 29)

    def test_parse_ymd_invalid_format(self):
        """Test that invalid format returns None."""
        result = parse_ymd("03-15-2024")
        assert result is None

    def test_parse_ymd_invalid_date(self):
        """Test that invalid date returns None."""
        result = parse_ymd("2024-02-30")
        assert result is None

    def test_parse_ymd_empty_string(self):
        """Test that empty string returns None."""
        result = parse_ymd("")
        assert result is None

    def test_parse_ymd_with_whitespace(self):
        """Test that whitespace is handled."""
        result = parse_ymd("  2024-03-15  ")
        assert result == date(2024, 3, 15)


class TestAddMonths(unittest.TestCase):
    """Test add_months function."""

    def test_add_months_positive(self):
        """Test adding months."""
        result = add_months(2024, 3, 2)
        assert result == (2024, 5)

    def test_add_months_year_boundary(self):
        """Test adding months across year boundary."""
        result = add_months(2024, 11, 2)
        assert result == (2025, 1)

    def test_add_months_negative(self):
        """Test subtracting months."""
        result = add_months(2024, 3, -2)
        assert result == (2024, 1)

    def test_add_months_negative_year_boundary(self):
        """Test subtracting months across year boundary."""
        result = add_months(2024, 1, -2)
        assert result == (2023, 11)

    def test_add_months_zero(self):
        """Test adding zero months."""
        result = add_months(2024, 6, 0)
        assert result == (2024, 6)

    def test_add_months_large_positive(self):
        """Test adding large number of months."""
        result = add_months(2024, 1, 12)
        assert result == (2025, 1)

    def test_add_months_large_negative(self):
        """Test subtracting large number of months."""
        result = add_months(2024, 1, -12)
        assert result == (2023, 1)


class TestElapsedMonthsInclusive(unittest.TestCase):
    """Test elapsed_months_inclusive function."""

    def test_same_day_same_month(self):
        """Test that same day counts as 1 month."""
        start = date(2024, 3, 15)
        end = date(2024, 3, 15)
        result = elapsed_months_inclusive(start, end)
        assert result == 1

    def test_same_month_one_day_apart(self):
        """Test consecutive days in same month."""
        start = date(2024, 3, 15)
        end = date(2024, 3, 16)
        result = elapsed_months_inclusive(start, end)
        assert result == 1

    def test_consecutive_months_same_day(self):
        """Test consecutive months on same day."""
        start = date(2024, 3, 15)
        end = date(2024, 4, 15)
        result = elapsed_months_inclusive(start, end)
        assert result == 2

    def test_consecutive_months_earlier_day(self):
        """Test consecutive months with earlier end day."""
        start = date(2024, 3, 15)
        end = date(2024, 4, 14)
        result = elapsed_months_inclusive(start, end)
        assert result == 1

    def test_end_before_start_returns_zero(self):
        """Test that end before start returns 0."""
        start = date(2024, 4, 15)
        end = date(2024, 3, 15)
        result = elapsed_months_inclusive(start, end)
        assert result == 0

    def test_six_months_apart(self):
        """Test 6 months apart."""
        start = date(2024, 1, 15)
        end = date(2024, 6, 15)
        result = elapsed_months_inclusive(start, end)
        assert result == 6

    def test_year_apart(self):
        """Test 1 year apart."""
        start = date(2024, 3, 15)
        end = date(2025, 3, 15)
        result = elapsed_months_inclusive(start, end)
        assert result == 13

    def test_year_apart_earlier_day(self):
        """Test 1 year apart with earlier end day."""
        start = date(2024, 3, 15)
        end = date(2025, 3, 14)
        result = elapsed_months_inclusive(start, end)
        assert result == 12


if __name__ == "__main__":
    unittest.main()
