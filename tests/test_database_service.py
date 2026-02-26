#!/usr/bin/env python3
"""Unit tests for database_service.py module."""

import sys
from pathlib import Path
import tempfile
import os
from datetime import datetime

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from data.database_service import DatabaseService


class TestDatabaseServiceInit(unittest.TestCase):
    """Test database initialization and schema creation."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        """Clean up temporary database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_database_creates_file(self):
        """Test that database file is created."""
        db = DatabaseService(self.db_path)
        assert os.path.exists(self.db_path)
        db.conn.close()

    def test_database_schema_created(self):
        """Test that schema is initialized."""
        db = DatabaseService(self.db_path)
        
        # Check that tables exist
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        
        # Should have at least customers table
        assert "customers" in tables
        db.conn.close()

    def test_database_foreign_keys_enabled(self):
        """Test that foreign keys are enabled."""
        db = DatabaseService(self.db_path)
        
        cursor = db.conn.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()[0]
        
        assert result == 1, "Foreign keys should be enabled"
        db.conn.close()

    def test_database_allows_multiple_connections(self):
        """Test that multiple connections can be created."""
        db1 = DatabaseService(self.db_path)
        db2 = DatabaseService(self.db_path)
        
        assert db1.conn is not None
        assert db2.conn is not None
        
        db1.conn.close()
        db2.conn.close()


class TestDatabaseServiceSchema(unittest.TestCase):
    """Test database schema structure."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseService(self.db_path)

    def tearDown(self):
        """Clean up temporary database."""
        self.db.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_customers_table_exists(self):
        """Test that customers table exists."""
        cursor = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='customers'"
        )
        assert cursor.fetchone() is not None

    def test_trucks_table_exists(self):
        """Test that trucks table exists."""
        cursor = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='trucks'"
        )
        assert cursor.fetchone() is not None

    def test_contracts_table_exists(self):
        """Test that contracts table exists."""
        cursor = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='contracts'"
        )
        assert cursor.fetchone() is not None

    def test_invoices_table_exists(self):
        """Test that invoices table exists."""
        cursor = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'"
        )
        assert cursor.fetchone() is not None

    def test_payments_table_exists(self):
        """Test that payments table exists."""
        cursor = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='payments'"
        )
        assert cursor.fetchone() is not None

    def test_invoice_has_date_column(self):
        """Test that invoices table has invoice_date column."""
        cursor = self.db.conn.execute("PRAGMA table_info(invoices)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "invoice_date" in columns

    def test_contracts_has_date_columns(self):
        """Test that contracts table has date columns."""
        cursor = self.db.conn.execute("PRAGMA table_info(contracts)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "start_date" in columns
        assert "end_date" in columns


class TestDatabaseServiceBasicOperations(unittest.TestCase):
    """Test basic CRUD operations."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseService(self.db_path)

    def tearDown(self):
        """Clean up temporary database."""
        self.db.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_insert_customer(self):
        """Test inserting a customer."""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO customers (name, phone, company, notes, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Test Customer", "555-1234", "Test Co", "Notes", datetime.now().isoformat()),
        )
        self.db.conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT name FROM customers WHERE name = ?", ("Test Customer",))
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "Test Customer"

    def test_query_empty_customers(self):
        """Test querying when no customers exist."""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]
        assert count == 0

    def test_delete_customer(self):
        """Test deleting a customer."""
        cursor = self.db.conn.cursor()
        
        # Insert
        cursor.execute(
            "INSERT INTO customers (name, created_at) VALUES (?, ?)",
            ("Delete Me", datetime.now().isoformat()),
        )
        self.db.conn.commit()
        
        # Delete
        cursor.execute("DELETE FROM customers WHERE name = ?", ("Delete Me",))
        self.db.conn.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM customers WHERE name = ?", ("Delete Me",))
        count = cursor.fetchone()[0]
        assert count == 0

    def test_update_customer(self):
        """Test updating a customer."""
        cursor = self.db.conn.cursor()
        
        # Insert
        cursor.execute(
            "INSERT INTO customers (name, phone, created_at) VALUES (?, ?, ?)",
            ("Original", "555-1111", datetime.now().isoformat()),
        )
        self.db.conn.commit()
        
        # Update
        cursor.execute(
            "UPDATE customers SET phone = ? WHERE name = ?",
            ("555-2222", "Original"),
        )
        self.db.conn.commit()
        
        # Verify
        cursor.execute("SELECT phone FROM customers WHERE name = ?", ("Original",))
        result = cursor.fetchone()
        assert result[0] == "555-2222"


class TestDatabaseServiceConstraints(unittest.TestCase):
    """Test database constraints and integrity."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseService(self.db_path)

    def tearDown(self):
        """Clean up temporary database."""
        self.db.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_duplicate_customer_not_allowed(self):
        """Test that duplicate customer names are not allowed (unique constraint on LOWER(name))."""
        cursor = self.db.conn.cursor()
        
        cursor.execute(
            "INSERT INTO customers (name, created_at) VALUES (?, ?)",
            ("Duplicate", datetime.now().isoformat()),
        )
        self.db.conn.commit()
        
        # Try to insert duplicate (should fail due to unique index on LOWER(name))
        with self.assertRaises(Exception):
            cursor.execute(
                "INSERT INTO customers (name, created_at) VALUES (?, ?)",
                ("Duplicate", datetime.now().isoformat()),
            )
            self.db.conn.commit()

    def test_foreign_key_constraint(self):
        """Test that foreign key constraints are enforced."""
        cursor = self.db.conn.cursor()
        
        # Try to insert truck with non-existent customer
        with self.assertRaises(Exception):
            cursor.execute(
                "INSERT INTO trucks (customer_id, plate, state, created_at) VALUES (?, ?, ?, ?)",
                (99999, "TEST-001", "TX", datetime.now().isoformat()),
            )
            self.db.conn.commit()


class TestDatabaseServiceTableInfo(unittest.TestCase):
    """Test database table information retrieval."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseService(self.db_path)

    def tearDown(self):
        """Clean up temporary database."""
        self.db.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_get_all_tables(self):
        """Test retrieving all table names."""
        cursor = self.db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ["customers", "trucks", "contracts", "invoices", "payments"]
        for table in expected_tables:
            assert table in tables

    def test_table_column_count(self):
        """Test that tables have expected columns."""
        cursor = self.db.conn.execute("PRAGMA table_info(customers)")
        columns = cursor.fetchall()
        
        # Should have at least: id, name, phone, company, notes, created_at
        assert len(columns) >= 5

    def test_primary_keys_defined(self):
        """Test that primary keys are defined."""
        for table in ["customers", "trucks", "contracts"]:
            cursor = self.db.conn.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            # First column should be primary key (usually id)
            pk_column = [col for col in columns if col[5] == 1]
            assert len(pk_column) > 0, f"{table} should have a primary key"


if __name__ == "__main__":
    unittest.main()
