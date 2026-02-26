from __future__ import annotations

from core.config import PHONE_PATTERN, PLATE_PATTERN, STATE_PATTERN


def normalize_whitespace(value: str) -> str:
    return " ".join(value.strip().split())


def required_text(label: str, value: str, max_len: int = 100) -> str:
    cleaned = normalize_whitespace(value)
    if not cleaned:
        raise ValueError(f"{label} is required.")
    if len(cleaned) > max_len:
        raise ValueError(f"{label} must be {max_len} characters or fewer.")
    return cleaned


def optional_text(label: str, value: str, max_len: int = 200) -> str | None:
    cleaned = normalize_whitespace(value)
    if not cleaned:
        return None
    if len(cleaned) > max_len:
        raise ValueError(f"{label} must be {max_len} characters or fewer.")
    return cleaned


def optional_phone(value: str) -> str | None:
    cleaned = normalize_whitespace(value)
    if not cleaned:
        return None
    if not PHONE_PATTERN.fullmatch(cleaned):
        raise ValueError("Phone format is invalid.")
    return cleaned


def required_plate(value: str) -> str:
    cleaned = normalize_whitespace(value).upper().replace("—", "-").replace("–", "-")
    if not cleaned:
        raise ValueError("Plate is required.")
    if not PLATE_PATTERN.fullmatch(cleaned):
        raise ValueError("Plate must be 2-15 chars (A-Z, 0-9, dash, space).")
    return cleaned


def optional_state(value: str) -> str | None:
    cleaned = normalize_whitespace(value).upper()
    if not cleaned:
        return None
    if not STATE_PATTERN.fullmatch(cleaned):
        raise ValueError("State must be exactly 2 letters (e.g., TX).")
    return cleaned


def positive_float(label: str, value: str) -> float:
    cleaned = normalize_whitespace(value).replace("$", "").replace(",", "")
    if not cleaned:
        raise ValueError(f"{label} is required.")
    try:
        number = float(cleaned)
    except ValueError:
        raise ValueError(f"{label} must be numeric.")
    if number <= 0:
        raise ValueError(f"{label} must be greater than 0.")
    return number


def positive_int(label: str, value: str) -> int:
    cleaned = normalize_whitespace(value)
    if not cleaned:
        raise ValueError(f"{label} is required.")
    try:
        number = int(cleaned)
    except ValueError:
        raise ValueError(f"{label} must be a whole number.")
    if number <= 0:
        raise ValueError(f"{label} must be greater than 0.")
    return number