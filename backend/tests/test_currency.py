"""Prices must be shown in the currency the stock actually trades in (rupees for NSE/BSE, not dollars)."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from agents import preprocessor_agent
from agents.risk_agent import risk_node
from mcp_layer import server
from services.report_builder import build_overview, build_summary
from utils.currency import format_money, infer_currency
from utils.tickers import base_symbol, news_edition, not_found_hint


# ------------------------------------------------------------ utils.currency
@pytest.mark.parametrize("amount, currency, expected", [
    (1234.5, "USD", "$1,234.50"),
    (2470.1, "INR", "\u20b92,470.10"),
    (24701000.5, "INR", "\u20b92,47,01,000.50"),          # lakh/crore grouping
    (247010, "INR", "\u20b92,47,010.00"),
    (5000, "JPY", "\u00a55,000"),                          # yen has no decimals
    (-12.5, "EUR", "-\u20ac12.50"),
    (300.456, "GBp", "300.46p"),                            # London quotes in pence
    (300.456, "GBX", "300.46p"),
    (12.5, "XYZ", "XYZ\u00a012.50"),                       # unknown code is shown, not guessed
    (12.5, None, "12.50"),
    (-0.001, "USD", "$0.00"),                                # rounds to zero: no "-$0.00"
    (float("nan"), "USD", "\u2014"),
    (None, "INR", "\u2014"),
])
def test_format_money(amount, currency, expected):
    assert format_money(amount, currency) == expected


def test_format_money_explicit_decimals():
    assert format_money(2470.1, "INR", 0) == "\u20b92,470"
    assert format_money(1234.5, "USD", 0) == "$1,235"


@pytest.mark.parametrize("ticker, currency", [
    ("RELIANCE.NS", "INR"), ("532540.BO", "INR"), ("tcs.ns", "INR"), ("SAP.DE", "EUR"),
    ("7203.T", "JPY"), ("HSBA.L", "GBp"), ("TSLA", "USD"), ("BRK-B", "USD"), ("", "USD"),
])
def test_infer_currency(ticker, currency):
    assert infer_currency(ticker) == currency


# ------------------------------------------------------------- utils.tickers
def test_not_found_hint_points_bse_codes_and_bare_symbols_at_the_right_suffix():
    assert "532540.BO" in not_found_hint("532540") and "TCS.NS" in not_found_hint("532540")
    assert ".NS" in not_found_hint("RELIANCE")
    assert ".NS" not in not_found_hint("EURUSD=X") and ".NS" not in not_found_hint("BTC-USD")


def test_news_edition_and_base_symbol():
    assert news_edition("TCS.NS") == ("en-IN", "IN", "IN:en")
    assert news_edition("HSBA.L")[1] == "GB" and news_edition("TSLA")[1] == "US"
    assert base_symbol("TCS.NS") == "TCS" and base_symbol("TSLA") == "TSLA"
    assert base_symbol("^NSEI") == "^NSEI" and base_symbol("BRK-B") == "BRK-B"


# ------------------------------------------------------------- report text
def _state(ticker, currency):
    return {
        "ticker": ticker, "currency": currency,
        "technical_metrics": {"latest_close": 2470.1, "sma_20": 2455.5, "ema_20": 2460.0, "rsi_14": 55.0,
                              "trend": "above SMA (bullish bias)"},
        "forecast": {"forecast_days": 30, "forecast_change_pct": 2.1,
                     "confidence_interval_95": {"lower": 2300.0, "upper": 2900.0}},
    }


def test_report_summary_uses_rupees_for_an_indian_stock():
    summary = build_summary(_state("RELIANCE.NS", "INR"))
    assert "\u20b92,470.10" in summary and "\u20b92,455.50" in summary and "\u20b92,300-\u20b92,900" in summary
    assert "$" not in summary
    assert build_overview(_state("RELIANCE.NS", "INR"))["currency"] == "INR"


def test_report_summary_keeps_dollars_for_a_us_stock():
    summary = build_summary(_state("TSLA", "USD"))
    assert "$2,470.10" in summary and "$2,300-$2,900" in summary and "\u20b9" not in summary


def test_report_falls_back_to_the_ticker_suffix_when_the_currency_is_missing():
    assert build_overview(_state("TCS.NS", None))["currency"] == "INR"
    assert build_overview(_state("TSLA", None))["currency"] == "USD"


# --------------------------------------------------------------- risk agent
def test_risk_interpretation_is_written_in_the_stocks_currency():
    rng = np.random.default_rng(3)
    close = pd.Series(2400 + np.cumsum(rng.normal(0, 20, 120)), index=pd.bdate_range("2025-01-01", periods=120))
    out = risk_node({"ticker": "RELIANCE.NS", "currency": "INR", "price_data": pd.DataFrame({"Close": close}),
                     "agent_log": []})
    var = out["risk"]["value_at_risk_95"]
    assert "\u20b9" in var["interpretation"] and "$" not in var["interpretation"]
    assert isinstance(var["daily_dollar_per_share"], float)     # field name is part of the API, unchanged


# -------------------------------------------------------- preprocessor / MCP
def _ohlcv(**extra):
    return {"ticker": "X", "dates": ["2025-01-01", "2025-01-02"], "open": [1, 2], "high": [1, 2],
            "low": [1, 2], "close": [1, 2], "volume": [10, 10], **extra}


def test_preprocessor_takes_the_currency_from_the_data_tool_or_falls_back_to_the_suffix():
    with patch.object(preprocessor_agent, "call_tool", return_value=_ohlcv(currency="INR")):
        assert preprocessor_agent._fetch_data("TCS.NS")[1] == "INR"
    with patch.object(preprocessor_agent, "call_tool", return_value=_ohlcv()):     # older tool, no currency field
        assert preprocessor_agent._fetch_data("TCS.NS")[1] == "INR"
        assert preprocessor_agent._fetch_data("TSLA")[1] == "USD"


def test_price_tool_failure_explains_how_to_fix_the_ticker():
    with patch.object(server.yf, "download", return_value=pd.DataFrame()):
        with pytest.raises(ValueError, match=r"532540\.BO"):
            server.fetch_ohlcv("532540")


def test_news_search_uses_the_company_name_and_home_market_edition():
    captured = {}

    def fake_parse(url):
        captured["url"] = url
        return type("Feed", (), {"bozo": False, "entries": [type("E", (), {"title": "headline"})()]})()

    with patch.object(server, "_info", return_value={"longName": "Tata Consultancy Services Limited"}), \
         patch.object(server.feedparser, "parse", side_effect=fake_parse):
        assert server.fetch_news_headlines("TCS.NS")["headlines"] == ["headline"]
    assert "%22Tata+Consultancy+Services%22+stock" in captured["url"]
    assert "gl=IN" in captured["url"] and "TCS.NS" not in captured["url"]


def test_news_search_falls_back_to_the_bare_symbol_when_the_name_is_unknown():
    captured = {}

    def fake_parse(url):
        captured["url"] = url
        return type("Feed", (), {"bozo": False, "entries": [type("E", (), {"title": "headline"})()]})()

    with patch.object(server, "_info", side_effect=RuntimeError("rate limited")), \
         patch.object(server.feedparser, "parse", side_effect=fake_parse):
        server.fetch_news_headlines("TCS.NS")
    assert "q=TCS+stock" in captured["url"]
