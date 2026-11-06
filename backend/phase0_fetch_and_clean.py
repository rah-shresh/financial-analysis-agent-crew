
"""
Phase 0 — Foundation
=====================
Goal (per spec.md, Phase 0): prove the data layer works before any agent
or orchestration logic sits on top of it.
 
What this script does, step by step:
1. Fetch OHLCV (Open/High/Low/Close/Volume) data for one ticker via yfinance
2. Clean it (fill missing values, treat extreme outliers)
3. Compute two basic technical indicators: SMA (20-day) and EMA (20-day)
4. Plot price + SMA + EMA and save it as a PNG
5. Print a short summary to the terminal
 
No agents. No LangGraph. No backend. No frontend. Just: does the data
pipeline work end to end for one ticker? Run this, look at the printed
summary and the PNG, and only then move on to Phase 1.
 
Usage:
    python phase0_fetch_and_clean.py TSLA
    python phase0_fetch_and_clean.py            # defaults to TSLA
"""
 
import sys
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use("Agg")  # so it works without a display (server/terminal-only)
import matplotlib.pyplot as plt
 
 
def fetch_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Download daily OHLCV data for the given ticker."""
    print(f"Fetching {period} of daily data for {ticker}...")
    df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
 
    if df.empty:
        raise ValueError(
            f"No data returned for '{ticker}'. Check the ticker symbol is correct "
            f"(e.g. 'TSLA', 'AAPL', 'RELIANCE.NS' for NSE-listed stocks)."
        )
 
    # yfinance sometimes returns MultiIndex columns for a single ticker — flatten them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
 
    df.index.name = "Date"
    print(f"  -> got {len(df)} rows, from {df.index.min().date()} to {df.index.max().date()}")
    return df
 
 
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic cleaning per spec.md Agent 1 responsibilities:
    - fill missing values (forward-fill, since price data is a time series)
    - treat outliers using a Z-score + capping (Winsorization) approach
    """
    df = df.copy()
 
    # 1. Missing values: forward-fill first (carry last known price forward),
    #    then back-fill any that are still missing at the very start
    missing_before = df["Close"].isna().sum()
    df = df.ffill().bfill()
    print(f"  -> filled {missing_before} missing Close values (forward/back-fill)")
 
    # 2. Outlier treatment on daily returns (not raw price, since price has a trend).
    #    A "outlier day" here means an unusually large single-day jump —
    #    we cap it rather than delete it, so we don't lose a trading day.
    returns = df["Close"].pct_change()
    mean, std = returns.mean(), returns.std()
    z_scores = (returns - mean) / std
 
    outlier_mask = z_scores.abs() > 3  # more than 3 standard deviations = outlier
    n_outliers = int(outlier_mask.sum())
 
    if n_outliers > 0:
        # Winsorize: cap the return at +/- 3 std devs instead of dropping the row
        cap_upper = mean + 3 * std
        cap_lower = mean - 3 * std
        capped_returns = returns.clip(lower=cap_lower, upper=cap_upper)
 
        # Rebuild a "cleaned" close price series from the capped returns
        cleaned_close = df["Close"].copy()
        for i in range(1, len(cleaned_close)):
            if outlier_mask.iloc[i]:
                prev_price = cleaned_close.iloc[i - 1]
                cleaned_close.iloc[i] = prev_price * (1 + capped_returns.iloc[i])
        df["Close"] = cleaned_close
 
    print(f"  -> detected and capped {n_outliers} outlier day(s) (|z-score| > 3)")
    return df
 
 
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add SMA-20 and EMA-20 columns."""
    df = df.copy()
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    return df
 
 
def plot_price(df: pd.DataFrame, ticker: str, out_path: str) -> None:
    """Plot Close price with SMA-20 and EMA-20 overlays, save as PNG."""
    plt.figure(figsize=(11, 5))
    plt.plot(df.index, df["Close"], label="Close Price", color="#26241D", linewidth=1.4)
    plt.plot(df.index, df["SMA_20"], label="SMA (20-day)", color="#9C3B2C", linewidth=1.2)
    plt.plot(df.index, df["EMA_20"], label="EMA (20-day)", color="#2F5D50", linewidth=1.2)
    plt.title(f"{ticker} — Price with SMA/EMA (Phase 0)")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  -> saved chart to {out_path}")
 
 
def print_summary(df: pd.DataFrame, ticker: str) -> None:
    """Print a short, human-readable summary — this is the 'proof it works' output."""
    latest = df.iloc[-1]
    print("\n" + "=" * 50)
    print(f"PHASE 0 SUMMARY — {ticker}")
    print("=" * 50)
    print(f"Latest date:       {df.index[-1].date()}")
    print(f"Latest close:      {latest['Close']:.2f}")
    print(f"SMA (20-day):      {latest['SMA_20']:.2f}")
    print(f"EMA (20-day):      {latest['EMA_20']:.2f}")
    trend = "above" if latest["Close"] > latest["SMA_20"] else "below"
    print(f"Price is currently {trend} its 20-day SMA.")
    print("=" * 50)
 
 
def main():
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "TSLA"
 
    raw_df = fetch_data(ticker)
    clean_df = clean_data(raw_df)
    enriched_df = add_indicators(clean_df)
 
    out_path = f"{ticker}_phase0_chart.png"
    plot_price(enriched_df, ticker, out_path)
    print_summary(enriched_df, ticker)
 
 
if __name__ == "__main__":
    main()
 
