"""Helpers for comparing money shown in the UI with minor units returned by the API."""
import re

MONEY = re.compile(r"\d[\d,]*\.\d{2}")


def to_minor(text: str, index: int = 0) -> int:
    """'≈ ₪14,823.50' -> 1482350. Takes the `index`-th amount in the text (default: first)."""
    found = MONEY.findall(text)
    if not found:
        raise ValueError(f"No money amount in: {text!r}")
    return int(found[index].replace(",", "").replace(".", ""))


def ui_amount_to_minor(amount: str) -> int:
    """'100' -> 10000, '0.01' -> 1 (the user-typed value, 2 decimals for every currency)."""
    whole, _, frac = amount.replace(",", "").partition(".")
    return int(whole + frac.ljust(2, "0"))


def format_minor(minor: int) -> str:
    """1482350 -> '14,823.50' (the UI's en-US format, without the currency symbol)."""
    return f"{minor // 100:,}.{minor % 100:02d}"
