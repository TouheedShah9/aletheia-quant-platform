"""Audit every chart's data source for problems"""
import duckdb, json

conn = duckdb.connect('aletheia.db')

print('='*60)
print('CHART DATA AUDIT')
print('='*60)

# 1. Candlestick
print('\n1. CANDLESTICK:')
cols = [c[0] for c in conn.execute('DESCRIBE price_data').fetchall()]
has_ohlcv = all(c in cols for c in ['open_price','high_price','low_price','close_price'])
sample = conn.execute("SELECT open_price, high_price, low_price, close_price, volume FROM price_data WHERE ticker='AAPL' LIMIT 1").fetchone()
print(f'   OHLCV columns: {has_ohlcv}')
print(f'   Sample: O={sample[0]:.2f} H={sample[1]:.2f} L={sample[2]:.2f} C={sample[3]:.2f} V={sample[4]:,}')

# 2. Correlation
print('\n2. CORRELATION HEATMAP:')
tickers = [r[0] for r in conn.execute('SELECT DISTINCT ticker FROM composite_signals').fetchall()]
for t in tickers:
    n = conn.execute('SELECT COUNT(*) FROM price_data WHERE ticker=?', [t]).fetchone()[0]
    print(f'   {t}: {n} rows')

# 3. Waterfall
print('\n3. WATERFALL:')
try:
    with open('alpaca_data.json') as f:
        d = json.load(f)
    for p in d.get('positions', []):
        print(f'   {p["symbol"]}: ${p["unrealized_pl"]:,.2f}')
except:
    print('   No Alpaca data')

# 4. Risk Gauges
print('\n4. RISK GAUGES:')
for t in ['AAPL','MSFT']:
    df = conn.execute('SELECT adj_close FROM price_data WHERE ticker=? ORDER BY trade_date', [t]).fetchdf()
    if len(df) > 100:
        ret = df['adj_close'].pct_change().dropna()
        sharpe = float(ret.mean() / ret.std() * (252**0.5))
        dd = float((ret.cumsum().cummax() - ret.cumsum()).max())
        print(f'   {t}: Sharpe={sharpe:.2f} MaxDD={dd*100:.2f}%')

# 5. Network Graph
print('\n5. NETWORK GRAPH:')
for e in conn.execute("SELECT ticker, AVG(ens_final) FROM ens_scores WHERE id LIKE 'earn_%' GROUP BY ticker").fetchall():
    valid = -1 <= e[1] <= 1
    print(f'   {e[0]}: {e[1]:+.4f} {"OK" if valid else "INVALID"}')

# 6. Event Timeline
print('\n6. EVENT TIMELINE:')
filings = conn.execute("SELECT event_date FROM transcripts_metadata WHERE source LIKE 'SEC_%' AND ticker='AAPL' LIMIT 5").fetchall()
prices = conn.execute("SELECT MIN(trade_date), MAX(trade_date) FROM price_data WHERE ticker='AAPL'").fetchone()
print(f'   Filings: {len(filings)}, Price range: {prices[0]} to {prices[1]}')

# 7. Sparklines
print('\n7. SPARKLINES:')
print('   ⚠️ Uses synthetic data (np.random) — decorative only')

# 8. ENS Chart
print('\n8. FinBERT CHART:')
n = conn.execute("SELECT COUNT(*) FROM ens_scores WHERE id LIKE 'earn_%'").fetchone()[0]
print(f'   Real scores: {n}')

# 9. Signal Panorama
print('\n9. SIGNAL PANORAMA:')
for d in conn.execute('SELECT signal_direction, COUNT(*) FROM composite_signals GROUP BY signal_direction').fetchall():
    side = 'LONG' if d[0]==1 else ('SHORT' if d[0]==-1 else 'NEUTRAL')
    print(f'   {side}: {d[1]}')

conn.close()
print('\n' + '='*60)