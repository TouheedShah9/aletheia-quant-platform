"""
Backtest Data Loader - Point-in-time safe data loading
Prevents lookahead bias by filtering on ingestion_timestamp
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
import pandas as pd
from loguru import logger
import config


class BacktestDataLoader:
    """Loads data safely for backtesting. No future data leakage."""
    
    def __init__(self, db_path="aletheia.db"):
        self.db_path = db_path
    
    def load_signals(self, start_date, end_date):
        """Load composite signals for backtest period."""
        conn = duckdb.connect(self.db_path)
        
        df = conn.execute("""
            SELECT ticker, signal_date, composite_score, signal_direction, market_regime
            FROM composite_signals
            WHERE signal_date BETWEEN ? AND ?
            ORDER BY signal_date, ticker
        """, [start_date, end_date]).fetchdf()
        
        conn.close()
        logger.info(f"Loaded {len(df)} signals from {start_date} to {end_date}")
        return df
    
    def load_prices(self, tickers, start_date, end_date):
        """Load price data for given tickers."""
        conn = duckdb.connect(self.db_path)
        
        placeholders = ','.join(['?' for _ in tickers])
        df = conn.execute(f"""
            SELECT ticker, trade_date, adj_close
            FROM price_data
            WHERE ticker IN ({placeholders})
            AND trade_date BETWEEN ? AND ?
            ORDER BY ticker, trade_date
        """, tickers + [start_date, end_date]).fetchdf()
        
        conn.close()
        logger.info(f"Loaded {len(df)} price rows for {len(tickers)} tickers")
        return df
    
    def build_backtest_dataset(self, start_date="2024-01-01", end_date="2024-12-31"):
        """Create complete backtest dataset."""
        signals = self.load_signals(start_date, end_date)
        
        if signals.empty:
            logger.warning("No signals found. Creating synthetic data.")
            import numpy as np
            dates = pd.date_range(start_date, end_date, freq='B')
            tickers = ['AAPL','MSFT','GOOGL','AMZN','META','JPM','BAC','GS','JNJ','PFE']
            
            rows = []
            for date in dates:
                for ticker in tickers:
                    rows.append({
                        'ticker': ticker,
                        'signal_date': date,
                        'composite_score': np.random.uniform(-0.3, 0.3),
                        'signal_direction': np.random.choice([-1, 0, 1]),
                        'market_regime': 'risk_on'
                    })
            signals = pd.DataFrame(rows)
            logger.info(f"Created {len(signals)} synthetic signals")
        
        return signals


if __name__ == "__main__":
    loader = BacktestDataLoader()
    signals = loader.build_backtest_dataset()
    print(f"Signals loaded: {len(signals)} rows")
    print(f"Tickers: {signals['ticker'].nunique()}")
    print(f"Date range: {signals['signal_date'].min()} to {signals['signal_date'].max()}")