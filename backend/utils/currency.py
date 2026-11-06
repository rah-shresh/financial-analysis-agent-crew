"""
Currency handling: work out which currency a stock trades in, and format
money in it. A report for an Indian stock must say rupees, not dollars.

The authoritative source is Yahoo Finance itself (the MCP price tool asks it
for the currency). The suffix table below is only a fallback for when that
lookup fails; for suffix-less tickers the fallback is USD, because plain
Yahoo symbols (AAPL, TSLA) are US listings.
"""

import math
import re
from decimal import ROUND_HALF_UP, Decimal

# Yahoo ticker suffix -> currency code. Longest suffix wins.
_SUFFIX_CURRENCY = {
    ".NS": "INR", ".BO": "INR",
    ".L": "GBp",                      # London quotes in pence, not pounds
    ".T": "JPY", ".HK": "HKD", ".SI": "SGD", ".KS": "KRW", ".KQ": "KRW",
    ".SS": "CNY", ".SZ": "CNY", ".TO": "CAD", ".V": "CAD", ".AX": "AUD",
    ".SW": "CHF", ".DE": "EUR", ".PA": "EUR", ".MI": "EUR", ".AS": "EUR",
    ".MC": "EUR", ".BR": "EUR", ".LS": "EUR", ".HE": "EUR", ".VI": "EUR",
}

_SYMBOLS = {
    "USD": "$", "INR": "\u20b9", "EUR": "\u20ac", "GBP": "\u00a3", "JPY": "\u00a5",
    "CNY": "CN\u00a5", "HKD": "HK$", "CAD": "C$", "AUD": "A$", "SGD": "S$",
    "KRW": "\u20a9", "CHF": "CHF\u00a0",
}

_ZERO_DECIMAL = {"JPY", "KRW"}


def infer_currency(ticker: str) -> str:
    """Best guess from the ticker's Yahoo suffix. Used only when Yahoo's own answer is unavailable."""
    t = (ticker or "").upper()
    for suffix in sorted(_SUFFIX_CURRENCY, key=len, reverse=True):
        if t.endswith(suffix):
            return _SUFFIX_CURRENCY[suffix]
    return "USD"


def _group(value: float, decimals: int, indian: bool) -> str:
    # Round half up like the dashboard does (Python's own float formatting rounds 1234.5 down to 1234).
    text = format(Decimal(repr(value)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP), "f")
    whole, _, frac = text.partition(".")
    if indian and len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        head = re.sub(r"(?<=\d)(?=(\d\d)+$)", ",", head)   # 24,70 + ,100 -> 24,70,100 (lakh/crore style)
        whole = f"{head},{tail}"
    else:
        whole = f"{int(whole):,}"
    return f"{whole}.{frac}" if frac else whole


def format_money(amount: float, currency: str | None, decimals: int | None = None) -> str:
    """format_money(2470.1, 'INR') -> '₹2,470.10' | (247010, 'INR', 0) -> '₹2,47,010' | (12.5, 'USD') -> '$12.50'.
    An unknown currency code is shown as the code itself rather than guessing a symbol."""
    if amount is None or not math.isfinite(amount):
        return "\u2014"                  # a missing / NaN price reads as a dash, never "nan" or a crash
    code = (currency or "").strip()
    if code == "GBX":                  # Yahoo sometimes spells pence "GBX" instead of "GBp"
        code = "GBp"
    if decimals is None:
        decimals = 0 if code in _ZERO_DECIMAL else 2
    number = _group(abs(float(amount)), decimals, indian=(code == "INR"))
    sign = "-" if amount < 0 and any(c in "123456789" for c in number) else ""     # no "-$0.00"
    if code == "GBp":
        return f"{sign}{number}p"
    if not code:
        return f"{sign}{number}"
    prefix = _SYMBOLS.get(code, f"{code}\u00a0")
    return f"{sign}{prefix}{number}"
