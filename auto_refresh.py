import os
import time
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
print("Loaded:", os.getenv("DB_CONN_STRING"))

conn_string = os.getenv("DB_CONN_STRING")

if not conn_string:
    raise ValueError("DB_CONN_STRING is missing. Check your .env file.")

engine = create_engine(
    conn_string,
    connect_args={"sslmode": "require"}
)

# ── Config ──────────────────────────────────────────────
load_dotenv()
engine = create_engine(
    os.getenv("DB_CONN_STRING"),
)

# ── Step 1: Get S&P 500 tickers ─────────────────────────
def get_tickers():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
    sp500 = pd.read_csv(url)
    return sp500["Symbol"].str.replace(".", "-", regex=False).tolist()

# ── Step 2: Find what date we already have in Neon (now supabase) ──────
def get_latest_date():
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT MAX(date) FROM stocks_optimized")
        ).fetchone()[0]
    if result is None:
        return datetime(2019, 1, 1).date()
    # Fix: convert string to date if needed
    if isinstance(result, str):
        return datetime.strptime(result, "%Y-%m-%d").date()
    return result

# ── Step 3: Download only missing days ──────────────────
def download_new_data(tickers, from_date):
    start = (from_date + timedelta(days=1)).strftime("%Y-%m-%d")
    end   = datetime.today().strftime("%Y-%m-%d")

    if start >= end:
        print("✅ Already up to date — no new data to download")
        return None

    print(f"Downloading data from {start} to {end}...")
    df = yf.download(
        tickers,
        start=start,
        end=end,
        group_by="ticker",
        auto_adjust=True,
        threads=True
    )

    frames = []
    for ticker in tickers:
        try:
            temp = df[ticker].copy()
            temp["ticker"] = ticker
            temp.reset_index(inplace=True)
            frames.append(temp)
        except KeyError:
            pass

    if not frames:
        print("No new data found")
        return None

    combined = pd.concat(frames, ignore_index=True)
    combined.columns = [c.lower().replace(" ", "_") for c in combined.columns]
    print(f"Downloaded {len(combined):,} new rows")
    return combined

# ── Step 4: Compute metrics ─────────────────────────────
def compute_metrics(df):
    df = df.sort_values(["ticker", "date"]).copy()

    # Daily return %
    df["daily_return_pct"] = df.groupby("ticker")["close"].pct_change() * 100

    # 50-day moving average
    df["ma_50"] = (
        df.groupby("ticker")["close"]
        .transform(lambda x: x.rolling(50, min_periods=1).mean())
    )

    # 30-day rolling volatility (annualised)
    df["volatility_30d"] = (
        df.groupby("ticker")["daily_return_pct"]
        .transform(lambda x: x.rolling(30, min_periods=1).std() * (252 ** 0.5))
    )

    # Volume spike ratio
    df["volume_spike"] = (
        df.groupby("ticker")["volume"]
        .transform(lambda x: x / x.rolling(30, min_periods=1).mean())
    )

    return df

# ── Step 5: Append only new rows to supabase ────────────────
def append_to_supabase(df):
    print(f"Appending {len(df):,} rows to Supabase...")
    start = time.time()

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    df.to_sql(
        "stocks_optimized",
        engine,
        if_exists="append",
        index=False,
        chunksize=5000
    )

    elapsed = time.time() - start
    print(f"✅ Appended in {elapsed:.2f} seconds")

# ── Main ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 45)
    print(f"  AUTO REFRESH — {datetime.today().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 45)

    tickers        = get_tickers()
    latest_date    = get_latest_date()
    print(f"Latest date in DB: {latest_date}")

    new_data = download_new_data(tickers, latest_date)

    if new_data is not None:
        new_data = compute_metrics(new_data)
        append_to_supabase(new_data)

        with engine.connect() as conn:
            total = conn.execute(
                text("SELECT COUNT(*) FROM stocks_optimized")
            ).fetchone()[0]

        print(f"\n{'='*45}")
        print(f"  Total rows in DB: {total:,}")
        print(f"  New rows added:   {len(new_data):,}")
        print(f"{'='*45}")
    else:
        print("Nothing to do — DB is current")