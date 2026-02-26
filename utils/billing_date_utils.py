from __future__ import annotations

from datetime import date, datetime


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def today() -> date:
    return datetime.now().date()


def ym(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def parse_ym(value: str) -> tuple[int, int] | None:
    try:
        cleaned = value.strip()
        dt = datetime.strptime(cleaned, "%Y-%m")
        return dt.year, dt.month
    except Exception:
        return None


def parse_ymd(value: str) -> date | None:
    try:
        cleaned = value.strip()
        return datetime.strptime(cleaned, "%Y-%m-%d").date()
    except Exception:
        return None


def add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    month_value = month + delta
    year_value = year + (month_value - 1) // 12
    month_value = (month_value - 1) % 12 + 1
    return year_value, month_value


def elapsed_months_inclusive(start_date: date, end_date: date) -> int:
    if end_date < start_date:
        return 0
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    if end_date.day < start_date.day:
        months -= 1
    return max(0, months)