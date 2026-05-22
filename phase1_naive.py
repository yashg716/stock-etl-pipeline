import os
import time
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, String

# ── Config ──────────────────────────────────────────────
load_dotenv()
CONN = os.getenv("DB_CONN_STRING")
engine = create_engine(CONN)

# ── Step 1: Get tickers ─────────────────────────────────
url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
sp500 = pd.read_csv(url)
tickers = sp500["Symbol"].str.replace(".", "-", regex=False).tolist()
print(f"Total tickers: {len(tickers)}")

# ── Step 2: Download data ───────────────────────────────
df = yf.download(
    tickers,
    start="2019-01-01",
    end="2024-12-31",
    group_by="ticker",
    auto_adjust=True,
    threads=True
)

# ── Step 3: Flatten to long format ──────────────────────
frames = []
for ticker in tickers:
    try:
        temp = df[ticker].copy()
        temp["ticker"] = ticker
        temp.reset_index(inplace=True)
        frames.append(temp)
    except KeyError:
        pass

combined = pd.concat(frames, ignore_index=True)
combined.columns = [c.lower().replace(" ", "_") for c in combined.columns]
print(f"Shape: {combined.shape}")

# ── Step 4: Save CSV and check size ─────────────────────
combined.to_csv("stock_data_naive.csv", index=False)
size = os.path.getsize("stock_data_naive.csv")
print(f"CSV size: {size / (1024*1024):.1f} MB")

# ── Step 5: Load to Neon (naive — all TEXT, no indexes) ─
print("\nLoading to Supabase... (this takes 3-5 mins)")
combined.to_sql(
    "stocks_naive",
    engine,
    if_exists="replace",
    index=False,
    dtype={col: String() for col in combined.columns}
)
print("Loaded to Neon")

# ── Step 6: Benchmark ───────────────────────────────────
with engine.connect() as conn:
    count = conn.execute(text("SELECT COUNT(*) FROM stocks_naive")).fetchone()[0]

    start = time.time()
    conn.execute(text("""
        SELECT date, ticker, close
        FROM stocks_naive
        WHERE ticker = 'AAPL'
        AND date > '2022-01-01'
    """)).fetchall()
    elapsed = time.time() - start

print("\n========= PHASE 1 BASELINE =========")
print(f"CSV size:   {size / (1024*1024):.1f} MB")
print(f"Row count:  {count}")
print(f"Query time: {elapsed:.4f} seconds")
print("=====================================")