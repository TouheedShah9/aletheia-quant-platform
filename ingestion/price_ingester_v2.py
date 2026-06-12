"""
Price Ingester V2 — Downloads full OHLCV data
Replaces old price_data with open, high, low, close, adj_close, volume
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
import yfinance as yf
import time
from datetime import datetime
import config

conn = duckdb.connect('aletheia.db')

# Drop old price_data and recreate with OHLCV
conn.execute("DROP TABLE IF EXISTS price_data")
conn.execute("""
    CREATE TABLE price_data (
        id VARCHAR PRIMARY KEY,
        ticker VARCHAR NOT NULL,
        trade_date DATE NOT NULL,
        open_price DOUBLE,
        high_price DOUBLE,
        low_price DOUBLE,
        close_price DOUBLE,
        adj_close DOUBLE NOT NULL,
        volume BIGINT,
        ingestion_timestamp TIMESTAMP NOT NULL
    )
""")

total_tickers = len(config.ALL_TICKERS)
downloaded = 0

for i, entry in enumerate(config.ALL_TICKERS):
    ticker = entry['ticker']
    market = entry['market']
    
    print(f"[{i+1}/{total_tickers}] {ticker} ({market})...", end=' ')
    
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=config.DATA_START, end=config.DATA_END)
        
        if df.empty:
            print("No data")
            continue
        
        df = df.reset_index()
        stored = 0
        
        for _, row in df.iterrows():
            trade_date = row['Date'].date() if hasattr(row['Date'], 'date') else str(row['Date'])[:10]
            
            conn.execute("""
                INSERT INTO price_data (id, ticker, trade_date, open_price, high_price, low_price, close_price, adj_close, volume, ingestion_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, [
                f"{ticker}_{trade_date}",
                ticker,
                trade_date,
                float(row['Open']) if str(row['Open']) != 'nan' else None,
                float(row['High']) if str(row['High']) != 'nan' else None,
                float(row['Low']) if str(row['Low']) != 'nan' else None,
                float(row['Close']) if str(row['Close']) != 'nan' else None,
                float(row['Close']),
                int(row['Volume']) if str(row['Volume']) != 'nan' else 0
            ])
            stored += 1
        
        downloaded += 1
        print(f"{stored} rows ✅")
        
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(1.5)

# Verify
count = conn.execute("SELECT COUNT(*) FROM price_data").fetchone()[0]
tickers = conn.execute("SELECT COUNT(DISTINCT ticker) FROM price_data").fetchone()[0]
sample = conn.execute("SELECT * FROM price_data WHERE ticker='AAPL' LIMIT 1").fetchone()

conn.close()

print(f"\n{'='*50}")
print(f"OHLCV INGESTION COMPLETE")
print(f"{'='*50}")
print(f"Total rows: {count:,}")
print(f"Tickers: {tickers}")
print(f"Sample AAPL: date={sample[2]}, O={sample[3]:.2f}, H={sample[4]:.2f}, L={sample[5]:.2f}, C={sample[6]:.2f}, V={sample[8]:,}")
print(f"{'='*50}")