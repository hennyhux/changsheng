from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from utils.billing_date_utils import elapsed_months_inclusive, parse_ymd


@dataclass(frozen=True)
class ContractBalance:
    months_elapsed: int
    expected_amount: float
    paid_total: float
    outstanding: float


def compute_contract_balance(
    monthly_rate: float,
    start_date_value: str | None,
    end_date_value: str | None,
    paid_total: float,
    as_of_date: date,
) -> ContractBalance | None:
    start_date = parse_ymd(str(start_date_value)) if start_date_value else None
    if not start_date:
        return None

    end_date = parse_ymd(str(end_date_value)) if end_date_value else None
    effective_end = min(end_date, as_of_date) if end_date else as_of_date
    months_elapsed = elapsed_months_inclusive(start_date, effective_end)
    expected_amount = float(monthly_rate) * months_elapsed
    outstanding = max(0.0, expected_amount - float(paid_total))

    return ContractBalance(
        months_elapsed=months_elapsed,
        expected_amount=expected_amount,
        paid_total=float(paid_total),
        outstanding=outstanding,
    )