import os
import time
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ── Config ──────────────────────────────────────────────
load_dotenv()
CONN = os.getenv("DB_CONN_STRING")
engine = create_engine(CONN)


# ── Read from stocks_naive ──────────────────────
print("Reading from stocks_naive...")
with engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM stocks_naive", conn)

print(f"Loaded {len(df):,} rows from stocks_naive")


# ── Cast columns to proper types ────────────────
df["date"]   = pd.to_datetime(df["date"])
df["open"]   = pd.to_numeric(df["open"],   errors="coerce")
df["high"]   = pd.to_numeric(df["high"],   errors="coerce")
df["low"]    = pd.to_numeric(df["low"],    errors="coerce")
df["close"]  = pd.to_numeric(df["close"],  errors="coerce")
df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
df["ticker"] = df["ticker"].astype(str)

df.dropna(subset=["date", "ticker", "close"], inplace=True)
df.sort_values(["ticker", "date"], inplace=True)
df.reset_index(drop=True, inplace=True)

print(f"After cleaning: {len(df):,} rows")


# ── Compute metrics ─────────────────────────────
print("Computing metrics...")

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

print("Metrics computed")


# ── Write stocks_optimized with proper types ────
print("\nWriting stocks_optimized to database...")
start = time.time()

df["date"] = df["date"].dt.strftime("%Y-%m-%d")

df.to_sql(
    "stocks_optimized",
    engine,
    if_exists="replace",
    index=False,
    chunksize=5000
)

elapsed = time.time() - start
print(f"Loaded in {elapsed:.2f} seconds")


# ── Add indexes ──────────────────────────────────
print("\nAdding indexes...")
with engine.connect() as conn:
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_ticker ON stocks_optimized (ticker)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_date ON stocks_optimized (date)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_ticker_date ON stocks_optimized (ticker, date)"
    ))
    conn.commit()
print("Indexes created")


# ──Benchmark naive vs optimized ────────────────
print("\nBenchmarking...")

# Naive query
with engine.connect() as conn:
    start = time.time()
    conn.execute(text("""
        SELECT date, ticker, close
        FROM stocks_naive
        WHERE ticker = 'AAPL'
        AND date > '2022-01-01'
    """)).fetchall()
    naive_time = time.time() - start

# Optimized query
with engine.connect() as conn:
    start = time.time()
    conn.execute(text("""
        SELECT date, ticker, close
        FROM stocks_optimized
        WHERE ticker = 'AAPL'
        AND date > '2022-01-01'
    """)).fetchall()
    opt_time = time.time() - start

    total_rows = conn.execute(
        text("SELECT COUNT(*) FROM stocks_optimized")
    ).fetchone()[0]


# ── Results ──────────────────────────────────────
speedup = naive_time / opt_time if opt_time > 0 else 0

print("\n========= PHASE 2 RESULTS =========")
print(f"Row count:         {total_rows:,}")
print(f"Naive query time:  {naive_time:.4f} seconds")
print(f"Optimized time:    {opt_time:.4f} seconds")
print(f"Speedup:           {speedup:.1f}x faster")
print("Added columns:     daily_return_pct, ma_50,")
print("                   volatility_30d, volume_spike")
print("Indexes:           ticker, date, ticker+date")
print("====================================")