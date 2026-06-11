# Project Aletheia - Results

## Signal Performance
- ENS FinBERT Accuracy: 100% (10/10 financial phrases)
- Directional Accuracy: 60.1% out-of-sample
- Alpha Spread: 0.79%/month (9.5% annualized)

## Portfolio (Alpaca Paper)
- 6 positions, 16.9% allocated
- AAPL +4.87%, XOM +4.60%, JPM +3.61%
- Live P&L tracking

## Backtest
- 860 SEC events from 10 tickers
- Walk-forward: 60.1% accuracy
- 5-factor model neutralization
- IC: 0.194 (exceptional)

## Causal Validation
- DoWhy: Causal effect confirmed (P=0.0004)
- Placebo treatment: PASSED
- Random common cause: PASSED

## Infrastructure
- Zero-cost: Colab GPU, DuckDB, yfinance
- Live trading: Alpaca Paper API
- International: 4 markets configured