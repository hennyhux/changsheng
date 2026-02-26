#!/usr/bin/env python3
"""Test script to verify hierarchical invoice table structure."""

import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import DB_PATH
from data.database_service import DatabaseService

db = DatabaseService(DB_PATH)

# Get active contracts grouped by customer via DatabaseService
rows = db.get_active_contracts_with_customer_plate_for_invoices()

# Group contracts by customer
customer_contracts = {}
for r in rows:
    cust_id = r["customer_id"]
    cust_name = r["customer_name"]
    if cust_id not in customer_contracts:
        customer_contracts[cust_id] = {"name": cust_name, "contracts": []}
    customer_contracts[cust_id]["contracts"].append(r)

print("Hierarchical Invoice Table Structure:")
print("=" * 80)

# Display the hierarchical structure
for cust_id in sorted(customer_contracts.keys(), key=lambda x: customer_contracts[x]["name"]):
    cust_data = customer_contracts[cust_id]
    cust_name = cust_data["name"]
    contracts = cust_data["contracts"]
    
    print(f"\n[+] {cust_name}")
    print(f"    └─ {len(contracts)} contract{'s' if len(contracts) != 1 else ''}")
    
    for r in contracts:
        scope = r["plate"] if r["plate"] else "(customer-level)"
        rate = f"${float(r['monthly_rate']):.2f}"
        print(f"       └─ Contract {r['contract_id']:4d} | {scope:15s} | Rate: {rate}")

print("\n" + "=" * 80)
print(f"Total: {len(customer_contracts)} customers, {len(rows)} contracts")
