"""Ticker-symbol helpers: help for symbols Yahoo doesn't recognise, the news edition to
search for a market, and the bare symbol without its exchange suffix."""


# Google News edition per exchange suffix: (hl, gl, ceid). Everything else uses the US edition.
_NEWS_EDITIONS = {
    ".NS": ("en-IN", "IN", "IN:en"),
    ".BO": ("en-IN", "IN", "IN:en"),
    ".L": ("en-GB", "GB", "GB:en"),
}
_US_EDITION = ("en-US", "US", "US:en")


def news_edition(ticker: str) -> tuple[str, str, str]:
    """(hl, gl, ceid) for the Google News RSS feed, so an Indian stock reads Indian news."""
    t = (ticker or "").strip().upper()
    for suffix, edition in _NEWS_EDITIONS.items():
        if t.endswith(suffix):
            return edition
    return _US_EDITION


def base_symbol(ticker: str) -> str:
    """'TCS.NS' -> 'TCS' (the symbol without its exchange suffix); '^NSEI', 'BRK-B' are left alone."""
    t = (ticker or "").strip().upper()
    if t.startswith("^") or "-" in t:
        return t
    return t.rsplit(".", 1)[0] if "." in t else t


def not_found_hint(ticker: str) -> str:
    t = (ticker or "").strip().upper()
    if t.isdigit():
        return (f"'{t}' looks like an Indian BSE scrip code. Yahoo Finance needs a suffix: "
                f"try {t}.BO (BSE), or use the NSE symbol with .NS (for example TCS.NS).")
    if "." not in t and not t.startswith("^") and "-" not in t and "=" not in t:
        return ("For Indian stocks add .NS (NSE) or .BO (BSE), for example RELIANCE.NS. "
                "Other markets use suffixes too, such as .L (London) or .T (Tokyo).")
    return "Check the symbol on finance.yahoo.com: it has to match Yahoo's symbol exactly."
