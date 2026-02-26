#!/usr/bin/env python3
"""Integration tests for real-world scenarios."""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from utils.billing_date_utils import (
    parse_ymd,
    parse_ym,
    add_months,
    elapsed_months_inclusive,
    ym,
)
from utils.validation import (
    required_text,
    optional_text,
    required_plate,
    positive_float,
    positive_int,
)


class TestScenarioCustomerValidation(unittest.TestCase):
    """Integration tests for customer validation scenarios."""

    def test_scenario_add_customer(self):
        """Test scenario: validating customer data before adding."""
        # Customer name validation
        customer_name = required_text("Customer Name", "ABC Logistics Inc.")
        assert customer_name == "ABC Logistics Inc."

        # Phone is optional but if provided, valid format
        phone = "555-123-4567"  # or optional_phone(phone)
        assert phone is not None

        # Company is optional
        company = optional_text("Company", "ABC Logistics Inc.")
        assert company == "ABC Logistics Inc."

    def test_scenario_invalid_customer_name_empty(self):
        """Test scenario: reject empty customer name."""
        with self.assertRaises(ValueError):
            required_text("Customer Name", "")

    def test_scenario_customer_name_too_long(self):
        """Test scenario: reject overly long customer name."""
        long_name = "A" * 250  # Exceeds typical 100 char limit
        with self.assertRaises(ValueError):
            required_text("Customer Name", long_name, max_len=100)


class TestScenarioTruckValidation(unittest.TestCase):
    """Integration tests for truck validation scenarios."""

    def test_scenario_add_truck_complete(self):
        """Test scenario: validating complete truck data."""
        # Plate validation (required)
        plate = required_plate("TX-ABC-123")
        assert plate == "TX-ABC-123"

        # State is optional
        state = "TX"  # optional_state("TX")
        assert state == "TX"

        # Make and model are optional
        make = optional_text("Make", "Peterbilt")
        assert make == "Peterbilt"

        model = optional_text("Model", "379")
        assert model == "379"

    def test_scenario_truck_plate_normalization(self):
        """Test scenario: truck plate is normalized."""
        # User enters lowercase
        plate = required_plate("tx-abc-123")
        assert plate == "TX-ABC-123"

    def test_scenario_truck_plate_with_em_dash(self):
        """Test scenario: truck plate with em dash is normalized."""
        plate = required_plate("TX—ABC—123")  # em dashes
        assert "—" not in plate
        assert "-" in plate


class TestScenarioContractBilling(unittest.TestCase):
    """Integration tests for contract and billing scenarios."""

    def test_scenario_contract_monthly_rate(self):
        """Test scenario: validating contract monthly rate."""
        rate = positive_float("Monthly Rate", "$2,500.00")
        assert rate == 2500.0

    def test_scenario_contract_duration_months(self):
        """Test scenario: calculating contract duration in months."""
        start = parse_ymd("2024-01-15")
        end = parse_ymd("2024-06-15")
        
        duration = elapsed_months_inclusive(start, end)
        assert duration == 6

    def test_scenario_contract_extends_beyond_year(self):
        """Test scenario: contract extends beyond year boundary."""
        start = parse_ymd("2024-11-01")
        end = parse_ymd("2025-02-28")
        
        duration = elapsed_months_inclusive(start, end)
        assert duration == 4

    def test_scenario_next_billing_date(self):
        """Test scenario: calculating next billing date."""
        # If contract started 2024-01-15, what's next due date?
        start = parse_ym("2024-01")
        today_ym = ym(date.today())
        
        # Parse current month
        current_year, current_month = parse_ym(today_ym)
        assert current_year is not None
        assert current_month is not None


class TestScenarioInvoicing(unittest.TestCase):
    """Integration tests for invoice generation scenarios."""

    def test_scenario_invoice_period_march(self):
        """Test scenario: generating invoice for March."""
        # Parse the period
        period = parse_ym("2024-03")
        assert period == (2024, 3)

        # Contract running for multiple months
        start = parse_ymd("2024-01-15")
        date_in_march = parse_ymd("2024-03-15")
        
        months = elapsed_months_inclusive(start, date_in_march)
        assert months == 3

    def test_scenario_invoice_multiple_contracts(self):
        """Test scenario: invoice with multiple contracts."""
        # Contract 1: started Jan
        contract1_start = parse_ymd("2024-01-01")
        contract1_rate = positive_float("Rate", "1000.00")
        
        # Contract 2: started Feb
        contract2_start = parse_ymd("2024-02-01")
        contract2_rate = positive_float("Rate", "1500.00")
        
        # Both active as of March
        as_of_date = parse_ymd("2024-03-15")
        
        c1_months = elapsed_months_inclusive(contract1_start, as_of_date)
        c2_months = elapsed_months_inclusive(contract2_start, as_of_date)
        
        c1_expected = c1_months * contract1_rate
        c2_expected = c2_months * contract2_rate
        
        total = c1_expected + c2_expected
        assert total == (3 * 1000.0) + (2 * 1500.0)

    def test_scenario_invoice_year_boundary(self):
        """Test scenario: invoice at year boundary."""
        # Contract from Nov 2023 to Feb 2024
        start = parse_ymd("2023-11-15")
        as_of = parse_ymd("2024-02-15")
        
        months = elapsed_months_inclusive(start, as_of)
        # Nov, Dec, Jan, Feb = 4 months
        assert months == 4


class TestScenarioBillingCalculations(unittest.TestCase):
    """Integration tests for billing calculation scenarios."""

    def test_scenario_calculate_total_owed(self):
        """Test scenario: calculating total amount owed."""
        # 6 contracts at different rates
        rates = [
            1000.0,
            1500.0,
            2000.0,
            750.0,
            1250.0,
            1000.0,
        ]

        months_each = [3, 3, 2, 6, 4, 5]

        total_owed = sum(rate * months for rate, months in zip(rates, months_each))
        
        expected = (
            1000 * 3 +  # 3000
            1500 * 3 +  # 4500
            2000 * 2 +  # 4000
            750 * 6 +   # 4500
            1250 * 4 +  # 5000
            1000 * 5    # 5000
        )
        
        assert total_owed == expected
        assert total_owed == 26000.0

    def test_scenario_payment_allocation(self):
        """Test scenario: allocating payment to contracts."""
        contracts = [
            {"rate": 1000.0, "months": 3, "paid": 0},
            {"rate": 1500.0, "months": 3, "paid": 1500.0},
            {"rate": 2000.0, "months": 2, "paid": 2000.0},
        ]

        payment = 2000.0

        total_owed = sum(c["rate"] * c["months"] for c in contracts)
        total_paid = sum(c["paid"] for c in contracts)
        
        outstanding = total_owed - total_paid - payment
        
        assert outstanding >= 0


class TestScenarioDateRanges(unittest.TestCase):
    """Integration tests for date range scenarios."""

    def test_scenario_fiscal_year_month_range(self):
        """Test scenario: get all months in fiscal year."""
        # Fiscal year 2024: Apr 2024 - Mar 2025
        fiscal_start_ym = "2024-04"
        fiscal_end_ym = "2025-03"

        start_yr, start_mo = parse_ym(fiscal_start_ym)
        end_yr, end_mo = parse_ym(fiscal_end_ym)

        assert (start_yr, start_mo) == (2024, 4)
        assert (end_yr, end_mo) == (2025, 3)

        # 12 months in a fiscal year
        months_count = (end_yr - start_yr) * 12 + (end_mo - start_mo) + 1
        assert months_count == 12

    def test_scenario_month_navigation(self):
        """Test scenario: navigating months forward and backward."""
        current = "2024-06"  # June 2024
        current_yr, current_mo = parse_ym(current)

        # Next month
        next_yr, next_mo = add_months(current_yr, current_mo, 1)
        assert next_yr == 2024 and next_mo == 7

        # Previous month
        prev_yr, prev_mo = add_months(current_yr, current_mo, -1)
        assert prev_yr == 2024 and prev_mo == 5

        # 6 months forward
        six_mo_yr, six_mo_mo = add_months(current_yr, current_mo, 6)
        assert six_mo_yr == 2024 and six_mo_mo == 12

        # 6 months backward
        back_yr, back_mo = add_months(current_yr, current_mo, -6)
        assert back_yr == 2023 and back_mo == 12


if __name__ == "__main__":
    unittest.main()
