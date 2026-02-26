from __future__ import annotations

import sqlite3
import os
import shutil
import uuid
from typing import Any

from core.app_logging import trace, get_exception_logger, get_trace_logger

_exc_logger = get_exception_logger()
_trace_logger = get_trace_logger()


class DatabaseService:
    SCHEMA_VERSION = 3
    ALLOWED_PAYMENT_METHODS = ("cash", "card", "zelle", "venmo", "other")
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = self._connect()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        if not self._has_table("customers"):
            self._create_schema_v3()
            self._set_user_version(self.SCHEMA_VERSION)
        else:
            current_version = self._get_user_version()
            if current_version < self.SCHEMA_VERSION:
                self._migrate_to_v3()
            else:
                self._create_schema_v3()

        invoice_columns = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(invoices)").fetchall()
        }
        if "invoice_date" not in invoice_columns:
            self.conn.execute("ALTER TABLE invoices ADD COLUMN invoice_date TEXT")

        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)")

        self.conn.execute(
            """
            UPDATE invoices
            SET invoice_date = invoice_ym || '-01'
            WHERE invoice_date IS NULL OR TRIM(invoice_date) = ''
            """
        )

        contract_columns = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(contracts)").fetchall()
        }
        if "start_date" not in contract_columns:
            self.conn.execute("ALTER TABLE contracts ADD COLUMN start_date TEXT")
        if "end_date" not in contract_columns:
            self.conn.execute("ALTER TABLE contracts ADD COLUMN end_date TEXT")

        self.conn.execute(
            """
            UPDATE contracts
            SET start_date = CASE
                WHEN LENGTH(TRIM(start_ym)) >= 10 THEN SUBSTR(TRIM(start_ym), 1, 10)
                ELSE TRIM(start_ym) || '-01'
            END
            WHERE start_date IS NULL OR TRIM(start_date) = ''
            """
        )
        self.conn.execute(
            """
            UPDATE contracts
            SET end_date = CASE
                WHEN end_ym IS NULL OR TRIM(end_ym) = '' THEN NULL
                WHEN LENGTH(TRIM(end_ym)) >= 10 THEN SUBSTR(TRIM(end_ym), 1, 10)
                ELSE TRIM(end_ym) || '-01'
            END
            WHERE end_date IS NULL OR TRIM(end_date) = ''
            """
        )

        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_contracts_start_date ON contracts(start_date)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_contracts_end_date ON contracts(end_date)")

        self.conn.commit()

    def _has_table(self, name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone()
        return row is not None

    def _get_user_version(self) -> int:
        row = self.conn.execute("PRAGMA user_version").fetchone()
        return int(row[0]) if row else 0

    def _set_user_version(self, version: int) -> None:
        self.conn.execute(f"PRAGMA user_version = {int(version)}")

    def _create_schema_v3(self) -> None:
        methods = ", ".join([f"'{m}'" for m in self.ALLOWED_PAYMENT_METHODS])
        self.conn.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL CHECK (LENGTH(TRIM(name)) > 0),
                phone TEXT,
                company TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_name_unique ON customers(LOWER(name));

            CREATE TABLE IF NOT EXISTS trucks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                plate TEXT NOT NULL UNIQUE CHECK (LENGTH(TRIM(plate)) > 0),
                state TEXT,
                make TEXT,
                model TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                truck_id INTEGER,
                monthly_rate REAL NOT NULL CHECK (monthly_rate > 0),
                start_ym TEXT NOT NULL CHECK (LENGTH(TRIM(start_ym)) > 0),
                end_ym TEXT,
                start_date TEXT,
                end_date TEXT,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                FOREIGN KEY (truck_id) REFERENCES trucks(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                invoice_uuid TEXT NOT NULL UNIQUE CHECK (LENGTH(TRIM(invoice_uuid)) > 0),
                invoice_ym TEXT NOT NULL CHECK (LENGTH(TRIM(invoice_ym)) > 0),
                invoice_date TEXT,
                amount REAL NOT NULL CHECK (amount >= 0),
                created_at TEXT NOT NULL,
                UNIQUE(contract_id, invoice_ym),
                FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                paid_at TEXT NOT NULL CHECK (LENGTH(TRIM(paid_at)) > 0),
                amount REAL NOT NULL CHECK (amount > 0),
                method TEXT NOT NULL CHECK (method IN ({methods})),
                reference TEXT,
                notes TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_trucks_plate ON trucks(plate);
            CREATE INDEX IF NOT EXISTS idx_invoices_ym ON invoices(invoice_ym);
            CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);

            CREATE TRIGGER IF NOT EXISTS trg_contract_overlap_insert
            BEFORE INSERT ON contracts
            WHEN NEW.is_active = 1 AND NEW.truck_id IS NOT NULL
            BEGIN
                SELECT
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM contracts c
                            WHERE c.truck_id = NEW.truck_id
                              AND c.is_active = 1
                              AND DATE(COALESCE(NULLIF(c.start_date, ''), c.start_ym || '-01')) <= DATE(COALESCE(NULLIF(NEW.end_date, ''), CASE WHEN NEW.end_ym IS NOT NULL AND TRIM(NEW.end_ym) <> '' THEN NEW.end_ym || '-01' ELSE '9999-12-31' END))
                              AND DATE(COALESCE(NULLIF(NEW.start_date, ''), NEW.start_ym || '-01')) <= DATE(COALESCE(NULLIF(c.end_date, ''), CASE WHEN c.end_ym IS NOT NULL AND TRIM(c.end_ym) <> '' THEN c.end_ym || '-01' ELSE '9999-12-31' END))
                        )
                        THEN RAISE(ABORT, 'Overlapping active contract for same truck')
                    END;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_contract_overlap_update
            BEFORE UPDATE ON contracts
            WHEN NEW.is_active = 1 AND NEW.truck_id IS NOT NULL
            BEGIN
                SELECT
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM contracts c
                            WHERE c.truck_id = NEW.truck_id
                              AND c.is_active = 1
                              AND c.id <> NEW.id
                              AND DATE(COALESCE(NULLIF(c.start_date, ''), c.start_ym || '-01')) <= DATE(COALESCE(NULLIF(NEW.end_date, ''), CASE WHEN NEW.end_ym IS NOT NULL AND TRIM(NEW.end_ym) <> '' THEN NEW.end_ym || '-01' ELSE '9999-12-31' END))
                              AND DATE(COALESCE(NULLIF(NEW.start_date, ''), NEW.start_ym || '-01')) <= DATE(COALESCE(NULLIF(c.end_date, ''), CASE WHEN c.end_ym IS NOT NULL AND TRIM(c.end_ym) <> '' THEN c.end_ym || '-01' ELSE '9999-12-31' END))
                        )
                        THEN RAISE(ABORT, 'Overlapping active contract for same truck')
                    END;
            END;
            """
        )

    def _migrate_to_v3(self) -> None:
        issues = self._collect_integrity_issues()
        if issues:
            details = "\n".join(issues[:20])
            extra = "\n..." if len(issues) > 20 else ""
            raise ValueError(f"Integrity check failed before migration:\n{details}{extra}")

        self.conn.execute("BEGIN")
        self.conn.execute("ALTER TABLE customers RENAME TO customers_old")
        self.conn.execute("ALTER TABLE trucks RENAME TO trucks_old")
        self.conn.execute("ALTER TABLE contracts RENAME TO contracts_old")
        self.conn.execute("ALTER TABLE invoices RENAME TO invoices_old")
        self.conn.execute("ALTER TABLE payments RENAME TO payments_old")

        self._create_schema_v3()

        self.conn.execute(
            """
            INSERT INTO customers(id, name, phone, company, notes, created_at)
            SELECT id, name, phone, company, notes, created_at
            FROM customers_old
            """
        )
        self.conn.execute(
            """
            INSERT INTO trucks(id, customer_id, plate, state, make, model, notes, created_at)
            SELECT id, customer_id, plate, state, make, model, notes, created_at
            FROM trucks_old
            """
        )
        self.conn.execute(
            """
            INSERT INTO contracts(
                id, customer_id, truck_id, monthly_rate, start_ym, end_ym,
                start_date, end_date, is_active, notes, created_at
            )
            SELECT
                id, customer_id, truck_id, monthly_rate, start_ym, end_ym,
                start_date, end_date, is_active, notes, created_at
            FROM contracts_old
            """
        )
        old_invoices = self.fetchall(
            "SELECT id, contract_id, invoice_ym, invoice_date, amount, created_at FROM invoices_old"
        )
        for row in old_invoices:
            invoice_uuid = str(uuid.uuid4())
            self.conn.execute(
                """
                INSERT INTO invoices(id, contract_id, invoice_uuid, invoice_ym, invoice_date, amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["contract_id"],
                    invoice_uuid,
                    row["invoice_ym"],
                    row["invoice_date"],
                    row["amount"],
                    row["created_at"],
                ),
            )
        self.conn.execute(
            """
            INSERT INTO payments(id, invoice_id, paid_at, amount, method, reference, notes)
            SELECT id, invoice_id, paid_at, amount, method, reference, notes
            FROM payments_old
            """
        )

        self.conn.execute("DROP TABLE payments_old")
        self.conn.execute("DROP TABLE invoices_old")
        self.conn.execute("DROP TABLE contracts_old")
        self.conn.execute("DROP TABLE trucks_old")
        self.conn.execute("DROP TABLE customers_old")

        self._set_user_version(self.SCHEMA_VERSION)
        self.conn.commit()

    def _collect_integrity_issues(self) -> list[str]:
        issues: list[str] = []

        dup_rows = self.fetchall(
            """
            SELECT LOWER(name) AS n, COUNT(*) AS c
            FROM customers
            GROUP BY LOWER(name)
            HAVING COUNT(*) > 1
            """
        )
        for r in dup_rows:
            issues.append(f"Duplicate customer name: '{r['n']}' (count={r['c']})")

        bad_rates = self.fetchall(
            "SELECT id, monthly_rate FROM contracts WHERE monthly_rate IS NULL OR monthly_rate <= 0"
        )
        for r in bad_rates:
            issues.append(f"Contract {r['id']} has invalid monthly_rate {r['monthly_rate']}")

        bad_active = self.fetchall(
            "SELECT id, is_active FROM contracts WHERE is_active NOT IN (0, 1) OR is_active IS NULL"
        )
        for r in bad_active:
            issues.append(f"Contract {r['id']} has invalid is_active {r['is_active']}")

        bad_invoices = self.fetchall(
            "SELECT id, amount FROM invoices WHERE amount IS NULL OR amount < 0"
        )
        for r in bad_invoices:
            issues.append(f"Invoice {r['id']} has invalid amount {r['amount']}")

        bad_payments = self.fetchall(
            "SELECT id, amount FROM payments WHERE amount IS NULL OR amount <= 0"
        )
        for r in bad_payments:
            issues.append(f"Payment {r['id']} has invalid amount {r['amount']}")

        method_placeholders = ", ".join(["?"] * len(self.ALLOWED_PAYMENT_METHODS))
        bad_methods = self.fetchall(
            f"SELECT id, method FROM payments WHERE method NOT IN ({method_placeholders})",
            self.ALLOWED_PAYMENT_METHODS,
        )
        for r in bad_methods:
            issues.append(f"Payment {r['id']} has invalid method '{r['method']}'")

        overlaps = self.fetchall(
            """
            SELECT c1.id AS id1, c2.id AS id2, c1.truck_id AS truck_id
            FROM contracts c1
            JOIN contracts c2 ON c1.truck_id = c2.truck_id AND c1.id < c2.id
            WHERE c1.truck_id IS NOT NULL
              AND c1.is_active = 1 AND c2.is_active = 1
              AND DATE(COALESCE(NULLIF(c1.start_date, ''), c1.start_ym || '-01')) <= DATE(COALESCE(NULLIF(c2.end_date, ''), CASE WHEN c2.end_ym IS NOT NULL AND TRIM(c2.end_ym) <> '' THEN c2.end_ym || '-01' ELSE '9999-12-31' END))
              AND DATE(COALESCE(NULLIF(c2.start_date, ''), c2.start_ym || '-01')) <= DATE(COALESCE(NULLIF(c1.end_date, ''), CASE WHEN c1.end_ym IS NOT NULL AND TRIM(c1.end_ym) <> '' THEN c1.end_ym || '-01' ELSE '9999-12-31' END))
            LIMIT 20
            """
        )
        for r in overlaps:
            issues.append(f"Overlapping active contracts for truck {r['truck_id']}: {r['id1']} and {r['id2']}")

        return issues

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        return self.conn.execute(query, params)

    def fetchone(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        return self.conn.execute(query, params).fetchone()

    def fetchall(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return self.conn.execute(query, params).fetchall()

    def count(self, table: str, where_clause: str, params: tuple[Any, ...]) -> int:
        query = f"SELECT COUNT(*) AS n FROM {table} WHERE {where_clause}"
        row = self.conn.execute(query, params).fetchone()
        return int(row["n"]) if row else 0

    @trace
    def count_contracts_for_customer(self, customer_id: int) -> int:
        row = self.fetchone("SELECT COUNT(*) AS n FROM contracts WHERE customer_id=?", (customer_id,))
        return int(row["n"]) if row else 0

    @trace
    def count_trucks_for_customer(self, customer_id: int) -> int:
        row = self.fetchone("SELECT COUNT(*) AS n FROM trucks WHERE customer_id=?", (customer_id,))
        return int(row["n"]) if row else 0

    @trace
    def count_contracts_for_truck(self, truck_id: int) -> int:
        row = self.fetchone("SELECT COUNT(*) AS n FROM contracts WHERE truck_id=?", (truck_id,))
        return int(row["n"]) if row else 0

    @trace
    def count_invoices_for_contract(self, contract_id: int) -> int:
        row = self.fetchone("SELECT COUNT(*) AS n FROM invoices WHERE contract_id=?", (contract_id,))
        return int(row["n"]) if row else 0

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def _quote_ident(self, name: str) -> str:
        return '"' + str(name).replace('"', '""') + '"'

    def _table_count(self, conn: sqlite3.Connection, table_name: str) -> int:
        query = f"SELECT COUNT(*) AS n FROM {self._quote_ident(table_name)}"
        row = conn.execute(query).fetchone()
        return int(row[0]) if row else 0

    def _user_table_names(self, conn: sqlite3.Connection) -> list[str]:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name ASC
            """
        ).fetchall()
        return [str(r[0]) for r in rows]

    def _validate_backup_copy(self, backup_conn: sqlite3.Connection) -> None:
        source_tables = self._user_table_names(self.conn)
        backup_tables = self._user_table_names(backup_conn)
        if source_tables != backup_tables:
            raise RuntimeError(
                "Backup verification failed: table list mismatch "
                f"(source={source_tables}, backup={backup_tables})"
            )

        core_tables = ["customers", "trucks", "contracts", "invoices", "payments"]
        missing_core = [t for t in core_tables if t not in backup_tables]
        if missing_core:
            raise RuntimeError(
                "Backup verification failed: missing core tables "
                f"{missing_core}"
            )

        for table_name in core_tables:
            src_count = self._table_count(self.conn, table_name)
            bak_count = self._table_count(backup_conn, table_name)
            if src_count != bak_count:
                raise RuntimeError(
                    "Backup verification failed: row count mismatch for "
                    f"'{table_name}' (source={src_count}, backup={bak_count})"
                )

    def _validate_connection_integrity(self, conn: sqlite3.Connection) -> None:
        integrity_row = conn.execute("PRAGMA integrity_check").fetchone()
        integrity_result = str(integrity_row[0]).lower() if integrity_row else ""
        if integrity_result != "ok":
            raise RuntimeError(f"Integrity check failed: {integrity_result}")

        fk_rows = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_rows:
            raise RuntimeError(f"Foreign key check failed with {len(fk_rows)} violation(s)")

        core_tables = ["customers", "trucks", "contracts", "invoices", "payments"]
        table_names = self._user_table_names(conn)
        missing_core = [t for t in core_tables if t not in table_names]
        if missing_core:
            raise RuntimeError(f"Missing core tables: {missing_core}")

    @trace
    def validate_backup_file(self, backup_file_path: str) -> None:
        if not backup_file_path or not os.path.exists(backup_file_path):
            raise RuntimeError("Backup file not found")

        backup_conn = sqlite3.connect(backup_file_path)
        try:
            backup_conn.row_factory = sqlite3.Row
            backup_conn.execute("PRAGMA foreign_keys = ON;")
            self._validate_connection_integrity(backup_conn)
        finally:
            backup_conn.close()

    @trace
    def restore_from_backup(self, backup_file_path: str, safety_backup_path: str) -> None:
        if not backup_file_path:
            raise RuntimeError("Backup file path is required")
        if not safety_backup_path:
            raise RuntimeError("Safety backup path is required")

        self.validate_backup_file(backup_file_path)
        self.backup_to(safety_backup_path)

        db_temp_restore = self.db_path + ".restore_tmp"
        if os.path.exists(db_temp_restore):
            os.remove(db_temp_restore)

        self.close()
        try:
            shutil.copy2(backup_file_path, db_temp_restore)
            validate_conn = sqlite3.connect(db_temp_restore)
            try:
                validate_conn.row_factory = sqlite3.Row
                validate_conn.execute("PRAGMA foreign_keys = ON;")
                self._validate_connection_integrity(validate_conn)
            finally:
                validate_conn.close()

            os.replace(db_temp_restore, self.db_path)
            self.conn = self._connect()
            self._init_db()
            self._validate_connection_integrity(self.conn)
        except Exception:
            if os.path.exists(db_temp_restore):
                try:
                    os.remove(db_temp_restore)
                except Exception:
                    pass
            try:
                self.conn = self._connect()
            except Exception:
                pass
            raise

    @trace
    def backup_to(self, file_path: str) -> None:
        self.conn.commit()
        try:
            self.conn.execute("PRAGMA wal_checkpoint(FULL)")
        except Exception:
            pass
        backup_conn = sqlite3.connect(file_path)
        try:
            self.conn.backup(backup_conn)
            backup_conn.commit()
            self._validate_backup_copy(backup_conn)
        finally:
            backup_conn.close()

    @trace
    def get_customers_with_truck_count(self, q: str | None = None, limit: int = 200) -> list[sqlite3.Row]:
        if q:
            phone_q = "".join(ch for ch in str(q) if ch.isdigit())
            phone_like = f"%{phone_q}%" if phone_q else "%"
            return self.fetchall(
                """
                SELECT c.id, c.name, c.phone, c.company, COALESCE(c.notes, '') AS notes, COUNT(t.id) AS truck_count
                FROM customers c
                LEFT JOIN trucks t ON t.customer_id = c.id
                WHERE c.name LIKE ?
                   OR c.phone LIKE ?
                   OR c.company LIKE ?
                   OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(c.phone, ''), '-', ''), ' ', ''), '(', ''), ')', ''), '+', ''), '.', '') LIKE ?
                GROUP BY c.id
                ORDER BY c.id DESC
                LIMIT ?
                """,
                (f"%{q}%", f"%{q}%", f"%{q}%", phone_like, limit),
            )

        return self.fetchall(
            """
            SELECT c.id, c.name, c.phone, c.company, COALESCE(c.notes, '') AS notes, COUNT(t.id) AS truck_count
            FROM customers c
            LEFT JOIN trucks t ON t.customer_id = c.id
            GROUP BY c.id
            ORDER BY c.id DESC
            LIMIT ?
            """,
            (limit,),
        )

    def get_trucks_with_customer(
        self,
        q: str | None = None,
        limit: int = 300,
        customer_id: int | None = None,
        search_mode: str = "all",
    ) -> list[sqlite3.Row]:
        base_query = (
            """
            SELECT t.id, t.plate, t.state, t.make, t.model, c.name AS customer_name
            FROM trucks t
            LEFT JOIN customers c ON c.id=t.customer_id
            """
        )
        where_clauses: list[str] = []
        params: list[Any] = []

        if customer_id is not None:
            where_clauses.append("t.customer_id = ?")
            params.append(customer_id)

        if q:
            if search_mode == "customer_name":
                where_clauses.append("c.name LIKE ?")
                params.append(f"%{q}%")
            else:
                where_clauses.append("(t.plate LIKE ? OR c.name LIKE ?)")
                params.append(f"%{q}%")
                params.append(f"%{q}%")

        query = base_query
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY t.id DESC LIMIT ?"
        params.append(limit)

        return self.fetchall(query, tuple(params))

    @trace
    def get_contracts_for_grid(self, limit: int = 500) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT
                ct.id AS contract_id,
                ct.customer_id AS customer_id,
                ct.monthly_rate,
                COALESCE(NULLIF(ct.start_date, ''), ct.start_ym || '-01') AS start_date,
                CASE
                    WHEN ct.end_date IS NOT NULL AND TRIM(ct.end_date) <> '' THEN ct.end_date
                    WHEN ct.end_ym IS NOT NULL AND TRIM(ct.end_ym) <> '' THEN ct.end_ym || '-01'
                    ELSE NULL
                END AS end_date,
                ct.is_active,
                c.name AS customer_name,
                t.plate AS plate
            FROM contracts ct
            JOIN customers c ON c.id=ct.customer_id
            LEFT JOIN trucks t ON t.id=ct.truck_id
            ORDER BY ct.id DESC
            LIMIT ?
            """,
            (limit,),
        )

    @trace
    def get_customer_dropdown_rows(self) -> list[sqlite3.Row]:
        return self.fetchall("SELECT id, name, phone, company FROM customers ORDER BY name ASC")

    @trace
    def get_truck_dropdown_rows(self) -> list[sqlite3.Row]:
        return self.fetchall("SELECT id, plate, state, customer_id FROM trucks ORDER BY plate ASC")

    @trace
    def get_active_contracts_for_dashboard(self) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT
                ct.id AS contract_id,
                ct.monthly_rate,
                COALESCE(NULLIF(ct.start_date, ''), ct.start_ym || '-01') AS start_date,
                CASE
                    WHEN ct.end_date IS NOT NULL AND TRIM(ct.end_date) <> '' THEN ct.end_date
                    WHEN ct.end_ym IS NOT NULL AND TRIM(ct.end_ym) <> '' THEN ct.end_ym || '-01'
                    ELSE NULL
                END AS end_date
            FROM contracts ct
            WHERE ct.is_active=1
            """
        )

    def get_paid_total_for_contract_as_of(self, contract_id: int, as_of_iso: str) -> float:
        row = self.fetchone(
            """
            SELECT COALESCE(SUM(p.amount), 0) AS paid_total
            FROM payments p
            JOIN invoices i ON i.id=p.invoice_id
            WHERE i.contract_id=? AND DATE(p.paid_at) <= ?
            """,
            (contract_id, as_of_iso),
        )
        return float(row["paid_total"]) if row else 0.0

    @trace
    def get_total_payments_for_invoice(self, invoice_id: int) -> float:
        row = self.fetchone(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM payments WHERE invoice_id=?",
            (invoice_id,),
        )
        return float(row["s"]) if row else 0.0

    @trace
    def get_active_contracts_with_customer_plate_for_invoices(self) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT
                ct.id AS contract_id,
                ct.customer_id,
                ct.monthly_rate,
                COALESCE(NULLIF(ct.start_date, ''), ct.start_ym || '-01') AS start_date,
                CASE
                    WHEN ct.end_date IS NOT NULL AND TRIM(ct.end_date) <> '' THEN ct.end_date
                    WHEN ct.end_ym IS NOT NULL AND TRIM(ct.end_ym) <> '' THEN ct.end_ym || '-01'
                    ELSE NULL
                END AS end_date,
                c.name AS customer_name,
                t.plate AS plate
            FROM contracts ct
            JOIN customers c ON c.id=ct.customer_id
            LEFT JOIN trucks t ON t.id=ct.truck_id
            WHERE ct.is_active=1
            ORDER BY customer_name ASC, plate ASC
            """
        )

    @trace
    def get_contracts_with_customer_plate_for_overdue(self) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT
                ct.id AS contract_id,
                ct.customer_id,
                ct.monthly_rate,
                COALESCE(NULLIF(ct.start_date, ''), ct.start_ym || '-01') AS start_date,
                CASE
                    WHEN ct.end_date IS NOT NULL AND TRIM(ct.end_date) <> '' THEN ct.end_date
                    WHEN ct.end_ym IS NOT NULL AND TRIM(ct.end_ym) <> '' THEN ct.end_ym || '-01'
                    ELSE NULL
                END AS end_date,
                ct.is_active,
                c.name AS customer_name,
                t.plate AS plate
            FROM contracts ct
            JOIN customers c ON c.id=ct.customer_id
            LEFT JOIN trucks t ON t.id=ct.truck_id
            ORDER BY customer_name ASC, plate ASC, ct.id ASC
            """
        )

    @trace
    def get_customer_name_by_contract(self, contract_id: int) -> str | None:
        row = self.fetchone(
            """
            SELECT c.name AS customer_name
            FROM contracts ct
            JOIN customers c ON c.id=ct.customer_id
            WHERE ct.id=?
            """,
            (contract_id,),
        )
        return row["customer_name"] if row else None

    @trace
    def get_customer_id_by_contract(self, contract_id: int) -> int | None:
        row = self.fetchone(
            "SELECT customer_id FROM contracts WHERE id=?",
            (contract_id,),
        )
        return int(row["customer_id"]) if row else None

    @trace
    def get_first_customer_id_by_name(self, customer_name: str) -> int | None:
        row = self.fetchone(
            "SELECT id FROM customers WHERE name=? ORDER BY id ASC LIMIT 1",
            (customer_name,),
        )
        return int(row["id"]) if row else None

    @trace
    def get_customer_basic_by_id(self, customer_id: int) -> sqlite3.Row | None:
        return self.fetchone(
            "SELECT id, name, phone, company FROM customers WHERE id = ?",
            (customer_id,),
        )

    @trace
    def get_active_contracts_for_customer_invoice(self, customer_id: int) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT ct.id, ct.monthly_rate, ct.start_date, ct.end_date, t.plate
            FROM contracts ct
            LEFT JOIN trucks t ON t.id = ct.truck_id
            WHERE ct.customer_id = ? AND ct.is_active = 1
            ORDER BY ct.id ASC
            """,
            (customer_id,),
        )

    @trace
    def get_payment_count_by_contract(self, contract_id: int) -> int:
        row = self.fetchone(
            """
            SELECT COUNT(*) AS n
            FROM payments p
            JOIN invoices i ON i.id = p.invoice_id
            WHERE i.contract_id = ?
            """,
            (contract_id,),
        )
        return int(row["n"]) if row else 0

    @trace
    def delete_payments_by_contract(self, contract_id: int) -> None:
        self.execute(
            """
            DELETE FROM payments
            WHERE invoice_id IN (
                SELECT id FROM invoices WHERE contract_id = ?
            )
            """,
            (contract_id,),
        )

    @trace
    def contract_exists(self, contract_id: int) -> bool:
        row = self.fetchone("SELECT id FROM contracts WHERE id=?", (contract_id,))
        return row is not None

    def get_or_create_anchor_invoice(
        self,
        contract_id: int,
        invoice_ym: str,
        invoice_date_iso: str,
        created_at: str,
    ) -> int:
        row = self.fetchone(
            """
            SELECT id
            FROM invoices
            WHERE contract_id=?
            ORDER BY COALESCE(invoice_date, created_at) DESC, id DESC
            LIMIT 1
            """,
            (contract_id,),
        )
        if row:
            return int(row["id"])

        invoice_uuid = str(uuid.uuid4())
        cur = self.execute(
            """
            INSERT INTO invoices(contract_id, invoice_uuid, invoice_ym, invoice_date, amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (contract_id, invoice_uuid, invoice_ym, invoice_date_iso, 0.0, created_at),
        )
        return int(cur.lastrowid)

    def create_payment(
        self,
        invoice_id: int,
        paid_at: str,
        amount: float,
        method: str,
        reference: str,
        notes: str,
    ) -> None:
        self.execute(
            "INSERT INTO payments(invoice_id, paid_at, amount, method, reference, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (invoice_id, paid_at, amount, method, reference, notes),
        )

    def get_contract_snapshot(self, contract_id: int) -> sqlite3.Row | None:
        return self.fetchone(
            """
            SELECT
                ct.monthly_rate,
                COALESCE(NULLIF(ct.start_date, ''), ct.start_ym || '-01') AS start_date,
                CASE
                    WHEN ct.end_date IS NOT NULL AND TRIM(ct.end_date) <> '' THEN ct.end_date
                    WHEN ct.end_ym IS NOT NULL AND TRIM(ct.end_ym) <> '' THEN ct.end_ym || '-01'
                    ELSE NULL
                END AS end_date
            FROM contracts ct
            WHERE ct.id=?
            """,
            (contract_id,),
        )

    @trace
    def get_overdue_invoice_rows(self, as_of_iso: str) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT
                i.id AS invoice_id,
                i.invoice_ym,
                i.invoice_date,
                i.amount,
                c.name AS customer_name,
                t.plate AS plate
            FROM invoices i
            JOIN contracts ct ON ct.id=i.contract_id
            JOIN customers c ON c.id=ct.customer_id
            LEFT JOIN trucks t ON t.id=ct.truck_id
            WHERE i.invoice_date <= ?
            ORDER BY i.invoice_date ASC, customer_name ASC
            """,
            (as_of_iso,),
        )

    @trace
    def get_contracts_for_statement(self) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT
                ct.id AS contract_id,
                ct.monthly_rate,
                COALESCE(NULLIF(ct.start_date, ''), ct.start_ym || '-01') AS start_date,
                CASE
                    WHEN ct.end_date IS NOT NULL AND TRIM(ct.end_date) <> '' THEN ct.end_date
                    WHEN ct.end_ym IS NOT NULL AND TRIM(ct.end_ym) <> '' THEN ct.end_ym || '-01'
                    ELSE NULL
                END AS end_date,
                ct.is_active
            FROM contracts ct
            """
        )

    @trace
    def get_paid_totals_by_contract(self) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT i.contract_id, COALESCE(SUM(p.amount), 0) AS paid_total
            FROM payments p
            JOIN invoices i ON i.id = p.invoice_id
            GROUP BY i.contract_id
            """
        )

    @trace
    def get_customer_truck_export_rows(self, q: str | None = None) -> list[sqlite3.Row]:
        if q:
            return self.fetchall(
                """
                SELECT
                    c.id AS customer_id,
                    c.name AS customer_name,
                    c.phone,
                    c.company,
                    t.id AS truck_id,
                    t.plate,
                    t.state,
                    t.make,
                    t.model
                FROM customers c
                LEFT JOIN trucks t ON t.customer_id = c.id
                WHERE c.name LIKE ? OR c.phone LIKE ? OR c.company LIKE ?
                ORDER BY c.name ASC, t.plate ASC
                """,
                (f"%{q}%", f"%{q}%", f"%{q}%"),
            )

        return self.fetchall(
            """
            SELECT
                c.id AS customer_id,
                c.name AS customer_name,
                c.phone,
                c.company,
                t.id AS truck_id,
                t.plate,
                t.state,
                t.make,
                t.model
            FROM customers c
            LEFT JOIN trucks t ON t.customer_id = c.id
            ORDER BY c.name ASC, t.plate ASC
            """
        )

    @trace
    def get_all_customer_names(self) -> list[str]:
        rows = self.fetchall("SELECT name FROM customers")
        return [str(r["name"]) for r in rows if r["name"] is not None]

    @trace
    def get_all_truck_plates(self) -> list[str]:
        rows = self.fetchall("SELECT plate FROM trucks")
        return [str(r["plate"]) for r in rows if r["plate"] is not None]

    @trace
    def get_all_customer_id_name_rows(self) -> list[sqlite3.Row]:
        return self.fetchall("SELECT id, name FROM customers")

    @trace
    def create_customer(self, name: str, phone: str | None, company: str | None, notes: str | None, created_at: str) -> int:
        cur = self.execute(
            "INSERT INTO customers(name, phone, company, notes, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, phone, company, notes, created_at),
        )
        return int(cur.lastrowid)

    @trace
    def update_customer(self, customer_id: int, name: str, phone: str | None, company: str | None, notes: str | None) -> None:
        self.execute(
            "UPDATE customers SET name=?, phone=?, company=?, notes=? WHERE id=?",
            (name, phone, company, notes, customer_id),
        )

    @trace
    def delete_customer(self, customer_id: int) -> None:
        self.execute("DELETE FROM customers WHERE id=?", (customer_id,))

    def create_truck(
        self,
        customer_id: int | None,
        plate: str,
        state: str | None,
        make: str | None,
        model: str | None,
        notes: str | None,
        created_at: str,
    ) -> int:
        cur = self.execute(
            "INSERT INTO trucks(customer_id, plate, state, make, model, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (customer_id, plate, state, make, model, notes, created_at),
        )
        return int(cur.lastrowid)

    @trace
    def delete_truck(self, truck_id: int) -> None:
        self.execute("DELETE FROM contracts WHERE truck_id=?", (truck_id,))
        self.execute("DELETE FROM trucks WHERE id=?", (truck_id,))

    def create_contract(
        self,
        customer_id: int,
        truck_id: int | None,
        monthly_rate: float,
        start_ym: str,
        end_ym: str | None,
        start_date: str,
        end_date: str | None,
        is_active: int,
        notes: str | None,
        created_at: str,
    ) -> int:
        cur = self.execute(
            """
            INSERT INTO contracts(customer_id, truck_id, monthly_rate, start_ym, end_ym, start_date, end_date, is_active, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (customer_id, truck_id, monthly_rate, start_ym, end_ym, start_date, end_date, is_active, notes, created_at),
        )
        return int(cur.lastrowid)

    @trace
    def get_contract_active_row(self, contract_id: int) -> sqlite3.Row | None:
        return self.fetchone("SELECT id, is_active FROM contracts WHERE id=?", (contract_id,))

    @trace
    def set_contract_active(self, contract_id: int, is_active: int) -> None:
        self.execute("UPDATE contracts SET is_active=? WHERE id=?", (is_active, contract_id))

    @trace
    def get_contract_for_edit(self, contract_id: int) -> sqlite3.Row | None:
        return self.fetchone(
            """
            SELECT
                id,
                customer_id,
                truck_id,
                monthly_rate,
                COALESCE(NULLIF(start_date, ''), start_ym || '-01') AS start_date,
                CASE
                    WHEN end_date IS NOT NULL AND TRIM(end_date) <> '' THEN end_date
                    WHEN end_ym IS NOT NULL AND TRIM(end_ym) <> '' THEN end_ym || '-01'
                    ELSE NULL
                END AS end_date,
                notes,
                is_active
            FROM contracts
            WHERE id=?
            """,
            (contract_id,),
        )

    def get_preferred_contract_for_truck(self, truck_id: int) -> sqlite3.Row | None:
        return self.fetchone(
            """
            SELECT
                ct.id AS contract_id,
                ct.is_active,
                c.name AS customer_name,
                CASE
                    WHEN ct.truck_id IS NULL THEN 'Customer-level'
                    ELSE 'Per-truck'
                END AS scope,
                ct.monthly_rate,
                COALESCE(NULLIF(ct.start_date, ''), ct.start_ym || '-01') AS start_date,
                CASE
                    WHEN ct.end_date IS NOT NULL AND TRIM(ct.end_date) <> '' THEN ct.end_date
                    WHEN ct.end_ym IS NOT NULL AND TRIM(ct.end_ym) <> '' THEN ct.end_ym || '-01'
                    ELSE NULL
                END AS end_date,
                COALESCE(t.plate, '') AS plate
            FROM contracts ct
            JOIN customers c ON c.id = ct.customer_id
            LEFT JOIN trucks t ON t.id = ct.truck_id
            WHERE (
                ct.truck_id = ?
                OR (
                    ct.truck_id IS NULL
                    AND ct.customer_id = (SELECT customer_id FROM trucks WHERE id = ?)
                )
            )
            ORDER BY
                CASE
                    WHEN ct.truck_id = ? AND ct.is_active = 1 THEN 0
                    WHEN ct.truck_id = ? THEN 1
                    WHEN ct.truck_id IS NULL AND ct.is_active = 1 THEN 2
                    ELSE 3
                END,
                COALESCE(NULLIF(ct.start_date, ''), ct.start_ym || '-01') DESC,
                ct.id DESC
            LIMIT 1
            """,
            (truck_id, truck_id, truck_id, truck_id),
        )

    def update_contract(
        self,
        contract_id: int,
        customer_id: int,
        truck_id: int | None,
        monthly_rate: float,
        start_ym: str,
        end_ym: str | None,
        start_date: str,
        end_date: str | None,
        is_active: int,
        notes: str | None,
    ) -> None:
        self.execute(
            """
            UPDATE contracts
            SET customer_id=?,
                truck_id=?,
                monthly_rate=?,
                start_ym=?,
                end_ym=?,
                start_date=?,
                end_date=?,
                is_active=?,
                notes=?
            WHERE id=?
            """,
            (customer_id, truck_id, monthly_rate, start_ym, end_ym, start_date, end_date, is_active, notes, contract_id),
        )

    @trace
    def delete_contract(self, contract_id: int) -> None:
        self.execute("DELETE FROM contracts WHERE id=?", (contract_id,))

    @trace
    def get_contracts_for_customer_ledger(self, customer_id: int) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT ct.id, ct.is_active, ct.monthly_rate, ct.notes,
                   COALESCE(NULLIF(ct.start_date,''), ct.start_ym || '-01') AS start_d,
                   CASE
                       WHEN ct.end_date IS NOT NULL AND TRIM(ct.end_date)<>'' THEN ct.end_date
                       WHEN ct.end_ym  IS NOT NULL AND TRIM(ct.end_ym) <>'' THEN ct.end_ym || '-01'
                       ELSE NULL
                   END AS end_d,
                   COALESCE(ct.start_date, ct.start_ym) AS start_raw,
                   COALESCE(ct.end_date,   ct.end_ym)   AS end_raw,
                   CASE WHEN ct.truck_id IS NULL THEN 'Customer' ELSE 'Per Truck' END AS scope,
                   t.plate || COALESCE(' ' || t.state, '') AS truck_info
            FROM contracts ct
            LEFT JOIN trucks t ON t.id = ct.truck_id
            WHERE ct.customer_id = ?
            ORDER BY ct.is_active DESC, start_d ASC
            """,
            (customer_id,),
        )

    @trace
    def get_total_paid_for_contract(self, contract_id: int) -> float:
        row = self.fetchone(
            """
            SELECT COALESCE(SUM(p.amount), 0) AS total
            FROM payments p JOIN invoices i ON i.id=p.invoice_id
            WHERE i.contract_id=?
            """,
            (contract_id,),
        )
        return float(row["total"]) if row else 0.0

    @trace
    def get_payments_for_contract(self, contract_id: int) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT p.id, p.paid_at, p.amount, p.method,
                   COALESCE(p.reference,'') AS reference,
                   COALESCE(p.notes,'')     AS notes
            FROM payments p
            JOIN invoices i ON i.id=p.invoice_id
            WHERE i.contract_id=?
            ORDER BY p.paid_at ASC, p.id ASC
            """,
            (contract_id,),
        )

    @trace
    def get_contract_payment_history(self, contract_id: int) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT p.id, p.paid_at, p.amount, p.method,
                   COALESCE(p.reference, '') AS reference,
                   COALESCE(p.notes, '')     AS notes,
                   i.invoice_ym
            FROM payments p
            JOIN invoices i ON i.id = p.invoice_id
            WHERE i.contract_id = ?
            ORDER BY p.paid_at ASC, p.id ASC
            """,
            (contract_id,),
        )

    @trace
    def get_recent_payments_for_customer(self, customer_id: int, limit: int = 5) -> list[sqlite3.Row]:
        return self.fetchall(
            """
            SELECT p.paid_at, p.amount, p.method,
                   COALESCE(p.reference, '') AS reference,
                   COALESCE(p.notes, '') AS notes,
                 i.contract_id,
                 COALESCE(t.plate, '') AS plate
            FROM payments p
            JOIN invoices i ON i.id = p.invoice_id
            JOIN contracts ct ON ct.id = i.contract_id
             LEFT JOIN trucks t ON t.id = ct.truck_id
            WHERE ct.customer_id = ?
            ORDER BY p.paid_at DESC, p.id DESC
            LIMIT ?
            """,
            (customer_id, limit),
        )
