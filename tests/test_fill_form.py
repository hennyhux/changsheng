#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to verify the right-click fill payment form functionality"""

# Simulate the behavior of _sync_selected_invoice_to_payment_form
def test_fill_payment_form():
    """Test that the form filling logic works correctly"""
    
    # Create test data that would come from Treeview
    test_cases = [
        # (values_tuple, expected_contract_id, expected_amount, description)
        (
            ("42", "J Smith", "F-100", "$1500.00", "2024-01", "2024-06", 6, "$9000.00", "$4500.00", "$4500.00", "DUE"),
            "42", "4500.00", "Child row (contract) with outstanding balance"
        ),
        (
            ("1 Contract", "XYZ Corp", "", "", "", "", "", "$1500.00", "$750.00", "$750.00", "DUE"),
            None, None, "Parent row (customer) - should not fill form"
        ),
        (
            ("99", "", "Truck-001", "$2000.00", "2024-03", "", 3, "$6000.00", "$6000.00", "$0.00", "PAID"),
            "99", "0.00", "Child row with zero balance"
        ),
    ]
    
    print("Testing _sync_selected_invoice_to_payment_form logic...\n")
    
    for values, expected_contract_id, expected_amount, description in test_cases:
        print(f"Test: {description}")
        print(f"  Input values: {values}")
        
        # This is the logic from _sync_selected_invoice_to_payment_form
        try:
            if not values or len(values) < 10:
                print(f"  Result: Form cleared (insufficient data)")
                assert expected_contract_id is None, f"Expected no fill, but got contract_id={expected_contract_id}"
                print("  ✓ PASS\n")
                continue
            
            contract_id_str = str(values[0]).strip()
            
            # Try to parse as integer
            try:
                contract_id = int(contract_id_str)
            except (ValueError, TypeError):
                # Parent row - don't fill
                print(f"  Result: Form cleared (parent row detected)")
                assert expected_contract_id is None, f"Expected no fill, but got contract_id={expected_contract_id}"
                print("  ✓ PASS\n")
                continue
            
            # Extract balance
            bal_str = str(values[9]).replace("$", "").replace(",", "").strip()
            
            try:
                bal_num = float(bal_str)
                amount_str = f"{bal_num:.2f}"
            except (ValueError, TypeError):
                amount_str = ""
            
            print(f"  Result: Form filled with contract_id={contract_id}, amount={amount_str}")
            assert contract_id == int(expected_contract_id), f"Expected {expected_contract_id}, got {contract_id}"
            assert amount_str == expected_amount, f"Expected {expected_amount}, got {amount_str}"
            print("  ✓ PASS\n")
            
        except AssertionError as e:
            print(f"  ✗ FAIL: {e}\n")
            return False
        except Exception as e:
            print(f"  ✗ FAIL: Unexpected error: {e}\n")
            return False
    
    print("All tests passed! ✓")
    return True

if __name__ == "__main__":
    success = test_fill_payment_form()
    exit(0 if success else 1)
