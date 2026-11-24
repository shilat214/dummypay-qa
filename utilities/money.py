import re

MONEY = re.compile(r"\d[\d,]*\.\d{2}")


# Turns the first amount in a text into minor units ('≈ ₪14,823.50' -> 1482350).
def to_minor(text: str) -> int:
    amount = MONEY.search(text).group()
    return int(amount.replace(",", "").replace(".", ""))


# Turns an amount typed by the user into minor units ('100' -> 10000, '1,234.56' -> 123456).
def ui_amount_to_minor(amount: str) -> int:
    whole, _, frac = amount.replace(",", "").partition(".")
    return int(whole + frac.ljust(2, "0"))


# Formats minor units the way the page shows them, without the currency symbol (1482350 -> '14,823.50').
def format_minor(minor: int) -> str:
    return f"{minor // 100:,}.{minor % 100:02d}"
