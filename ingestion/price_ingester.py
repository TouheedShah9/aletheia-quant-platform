"""
Price Data Ingester - Multi-market OHLCV via yfinance
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import duckdb
import yfinance as yf
from loguru import logger
from ingestion.base_ingester import BaseIngester
import config


class PriceIngester(BaseIngester):
    def __init__(self):
        super().__init__("yfinance", rate_limit=2.0)

    def fetch_ticker(self, ticker, start, end):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start, end=end)
            if df.empty:
                logger.warning(f"No data for {ticker}")
                return None
            df = df.reset_index()
            df['ticker'] = ticker
            df['trade_date'] = df['Date'].dt.date
            return df
        except Exception as e:
            logger.error(f"Failed {ticker}: {e}")
            return None

    def ingest_all(self, db_path="aletheia.db"):
        conn = duckdb.connect(db_path)
        total = len(config.ALL_TICKERS)

        for i, entry in enumerate(config.ALL_TICKERS):
            ticker = entry['ticker']
            market = entry['market']
            logger.info(f"[{i+1}/{total}] {ticker} ({market})")

            df = self.fetch_ticker(ticker, config.DATA_START, config.DATA_END)
            if df is not None and not df.empty:
                count = 0
                for _, row in df.iterrows():
                    try:
                        conn.execute("""
                            INSERT OR REPLACE INTO price_data 
                            (id, ticker, trade_date, adj_close, volume, ingestion_timestamp)
                            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, [
                            f"{ticker}_{row['trade_date']}",
                            row['ticker'],
                            row['trade_date'],
                            float(row['Close']),
                            int(row['Volume']) if pd.notna(row['Volume']) else 0
                        ])
                        count += 1
                    except:
                        pass
                logger.info(f"  -> {count} rows")
            else:
                logger.warning(f"  -> Skipped")

            time.sleep(self.rate_limit)

        conn.close()
        logger.info("Price ingestion complete.")


if __name__ == "__main__":
    import pandas as pd
    ingester = PriceIngester()
    ingester.ingest_all()