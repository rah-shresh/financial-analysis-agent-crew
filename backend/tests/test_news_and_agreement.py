"""Phase 9.2: the news that feeds sentiment is recent and real, and "models disagree" means it."""

import time
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from mcp_layer import server
from services.report_builder import build_overview, build_summary, models_agree


# --------------------------------------------------------------- model agreement
@pytest.mark.parametrize("arima, lstm, expected", [
    (1.5, 2.0, True),
    (-3.0, -0.8, True),
    (1.5, -2.0, False),
    (0.0, -7.0, None),          # ARIMA flat vs LSTM down: not a disagreement
    (4.0, 0.2, None),
    (-0.49, 0.6, None),
    (0.5, -0.5, False),         # exactly at the threshold counts as a move
])
def test_models_agree(arima, lstm, expected):
    assert models_agree(arima, lstm) is expected


def _state(arima, lstm):
    return {"ticker": "TCS.NS", "currency": "INR",
            "forecast": {"forecast_days": 30, "forecast_change_pct": arima, "confidence_interval_95":
                         {"lower": 1900.0, "upper": 3000.0}, "lstm": {"forecast_change_pct": lstm}}}


def test_flat_model_is_reported_as_neither_agreeing_nor_disagreeing():
    state = _state(0.0, -7.0)
    assert build_overview(state)["forecast_models_agree"] is None
    summary = build_summary(state)
    assert "neither clearly agree nor disagree" in summary and "disagree on direction" not in summary


def test_opposite_models_still_disagree():
    state = _state(1.5, -2.0)
    assert build_overview(state)["forecast_models_agree"] is False
    assert "disagree on direction" in build_summary(state)


# ------------------------------------------------------------------- news filter
def _entry(title, days_old=1):
    published = time.gmtime(time.time() - days_old * 86400) if days_old is not None else None
    return SimpleNamespace(title=title, published_parsed=published)


def _fetch(entries, **kwargs):
    feed = SimpleNamespace(bozo=False, entries=entries)
    captured = {}

    def fake_parse(url):
        captured["url"] = url
        return feed

    with patch.object(server, "_info", return_value={"longName": "Tata Consultancy Services Limited"}), \
         patch.object(server.feedparser, "parse", side_effect=fake_parse):
        return server.fetch_news_headlines("TCS.NS", **kwargs), captured["url"]


def test_news_keeps_only_recent_real_headlines_without_repeats():
    entries = [
        _entry("TCS wins a large cloud deal"),
        _entry("TCS Wins a Large Cloud Deal!"),                                        # same story, repeated
        _entry("Tata Consultancy Services Prediction for Tomorrow: 9 Oct 2026"),      # SEO filler
        _entry("Tata Consultancy Services Limited (TCS.BO) stock price, news, quote and history"),
        _entry("TCS announces layoffs", days_old=40),                                  # too old
        _entry("TCS quarterly results beat estimates", days_old=3),
        _entry("TCS share price falls", days_old=None),                                # undated: kept
    ]
    result, url = _fetch(entries)
    assert result["headlines"] == ["TCS wins a large cloud deal", "TCS quarterly results beat estimates",
                                   "TCS share price falls"]
    assert "when%3A14d" in url                                                         # Google News's own recency filter


def test_news_respects_the_headline_cap():
    result, _ = _fetch([_entry(f"TCS story number {i}") for i in range(20)], max_headlines=5)
    assert len(result["headlines"]) == 5


def test_news_with_nothing_recent_says_so():
    with pytest.raises(ValueError, match="last 14 days"):
        _fetch([_entry("TCS old story", days_old=60)])
