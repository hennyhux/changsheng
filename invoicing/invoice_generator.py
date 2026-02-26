from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import uuid
from typing import Any, Mapping

from data.database_service import DatabaseService
from core.app_logging import trace


@dataclass
class ContractInvoiceLine:
    contract_id: int
    customer_name: str
    scope: str
    monthly_rate: float
    start_date: str
    end_date: str
    months_elapsed: int
    expected_amount: float
    paid_total: float
    outstanding: float
    status: str


@dataclass
class CustomerInvoiceGroup:
    customer_name: str
    contracts: list[ContractInvoiceLine]
    total_expected: float
    total_paid: float
    total_outstanding: float
    status: str


@dataclass
class PdfContractLine:
    contract_id: int
    scope: str
    monthly_rate: float
    start_date: str
    end_date: str
    expected: float
    paid: float
    outstanding: float


@dataclass
class PdfPaymentLine:
    paid_at: str
    amount: float
    method: str
    contract_id: int
    plate: str
    reference: str
    notes: str


@dataclass
class PdfInvoiceData:
    customer_name: str
    phone: str | None
    company: str | None
    invoice_uuid: str
    as_of_date: date
    contracts: list[PdfContractLine]
    total_expected: float
    total_paid: float
    total_outstanding: float
    next_due_date: date | None
    recent_payments: list[PdfPaymentLine]


def _parse_ymd(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def _elapsed_months_inclusive(start_date: date, end_date: date) -> int:
    if end_date < start_date:
        return 0
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    if end_date.day < start_date.day:
        months -= 1
    return max(0, months)


def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    m = month + delta
    y = year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    return y, m


def _next_due_after(start: date, as_of: date) -> date:
    if as_of <= start:
        return start
    if as_of.day <= start.day:
        due_year, due_month = as_of.year, as_of.month
    else:
        due_year, due_month = _add_months(as_of.year, as_of.month, 1)

    next_year, next_month = _add_months(due_year, due_month, 1)
    last_day = (date(next_year, next_month, 1) - timedelta(days=1)).day
    due_day = min(start.day, last_day)
    return date(due_year, due_month, due_day)


def _build_contract_line(
    db: DatabaseService,
    row: Mapping[str, Any],
    as_of_date: date,
) -> ContractInvoiceLine | None:
    start_date_str = str(row["start_date"]) if row["start_date"] else ""
    start_date = _parse_ymd(start_date_str)
    if not start_date:
        return None

    end_date_str = str(row["end_date"]) if row["end_date"] else ""
    parsed_end = _parse_ymd(end_date_str) if end_date_str else None
    effective_end = min(parsed_end, as_of_date) if parsed_end else as_of_date

    months_elapsed = _elapsed_months_inclusive(start_date, effective_end)
    monthly_rate = float(row["monthly_rate"])
    expected_amount = monthly_rate * months_elapsed
    contract_id = int(row["contract_id"])
    paid_total = db.get_paid_total_for_contract_as_of(contract_id, as_of_date.isoformat())
    outstanding = expected_amount - paid_total

    return ContractInvoiceLine(
        contract_id=contract_id,
        customer_name=str(row["customer_name"]),
        scope=str(row["plate"]) if row["plate"] else "(customer-level)",
        monthly_rate=monthly_rate,
        start_date=start_date_str,
        end_date=end_date_str,
        months_elapsed=months_elapsed,
        expected_amount=expected_amount,
        paid_total=paid_total,
        outstanding=outstanding,
        status="PAID" if outstanding <= 0.01 else "DUE",
    )


@trace
def build_invoice_groups(db: DatabaseService, as_of_date: date) -> tuple[list[CustomerInvoiceGroup], float]:
    rows = db.get_active_contracts_with_customer_plate_for_invoices()

    grouped: dict[int, dict[str, Any]] = {}
    for row in rows:
        customer_id = int(row["customer_id"])
        customer_name = str(row["customer_name"])
        if customer_id not in grouped:
            grouped[customer_id] = {"name": customer_name, "rows": []}
        grouped[customer_id]["rows"].append(row)

    groups: list[CustomerInvoiceGroup] = []
    total_outstanding = 0.0

    for customer_id in sorted(grouped.keys(), key=lambda cid: grouped[cid]["name"]):
        customer_name = str(grouped[customer_id]["name"])
        contract_rows = grouped[customer_id]["rows"]

        lines: list[ContractInvoiceLine] = []
        total_expected = 0.0
        total_paid = 0.0
        customer_outstanding = 0.0

        for row in contract_rows:
            line = _build_contract_line(db, row, as_of_date)
            if not line:
                continue
            lines.append(line)
            total_expected += line.expected_amount
            total_paid += line.paid_total
            customer_outstanding += line.outstanding
            total_outstanding += line.outstanding

        customer_status = "PAID" if customer_outstanding <= 0.01 else "DUE"
        groups.append(
            CustomerInvoiceGroup(
                customer_name=customer_name,
                contracts=lines,
                total_expected=total_expected,
                total_paid=total_paid,
                total_outstanding=customer_outstanding,
                status=customer_status,
            )
        )

    return groups, total_outstanding


@trace
def build_pdf_invoice_data(
    db: DatabaseService,
    customer_id: int,
    as_of_date: date,
    payments_limit: int = 5,
) -> PdfInvoiceData | None:
    customer_row = db.get_customer_basic_by_id(customer_id)
    if not customer_row:
        return None

    contracts = db.get_active_contracts_for_customer_invoice(customer_id)
    paid_rows = db.get_paid_totals_by_contract_as_of(as_of_date.isoformat())
    paid_by_contract = {int(r["contract_id"]): float(r["paid_total"]) for r in paid_rows}
    contract_lines: list[PdfContractLine] = []

    total_expected = 0.0
    total_paid = 0.0
    total_outstanding = 0.0
    next_due_date: date | None = None

    for row in contracts:
        start_date_str = str(row["start_date"]) if row["start_date"] else ""
        start = _parse_ymd(start_date_str)
        if not start:
            continue

        end_date_str = str(row["end_date"]) if row["end_date"] else ""
        monthly_rate = float(row["monthly_rate"])

        months = _elapsed_months_inclusive(start, as_of_date)
        expected = monthly_rate * months
        paid = paid_by_contract.get(int(row["id"]), 0.0)
        outstanding = expected - paid

        total_expected += expected
        total_paid += paid
        total_outstanding += outstanding

        if outstanding > 0.01 and monthly_rate > 0:
            due_date = _next_due_after(start, as_of_date)
            if end_date_str:
                parsed_end = _parse_ymd(end_date_str)
                if parsed_end and due_date > parsed_end:
                    due_date = parsed_end
            if next_due_date is None or due_date < next_due_date:
                next_due_date = due_date

        contract_lines.append(
            PdfContractLine(
                contract_id=int(row["id"]),
                scope=str(row["plate"]) if row["plate"] else "(customer-level)",
                monthly_rate=monthly_rate,
                start_date=start_date_str,
                end_date=end_date_str,
                expected=expected,
                paid=paid,
                outstanding=outstanding,
            )
        )

    payments = []
    for payment in db.get_recent_payments_for_customer(customer_id, limit=payments_limit):
        payments.append(
            PdfPaymentLine(
                paid_at=str(payment["paid_at"]),
                amount=float(payment["amount"]),
                method=str(payment["method"]),
                contract_id=int(payment["contract_id"]),
                plate=str(payment["plate"] or ""),
                reference=str(payment["reference"] or ""),
                notes=str(payment["notes"] or ""),
            )
        )

    return PdfInvoiceData(
        customer_name=str(customer_row["name"]),
        phone=customer_row["phone"],
        company=customer_row["company"],
        invoice_uuid=str(uuid.uuid4()),
        as_of_date=as_of_date,
        contracts=contract_lines,
        total_expected=total_expected,
        total_paid=total_paid,
        total_outstanding=total_outstanding,
        next_due_date=next_due_date,
        recent_payments=payments,
    )
