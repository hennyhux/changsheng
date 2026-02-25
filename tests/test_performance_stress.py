#!/usr/bin/env python3
"""Stress and performance tests for critical functions."""

import sys
from pathlib import Path
from datetime import date
import time

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from validation import (
    normalize_whitespace,
    required_text,
    positive_float,
    required_plate,
)
from billing_date_utils import (
    add_months,
    elapsed_months_inclusive,
    parse_ymd,
    parse_ym,
)


class TestPerformanceValidation(unittest.TestCase):
    """Performance tests for validation functions."""

    def test_performance_normalize_whitespace_bulk(self):
        """Test performance of bulk whitespace normalization."""
        test_strings = [
            "  hello   world  " * 100,
            "a b c d e f g h" * 50,
            "\t\n  mixed  whitespace  \n\t" * 100,
        ]

        start = time.time()
        for _ in range(1000):
            for s in test_strings:
                normalize_whitespace(s)
        elapsed = time.time() - start

        # Should complete 3000 operations in under 1 second
        assert elapsed < 1.0, f"Whitespace normalization too slow: {elapsed}s"

    def test_performance_required_text_validation(self):
        """Test performance of text validation."""
        test_cases = [
            ("Field", "Simple text"),
            ("Field", "Text with spaces   and   tabs"),
            ("Field", "Special chars !@#$%^&*()"),
        ]

        start = time.time()
        for _ in range(1000):
            for label, value in test_cases:
                required_text(label, value)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Text validation too slow: {elapsed}s"

    def test_performance_positive_float_parsing(self):
        """Test performance of float parsing."""
        test_cases = [
            "1234.56",
            "$1,234.56",
            "9999.99",
            "0.01",
        ]

        start = time.time()
        for _ in range(1000):
            for value in test_cases:
                positive_float("Price", value)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Float parsing too slow: {elapsed}s"

    def test_performance_plate_validation(self):
        """Test performance of plate validation."""
        test_cases = [
            "ABC-1234",
            "TX-XYZ-999",
            "ABCDEFGH",
        ]

        start = time.time()
        for _ in range(1000):
            for plate in test_cases:
                required_plate(plate)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Plate validation too slow: {elapsed}s"


class TestPerformanceDateFunctions(unittest.TestCase):
    """Performance tests for date functions."""

    def test_performance_add_months_bulk(self):
        """Test performance of bulk month addition."""
        test_cases = [
            (2024, 1, 6),
            (2024, 6, -3),
            (2024, 12, 1),
            (2024, 1, 36),
        ]

        start = time.time()
        for _ in range(10000):
            for y, m, delta in test_cases:
                add_months(y, m, delta)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Month addition too slow: {elapsed}s"

    def test_performance_elapsed_months_bulk(self):
        """Test performance of bulk elapsed months calculation."""
        start_d = date(2024, 1, 15)
        end_dates = [
            date(2024, 1, 15),
            date(2024, 6, 15),
            date(2025, 1, 15),
        ]

        start = time.time()
        for _ in range(10000):
            for end_d in end_dates:
                elapsed_months_inclusive(start_d, end_d)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Elapsed months too slow: {elapsed}s"

    def test_performance_parse_ymd_bulk(self):
        """Test performance of bulk YMD parsing."""
        test_dates = [
            "2024-01-15",
            "2024-06-30",
            "2024-12-31",
        ]

        start = time.time()
        for _ in range(10000):
            for d in test_dates:
                parse_ymd(d)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"YMD parsing too slow: {elapsed}s"

    def test_performance_parse_ym_bulk(self):
        """Test performance of bulk YM parsing."""
        test_months = [
            "2024-01",
            "2024-06",
            "2024-12",
        ]

        start = time.time()
        for _ in range(10000):
            for m in test_months:
                parse_ym(m)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"YM parsing too slow: {elapsed}s"


class TestStressExtremeCases(unittest.TestCase):
    """Stress tests with extreme edge cases."""

    def test_stress_very_long_text_fields(self):
        """Test validation with extremely long text."""
        # 10,000 character string
        long_text = "A" * 10000
        
        # With reasonable max length, should raise
        with self.assertRaises(ValueError):
            required_text("Field", long_text, max_len=1000)

    def test_stress_many_months_addition(self):
        """Test adding very large number of months."""
        year, month = 2024, 1
        
        # Add 1200 months (100 years)
        result_year, result_month = add_months(year, month, 1200)
        
        # Should end up at 2124, January
        assert result_year == 2124
        assert result_month == 1

    def test_stress_very_distant_date_range(self):
        """Test elapsed months for very distant dates."""
        start = date(1970, 1, 1)
        end = date(2024, 2, 24)
        
        months = elapsed_months_inclusive(start, end)
        
        # Roughly 54 years * 12 = 648 months
        assert 640 < months < 660


class TestConsistency(unittest.TestCase):
    """Test consistency and idempotency of functions."""

    def test_consistency_add_months_reverse(self):
        """Test that add_months and its reverse are consistent."""
        y, m = 2024, 6
        delta = 7
        
        # Add 7 months
        y1, m1 = add_months(y, m, delta)
        
        # Subtract 7 months
        y2, m2 = add_months(y1, m1, -delta)
        
        # Should get back to original
        assert (y2, m2) == (y, m)

    def test_consistency_multiple_normalizations(self):
        """Test that multiple normalizations are idempotent."""
        text = "  hello   world  "
        
        norm1 = normalize_whitespace(text)
        norm2 = normalize_whitespace(norm1)
        norm3 = normalize_whitespace(norm2)
        
        # All should be identical
        assert norm1 == norm2 == norm3

    def test_consistency_plate_uppercase_normalization(self):
        """Test that plate normalization is consistent."""
        plates = ["abc-1234", "ABC-1234", "AbC-1234"]
        
        results = [required_plate(p) for p in plates]
        
        # All should normalize to same value
        assert results[0] == results[1] == results[2]


if __name__ == "__main__":
    unittest.main()
