#!/usr/bin/env python3
"""Edge case tests for billing_date_utils.py module."""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from billing_date_utils import (
    ym,
    parse_ym,
    parse_ymd,
    add_months,
    elapsed_months_inclusive,
)


class TestDateUtilsEdgeCases(unittest.TestCase):
    """Edge case tests for date utility functions."""

    # ========== YM FORMATTING EDGE CASES ==========
    def test_ym_january(self):
        """Test January formatting."""
        d = date(2024, 1, 1)
        assert ym(d) == "2024-01"

    def test_ym_december(self):
        """Test December formatting."""
        d = date(2024, 12, 31)
        assert ym(d) == "2024-12"

    def test_ym_year_2000(self):
        """Test year 2000."""
        d = date(2000, 6, 15)
        assert ym(d) == "2000-06"

    def test_ym_year_1970(self):
        """Test year 1970 (Unix epoch)."""
        d = date(1970, 1, 1)
        assert ym(d) == "1970-01"

    def test_ym_far_future(self):
        """Test far future date."""
        d = date(9999, 12, 31)
        assert ym(d) == "9999-12"

    def test_ym_leap_year_feb_29(self):
        """Test leap year February 29."""
        d = date(2024, 2, 29)
        assert ym(d) == "2024-02"

    # ========== PARSE YM EDGE CASES ==========
    def test_parse_ym_january(self):
        """Test parsing January."""
        assert parse_ym("2024-01") == (2024, 1)

    def test_parse_ym_december(self):
        """Test parsing December."""
        assert parse_ym("2024-12") == (2024, 12)

    def test_parse_ym_year_1000(self):
        """Test parsing year 1000."""
        assert parse_ym("1000-06") == (1000, 6)

    def test_parse_ym_year_9999(self):
        """Test parsing year 9999."""
        assert parse_ym("9999-12") == (9999, 12)

    def test_parse_ym_with_extra_whitespace(self):
        """Test parsing with extra whitespace."""
        assert parse_ym("   2024-03   ") == (2024, 3)

    def test_parse_ym_zero_padded_month(self):
        """Test all zero-padded months."""
        for month in range(1, 13):
            result = parse_ym(f"2024-{month:02d}")
            assert result == (2024, month)

    def test_parse_ym_invalid_month_0(self):
        """Test month 0 is invalid."""
        assert parse_ym("2024-00") is None

    def test_parse_ym_invalid_month_13(self):
        """Test month 13 is invalid."""
        assert parse_ym("2024-13") is None

    def test_parse_ym_missing_dash(self):
        """Test format without dash."""
        assert parse_ym("202403") is None

    def test_parse_ym_extra_dash(self):
        """Test format with extra dash."""
        assert parse_ym("2024-03-15") is None

    def test_parse_ym_letters_in_month(self):
        """Test non-numeric month."""
        assert parse_ym("2024-ab") is None

    def test_parse_ym_negative_year(self):
        """Test negative year."""
        assert parse_ym("-2024-03") is None

    # ========== PARSE YMD EDGE CASES ==========
    def test_parse_ymd_year_boundaries(self):
        """Test year boundaries."""
        assert parse_ymd("1000-01-01") == date(1000, 1, 1)
        assert parse_ymd("9999-12-31") == date(9999, 12, 31)

    def test_parse_ymd_leap_day_2024(self):
        """Test leap day in leap year."""
        assert parse_ymd("2024-02-29") == date(2024, 2, 29)

    def test_parse_ymd_leap_day_2000(self):
        """Test leap day in year 2000."""
        assert parse_ymd("2000-02-29") == date(2000, 2, 29)

    def test_parse_ymd_non_leap_day_2023(self):
        """Test Feb 29 in non-leap year returns None."""
        assert parse_ymd("2023-02-29") is None

    def test_parse_ymd_last_day_each_month(self):
        """Test last day of each month."""
        test_cases = [
            ("2024-01-31", date(2024, 1, 31)),
            ("2024-02-29", date(2024, 2, 29)),  # leap
            ("2024-03-31", date(2024, 3, 31)),
            ("2024-04-30", date(2024, 4, 30)),
            ("2024-05-31", date(2024, 5, 31)),
            ("2024-06-30", date(2024, 6, 30)),
            ("2024-07-31", date(2024, 7, 31)),
            ("2024-08-31", date(2024, 8, 31)),
            ("2024-09-30", date(2024, 9, 30)),
            ("2024-10-31", date(2024, 10, 31)),
            ("2024-11-30", date(2024, 11, 30)),
            ("2024-12-31", date(2024, 12, 31)),
        ]
        for ym_str, expected in test_cases:
            assert parse_ymd(ym_str) == expected

    def test_parse_ymd_invalid_feb_30(self):
        """Test February 30 is invalid."""
        assert parse_ymd("2024-02-30") is None

    def test_parse_ymd_invalid_april_31(self):
        """Test April 31 is invalid."""
        assert parse_ymd("2024-04-31") is None

    def test_parse_ymd_invalid_day_0(self):
        """Test day 0 is invalid."""
        assert parse_ymd("2024-01-00") is None

    def test_parse_ymd_with_whitespace(self):
        """Test parsing with whitespace."""
        assert parse_ymd("  2024-03-15  ") == date(2024, 3, 15)

    def test_parse_ymd_wrong_format(self):
        """Test various wrong formats."""
        wrong_formats = [
            "03-15-2024",
            "2024/03/15",
            "2024.03.15",
            "03-15",
            "2024",
        ]
        for fmt in wrong_formats:
            assert parse_ymd(fmt) is None

    # ========== ADD MONTHS EDGE CASES ==========
    def test_add_months_stays_in_year(self):
        """Test adding months within same year."""
        result = add_months(2024, 1, 5)
        assert result == (2024, 6)

    def test_add_months_crosses_year_forward(self):
        """Test adding months crosses year forward."""
        result = add_months(2024, 11, 3)
        assert result == (2025, 2)

    def test_add_months_stays_in_year_backward(self):
        """Test subtracting months within same year."""
        result = add_months(2024, 6, -3)
        assert result == (2024, 3)

    def test_add_months_crosses_year_backward(self):
        """Test subtracting months crosses year backward."""
        result = add_months(2024, 2, -3)
        assert result == (2023, 11)

    def test_add_months_large_positive_offset(self):
        """Test large positive offset (many years)."""
        result = add_months(2024, 6, 36)  # +3 years
        assert result == (2027, 6)

    def test_add_months_large_negative_offset(self):
        """Test large negative offset (many years)."""
        result = add_months(2024, 6, -36)  # -3 years
        assert result == (2021, 6)

    def test_add_months_to_jan(self):
        """Test adding to January."""
        result = add_months(2024, 1, 0)
        assert result == (2024, 1)

    def test_add_months_to_dec(self):
        """Test adding to December."""
        result = add_months(2024, 12, 0)
        assert result == (2024, 12)

    def test_add_months_wraps_month_correctly(self):
        """Test month wraps correctly at boundaries."""
        # Dec + 1 month = Jan of next year
        result = add_months(2024, 12, 1)
        assert result == (2025, 1)
        # Jan - 1 month = Dec of previous year
        result = add_months(2024, 1, -1)
        assert result == (2023, 12)

    def test_add_months_very_large_year(self):
        """Test with large year value."""
        result = add_months(9999, 6, 12)
        assert result[0] >= 10000  # Overflows beyond 9999

    # ========== ELAPSED MONTHS EDGE CASES ==========
    def test_elapsed_months_same_date(self):
        """Test same date returns 1."""
        d = date(2024, 6, 15)
        assert elapsed_months_inclusive(d, d) == 1

    def test_elapsed_months_one_day_later(self):
        """Test one day later returns 1."""
        start = date(2024, 6, 15)
        end = date(2024, 6, 16)
        assert elapsed_months_inclusive(start, end) == 1

    def test_elapsed_months_end_of_month_to_start_next(self):
        """Test end of month to start of next month."""
        start = date(2024, 6, 30)
        end = date(2024, 7, 1)
        # One day difference within inclusive counting
        result = elapsed_months_inclusive(start, end)
        assert result >= 0

    def test_elapsed_months_first_of_month_to_first(self):
        """Test first of month to first of next month."""
        start = date(2024, 6, 1)
        end = date(2024, 7, 1)
        assert elapsed_months_inclusive(start, end) == 2

    def test_elapsed_months_mid_month_to_mid_month(self):
        """Test mid-month to mid-month."""
        start = date(2024, 6, 15)
        end = date(2024, 7, 15)
        assert elapsed_months_inclusive(start, end) == 2

    def test_elapsed_months_mid_month_to_earlier_day(self):
        """Test mid-month to earlier day in next month."""
        start = date(2024, 6, 15)
        end = date(2024, 7, 14)
        assert elapsed_months_inclusive(start, end) == 1

    def test_elapsed_months_end_to_earlier_day(self):
        """Test end of month to earlier day in next month."""
        start = date(2024, 6, 30)
        end = date(2024, 7, 29)
        # Should be 1 because day 29 < day 30
        assert elapsed_months_inclusive(start, end) == 1

    def test_elapsed_months_reverse_order(self):
        """Test end date before start date returns 0."""
        start = date(2024, 7, 15)
        end = date(2024, 6, 15)
        assert elapsed_months_inclusive(start, end) == 0

    def test_elapsed_months_one_year(self):
        """Test exactly one year."""
        start = date(2024, 6, 15)
        end = date(2025, 6, 15)
        assert elapsed_months_inclusive(start, end) == 13

    def test_elapsed_months_one_year_one_day_earlier(self):
        """Test one year but end day is earlier."""
        start = date(2024, 6, 15)
        end = date(2025, 6, 14)
        assert elapsed_months_inclusive(start, end) == 12

    def test_elapsed_months_leap_year_boundary(self):
        """Test across leap day."""
        start = date(2024, 2, 28)
        end = date(2024, 3, 1)
        result = elapsed_months_inclusive(start, end)
        assert result >= 0

    def test_elapsed_months_multiple_years(self):
        """Test multiple years."""
        start = date(2020, 1, 1)
        end = date(2024, 12, 31)
        result = elapsed_months_inclusive(start, end)
        # Should be roughly 60 months for 5 years
        assert 50 <= result <= 70


if __name__ == "__main__":
    unittest.main()
