"""Verify every chart uses real data"""
import duckdb, json, os

print("="*60)
print("COMPLETE DATA VERIFICATION")
print("="*60)

# ── 1. CANDLESTICK ──────────────────────────
print("\n1. CANDLESTICK CHART")
try:
    conn = duckdb.connect('aletheia.db')
    df = conn.execute("SELECT trade_date, open_price, high_price, low_price, close_price, volume FROM price_data WHERE ticker='AAPL' ORDER BY trade_date DESC LIMIT 5").fetchdf()
    cols = conn.execute("DESCRIBE price_data").fetchall()
    has_ohlcv = all(c[0] in ['open_price','high_price','low_price','close_price'] for c in cols)
    print(f"   Rows found: {len(df)}")
    print(f"   Has OHLCV columns: {has_ohlcv}")
    print(f"   Status: {'REAL DATA' if len(df)>0 and has_ohlcv else 'USING FALLBACK'}")
    conn.close()
except Exception as e:
    print(f"   ERROR: {e}")

# ── 2. CORRELATION HEATMAP ──────────────────
print("\n2. CORRELATION HEATMAP")
try:
    conn = duckdb.connect('aletheia.db')
    tickers = [r[0] for r in conn.execute("SELECT DISTINCT ticker FROM composite_signals LIMIT 8").fetchall()]
    valid = 0
    for t in tickers:
        n = conn.execute("SELECT COUNT(*) FROM price_data WHERE ticker=?", [t]).fetchone()[0]
        if n > 20:
            valid += 1
    print(f"   Tickers available: {len(tickers)}")
    print(f"   With enough price data: {valid}")
    print(f"   Status: {'REAL DATA' if valid >= 3 else 'USING FALLBACK'}")
    conn.close()
except Exception as e:
    print(f"   ERROR: {e}")

# ── 3. WATERFALL ─────────────────────────────
print("\n3. WATERFALL (P&L Attribution)")
try:
    with open('alpaca_data.json', 'r') as f:
        d = json.load(f)
    positions = d.get('positions', [])
    total_pnl = sum(p['unrealized_pl'] for p in positions)
    print(f"   Positions: {len(positions)}")
    print(f"   Total P&L: ${total_pnl:,.2f}")
    print(f"   Status: {'REAL DATA' if len(positions) > 0 else 'USING FALLBACK'}")
except:
    print(f"   No Alpaca data file")
    print(f"   Status: USING FALLBACK")

# ── 4. RISK GAUGES ───────────────────────────
print("\n4. RISK GAUGES")
try:
    conn = duckdb.connect('aletheia.db')
    df = conn.execute("SELECT adj_close FROM price_data WHERE ticker='AAPL' ORDER BY trade_date LIMIT 252").fetchdf()
    if len(df) > 10:
        returns = df['adj_close'].pct_change().dropna()
        sharpe = float(returns.mean() / returns.std() * (252**0.5))
        max_dd = float((returns.cumsum().cummax() - returns.cumsum()).max())
        print(f"   Sharpe from real data: {sharpe:.2f}")
        print(f"   Max DD from real data: {max_dd*100:.2f}%")
        print(f"   Status: REAL DATA")
    else:
        print(f"   Not enough data")
    conn.close()
except Exception as e:
    print(f"   ERROR: {e}")

# ── 5. NETWORK GRAPH ─────────────────────────
print("\n5. NETWORK GRAPH (Signal Correlation)")
try:
    conn = duckdb.connect('aletheia.db')
    ens = conn.execute("SELECT ticker, AVG(ens_final) FROM ens_scores WHERE id LIKE 'earn_%' GROUP BY ticker").fetchall()
    print(f"   Tickers with ENS scores: {len(ens)}")
    for e in ens:
        print(f"      {e[0]}: {e[1]:+.4f}")
    print(f"   Status: {'REAL DATA' if len(ens) >= 3 else 'USING FALLBACK'}")
    conn.close()
except Exception as e:
    print(f"   ERROR: {e}")

# ── 6. EVENT TIMELINE ────────────────────────
print("\n6. EVENT TIMELINE")
try:
    conn = duckdb.connect('aletheia.db')
    filings = conn.execute("SELECT ticker, event_date FROM transcripts_metadata WHERE source LIKE 'SEC_%' AND ticker='AAPL' LIMIT 5").fetchall()
    prices = conn.execute("SELECT COUNT(*) FROM price_data WHERE ticker='AAPL'").fetchone()[0]
    print(f"   SEC filings for AAPL: {len(filings)}")
    print(f"   Price rows for AAPL: {prices}")
    if filings:
        for f in filings:
            print(f"      {f[0]}: {f[1]}")
    print(f"   Status: {'REAL DATA' if len(filings) > 0 and prices > 0 else 'USING FALLBACK'}")
    conn.close()
except Exception as e:
    print(f"   ERROR: {e}")

# ── 7. EQUITY CURVE ──────────────────────────
print("\n7. EQUITY CURVE")
try:
    with open('alpaca_history.json', 'r') as f:
        hist = json.load(f)
    print(f"   Data points: {len(hist)}")
    if hist:
        print(f"   First: ${hist[0]['equity']:,.2f}")
        print(f"   Last: ${hist[-1]['equity']:,.2f}")
    print(f"   Status: {'REAL DATA' if len(hist) > 5 else 'USING FALLBACK'}")
except:
    print(f"   No history file")
    print(f"   Status: USING FALLBACK")

# ── 8. FinBERT SCORES ────────────────────────
print("\n8. FinBERT SCORES CHART")
try:
    conn = duckdb.connect('aletheia.db')
    scores = conn.execute("SELECT ticker, AVG(ens_final) as e, COUNT(*) as n FROM ens_scores WHERE id LIKE 'earn_%' GROUP BY ticker").fetchall()
    print(f"   Tickers: {len(scores)}")
    for s in scores:
        print(f"      {s[0]}: {s[1]:+.4f} ({s[2]} scores)")
    print(f"   Status: {'REAL FinBERT DATA' if len(scores) > 0 else 'USING FALLBACK'}")
    conn.close()
except Exception as e:
    print(f"   ERROR: {e}")

# ── 9. SIGNAL PANORAMA ───────────────────────
print("\n9. SIGNAL PANORAMA")
try:
    conn = duckdb.connect('aletheia.db')
    sig = conn.execute("SELECT ticker, composite_score, signal_direction FROM composite_signals").fetchall()
    print(f"   Composite signals: {len(sig)}")
    for s in sig:
        direction = 'LONG' if s[2]==1 else ('SHORT' if s[2]==-1 else 'NEUTRAL')
        print(f"      {s[0]}: {s[1]:+.4f} ({direction})")
    print(f"   Status: {'REAL DATA' if len(sig) > 0 else 'EMPTY'}")
    conn.close()
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60)