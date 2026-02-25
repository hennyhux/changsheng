#!/usr/bin/env python3
"""Unit tests for ui_actions.py utility functions."""

import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from validation import (
    required_text,
    optional_phone,
    required_plate,
    positive_float,
)


class TestUiActionsCustomerValidation(unittest.TestCase):
    """Test validation logic used in UI actions."""

    def test_validate_customer_name(self):
        """Test customer name validation."""
        name = required_text("Customer Name", "ABC Logistics")
        assert name == "ABC Logistics"

    def test_validate_customer_name_empty_fails(self):
        """Test empty customer name fails."""
        with self.assertRaises(ValueError):
            required_text("Customer Name", "")

    def test_validate_customer_phone_optional(self):
        """Test customer phone is optional."""
        # Empty phone should return None
        result = optional_phone("")
        assert result is None

    def test_validate_customer_phone_valid(self):
        """Test valid customer phone."""
        result = optional_phone("555-123-4567")
        assert result is not None

    def test_validate_customer_phone_invalid(self):
        """Test invalid customer phone."""
        with self.assertRaises(ValueError):
            optional_phone("invalid")


class TestUiActionsTruckValidation(unittest.TestCase):
    """Test truck validation logic."""

    def test_validate_plate_required(self):
        """Test truck plate is required."""
        plate = required_plate("TX-ABC-001")
        assert plate == "TX-ABC-001"

    def test_validate_plate_empty_fails(self):
        """Test empty plate fails."""
        with self.assertRaises(ValueError):
            required_plate("")

    def test_validate_plate_normalization(self):
        """Test plate normalization."""
        plate = required_plate("tx-abc-001")
        assert plate == "TX-ABC-001"


class TestUiActionsContractValidation(unittest.TestCase):
    """Test contract validation logic."""

    def test_validate_contract_rate(self):
        """Test contract rate validation."""
        rate = positive_float("Monthly Rate", "1500.00")
        assert rate == 1500.0

    def test_validate_contract_rate_with_currency(self):
        """Test rate validation with currency symbol."""
        rate = positive_float("Monthly Rate", "$1,500.00")
        assert rate == 1500.0

    def test_validate_contract_rate_zero_fails(self):
        """Test zero rate fails."""
        with self.assertRaises(ValueError):
            positive_float("Monthly Rate", "0.00")

    def test_validate_contract_rate_negative_fails(self):
        """Test negative rate fails."""
        with self.assertRaises(ValueError):
            positive_float("Monthly Rate", "-100.00")


class TestUiActionsPaymentValidation(unittest.TestCase):
    """Test payment validation logic."""

    def test_validate_payment_amount(self):
        """Test payment amount validation."""
        amount = positive_float("Payment Amount", "500.00")
        assert amount == 500.0

    def test_validate_payment_with_symbols(self):
        """Test payment with currency symbols."""
        amount = positive_float("Payment Amount", "$1,234.56")
        assert amount == 1234.56

    def test_validate_payment_minimum(self):
        """Test payment must be positive."""
        with self.assertRaises(ValueError):
            positive_float("Payment Amount", "0.00")

    def test_validate_payment_currency_format(self):
        """Test various currency formats."""
        formats = [
            "100.00",
            "$100.00",
            "100",
            "$100",
            "$1,000.00",
        ]
        for fmt in formats:
            result = positive_float("Amount", fmt)
            assert result > 0


class TestUiActionsFormValidation(unittest.TestCase):
    """Test form-level validation logic."""

    def test_multi_field_validation_pass(self):
        """Test validating multiple fields together."""
        customer = required_text("Name", "Test Customer")
        plate = required_plate("TEST-001")
        rate = positive_float("Rate", "500.00")
        
        assert customer is not None
        assert plate is not None
        assert rate > 0

    def test_multi_field_validation_fail_on_first(self):
        """Test validation stops on first failure."""
        with self.assertRaises(ValueError):
            required_text("Name", "")

    def test_multi_field_validation_fail_on_second(self):
        """Test validation fails on second field."""
        customer = required_text("Name", "Valid")
        
        with self.assertRaises(ValueError):
            required_plate("")

    def test_sequential_validation_chain(self):
        """Test chaining validations."""
        try:
            name = required_text("Name", "Test")
            plate = required_plate("ABC-123")
            rate = positive_float("Rate", "100")
            
            all_valid = name and plate and rate > 0
            assert all_valid
        except ValueError:
            self.fail("Validation chain failed unexpectedly")


class TestUiActionsErrorHandling(unittest.TestCase):
    """Test error handling in validation."""

    def test_validation_error_message_readable(self):
        """Test that error messages are readable."""
        try:
            required_text("Customer Name", "")
        except ValueError as e:
            assert "required" in str(e).lower()

    def test_validation_provides_field_context(self):
        """Test that error includes field name."""
        try:
            positive_float("Monthly Rate", "-100")
        except ValueError as e:
            error_msg = str(e).lower()
            assert "rate" in error_msg or "greater than 0" in error_msg

    def test_multiple_validation_errors(self):
        """Test handling multiple validation errors."""
        errors = []
        
        try:
            required_text("Name", "")
        except ValueError as e:
            errors.append(str(e))
        
        try:
            required_plate("")
        except ValueError as e:
            errors.append(str(e))
        
        assert len(errors) == 2


class TestUiActionsDataFormats(unittest.TestCase):
    """Test handling of various data formats."""

    def test_phone_formats(self):
        """Test various phone formats are accepted."""
        formats = [
            "555-123-4567",
            "(555) 123-4567",
            "5551234567",
            "555.123.4567",
        ]
        for fmt in formats:
            result = optional_phone(fmt)
            assert result is not None

    def test_plate_formats(self):
        """Test various plate formats."""
        plates = [
            "ABC-1234",
            "ABC 1234",
            "ABCDEFGH",
        ]
        for plate in plates:
            result = required_plate(plate)
            assert result is not None

    def test_currency_formats(self):
        """Test various currency formats."""
        amounts = [
            "100",
            "100.00",
            "$100",
            "$100.00",
            "$1,000",
            "$1,000.00",
        ]
        for amount in amounts:
            result = positive_float("Amount", amount)
            assert result > 0

    def test_whitespace_handling(self):
        """Test whitespace handling in validation."""
        # Names with extra whitespace
        name = required_text("Name", "  John  Smith  ")
        assert "John Smith" == name

        # Phone with whitespace
        phone = optional_phone("  555-123-4567  ")
        assert phone is not None


if __name__ == "__main__":
    unittest.main()
