# Project Aletheia - Limitations

## Data
- 15 earnings excerpts (not full transcripts) from 8 tickers
- Survivorship bias: only currently traded companies
- yfinance for prices (not licensed for commercial use)
- No historical index constituents for delisted stocks

## Models
- FinBERT: validated on 10 phrases (100% accuracy), not full transcripts
- RIV: 4 sample regulatory documents
- CMI: 3 sample companies

## Backtest
- Walk-forward: 288 OOS observations
- Synthetic factor data (Fama-French download failed)
- No transaction cost model for small caps
- Factor-neutral Sharpe: -0.02 (needs more data)

## Infrastructure
- Laptop: 4GB RAM, cannot run 24/7
- Colab: 12-hour session limit
- No automated scheduling
- No backup system beyond Google Drive

## Production Requirements
- Licensed data: $2,000-5,000/month
- Cloud compute: $1,000-3,000/month
- 2 additional engineers
- SEC/FCA regulatory registration