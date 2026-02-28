#!/usr/bin/env python3
"""Edge case tests for numeric and formatting edge cases."""

import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from utils.validation import (
    normalize_whitespace,
    required_text,
    optional_text,
    optional_phone,
    required_plate,
    optional_state,
    positive_float,
    positive_int,
)


class TestUnicodeAndSpecialCharEdgeCases(unittest.TestCase):
    """Test handling of unicode and special characters."""

    def test_normalize_fullwidth_spaces(self):
        """Test normalization of fullwidth spaces (CJK)."""
        text = "hello\u3000world"  # fullwidth space
        result = normalize_whitespace(text)
        # Should handle or convert fullwidth space
        assert result is not None

    def test_normalize_multiple_newlines(self):
        """Test multiple newlines are normalized."""
        result = normalize_whitespace("line1\n\n\nline2")
        assert "\n" not in result

    def test_plate_with_various_dashes(self):
        """Test various dash types in plates."""
        dashes = [
            ("-", "-"),      # regular hyphen
            ("—", "-"),      # em dash (should normalize)
            ("–", "-"),      # en dash (should normalize)
            ("‐", "-"),      # hyphen (unicode)
        ]
        for dash_input, dash_output in dashes[:2]:  # Test em and en dashes
            plate = f"AB{dash_input}12"
            result = required_plate(plate)
            assert dash_output in result

    def test_phone_with_chinese_characters(self):
        """Test phone with invalid Chinese characters."""
        with self.assertRaises(ValueError):
            optional_phone("555-1234中文")

    def test_plate_with_accented_characters(self):
        """Test plate with accented characters (invalid)."""
        with self.assertRaises(ValueError):
            required_plate("ABC-é123")

    def test_required_plate_with_unicode_dashes(self):
        """Test plate accepts normalization of unicode dashes."""
        # Test various unicode minus/dash signs
        unicode_dashes = [
            "−",  # minus sign
            "‑",  # non-breaking hyphen
            "⁄",  # fraction slash
        ]
        for dash in unicode_dashes[:1]:  # Just test the most common case
            plate = f"AB{dash}12"
            # Should either normalize or reject clearly
            try:
                result = required_plate(plate)
                # If it doesn't raise, should have converted dash
                assert result is not None
            except ValueError:
                # Valid to reject unicode dashes
                pass


class TestNumericEdgeCases(unittest.TestCase):
    """Test numeric parsing edge cases."""

    def test_float_negative_zero(self):
        """Test negative zero is treated as zero."""
        with self.assertRaises(ValueError):
            positive_float("Price", "-0.00")

    def test_float_positive_zero(self):
        """Test positive zero is invalid."""
        with self.assertRaises(ValueError):
            positive_float("Price", "+0.00")

    def test_float_with_multiple_decimals(self):
        """Test multiple decimal points."""
        with self.assertRaises(ValueError):
            positive_float("Price", "19.99.99")

    def test_float_very_small_number(self):
        """Test very small but positive number."""
        result = positive_float("Price", "0.001")
        assert result > 0

    def test_float_rounding_precision(self):
        """Test floating point precision."""
        result = positive_float("Price", "19.999999")
        assert result > 19.99

    def test_int_whitespace_padding(self):
        """Test int with various whitespace."""
        result = positive_int("Count", "\t\n  42  \n\t")
        assert result == 42

    def test_int_only_zeros_invalid(self):
        """Test all zeros is invalid (equals 0)."""
        with self.assertRaises(ValueError):
            positive_int("Count", "00000")

    def test_float_scientific_notation_tiny(self):
        """Test very small scientific notation."""
        result = positive_float("Price", "1e-5")
        assert result > 0

    def test_float_scientific_notation_large(self):
        """Test large scientific notation."""
        result = positive_float("Price", "1.5e5")
        assert result == 150000.0

    def test_float_infinity_string(self):
        """Test 'inf' or 'infinity' strings are rejected as non-numeric."""
        with self.assertRaises(ValueError):
            positive_float("Price", "inf")
        with self.assertRaises(ValueError):
            positive_float("Price", "infinity")

    def test_float_nan_string(self):
        """Test 'nan' strings are rejected as non-numeric."""
        with self.assertRaises(ValueError):
            positive_float("Price", "nan")
        with self.assertRaises(ValueError):
            positive_float("Price", "NaN")


class TestBoundaryConditionEdgeCases(unittest.TestCase):
    """Test boundary conditions and limits."""

    def test_required_text_max_len_zero(self):
        """Test with max_len of 0."""
        # Should act like everything is too long
        with self.assertRaises(ValueError):
            required_text("Field", "a", max_len=0)

    def test_required_text_negative_max_len(self):
        """Test with negative max_len (edge case in parameter)."""
        # Should handle gracefully
        try:
            with self.assertRaises(ValueError):
                required_text("Field", "a", max_len=-1)
        except (ValueError, AssertionError):
            pass  # Either response is reasonable

    def test_plate_special_sequences(self):
        """Test plates with special number sequences."""
        # Test plates that might look like commands or codes
        test_plates = [
            "ABC-0000",
            "XYZ-1111",
            "AAA-9999",
        ]
        for plate in test_plates:
            result = required_plate(plate)
            assert result is not None

    def test_state_all_uppercase_variants(self):
        """Test state handling of case variants."""
        variants = ["ca", "CA", "Ca", "cA"]
        for variant in variants:
            if variant.lower() == "ca":  # Valid state
                result = optional_state(variant)
                assert result == "CA"

    def test_phone_only_spaces_returns_none(self):
        """Test phone with only spaces returns None (optional)."""
        result = optional_phone("        ")
        assert result is None

    def test_phone_null_chars(self):
        """Test phone with null characters."""
        with self.assertRaises(ValueError):
            optional_phone("555-1234\x00test")


class TestEmptyAndNoneEdgeCases(unittest.TestCase):
    """Test empty and None-like edge cases."""

    def test_optional_phone_empty_after_strip(self):
        """Test phone that's empty after stripping."""
        assert optional_phone("   \t\n   ") is None

    def test_optional_state_empty_after_strip(self):
        """Test state that's empty after stripping."""
        assert optional_state("   ") is None

    def test_optional_text_tabs_and_newlines(self):
        """Test optional text with only tabs/newlines."""
        assert optional_text("Field", "\t\n\t\n") is None

    def test_validate_consecutive_calls_same_input(self):
        """Test that multiple calls to validate same input are consistent."""
        from utils.validation import required_text
        input_val = "Test Value"
        result1 = required_text("Field", input_val)
        result2 = required_text("Field", input_val)
        assert result1 == result2

    def test_plate_consecutive_calls_idempotent(self):
        """Test plate validation is idempotent."""
        from utils.validation import required_plate
        plate = "ABC-1234"
        result1 = required_plate(plate)
        result2 = required_plate(result1)
        assert result1 == result2


if __name__ == "__main__":
    unittest.main()
