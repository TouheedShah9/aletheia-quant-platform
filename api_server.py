"""
ALETHEIA API Server — Serves real data to any frontend (React, mobile, etc.)
Replaces Streamlit with a proper REST API
All data is LIVE from your existing database and Alpaca
"""
import sys, os, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import duckdb
from datetime import datetime
from typing import Optional

app = FastAPI(
    title="ALETHEIA Alpha Intelligence API",
    description="Real-time financial alpha signals, portfolio data, and AI insights",
    version="1.0.0"
)

# Allow any frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = str(Path(__file__).parent / 'aletheia.db')


def get_db():
    return duckdb.connect(DB_PATH)


# ═══════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════
@app.get("/")
def root():
    return {
        "system": "ALETHEIA Alpha Intelligence API",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    conn = get_db()
    try:
        tables = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='main'").fetchone()[0]
        prices = conn.execute("SELECT COUNT(*) FROM price_data").fetchone()[0]
        signals = conn.execute("SELECT COUNT(*) FROM composite_signals").fetchone()[0]
        return {
            "database": "healthy",
            "tables": tables,
            "price_rows": prices,
            "signals": signals,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        conn.close()


# ═══════════════════════════════════
# COMPOSITE SIGNALS
# ═══════════════════════════════════
@app.get("/signals")
def get_signals(
    ticker: Optional[str] = None,
    min_score: Optional[float] = None,
    direction: Optional[str] = None
):
    """Get composite trading signals with optional filters."""
    conn = get_db()
    try:
        query = "SELECT ticker, composite_score, signal_direction, market_regime FROM composite_signals WHERE 1=1"
        params = []
        
        if ticker:
            query += " AND ticker = ?"
            params.append(ticker.upper())
        if min_score is not None:
            query += " AND ABS(composite_score) >= ?"
            params.append(min_score)
        if direction == 'long':
            query += " AND signal_direction = 1"
        elif direction == 'short':
            query += " AND signal_direction = -1"
        
        query += " ORDER BY composite_score DESC"
        results = conn.execute(query, params).fetchall()
        
        signals = []
        for r in results:
            d = 'LONG' if r[2] == 1 else ('SHORT' if r[2] == -1 else 'NEUTRAL')
            signals.append({
                'ticker': r[0],
                'composite_score': round(r[1], 4),
                'direction': d,
                'regime': r[3]
            })
        
        return {
            'count': len(signals),
            'signals': signals,
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        conn.close()


# ═══════════════════════════════════
# FINBERT ENS SCORES
# ═══════════════════════════════════
@app.get("/ens-scores")
def get_ens_scores():
    """Get FinBERT GPU earnings narrative scores."""
    conn = get_db()
    try:
        results = conn.execute("""
            SELECT ticker, AVG(tcs_score) as avg_ens, COUNT(*) as count
            FROM ens_scores WHERE id LIKE 'finbert_%'
            GROUP BY ticker ORDER BY avg_ens DESC
        """).fetchall()
        
        scores = []
        for r in results:
            sentiment = 'bullish' if r[1] > 0.1 else ('bearish' if r[1] < -0.1 else 'neutral')
            scores.append({
                'ticker': r[0],
                'ens_score': round(r[1], 4),
                'transcripts': r[2],
                'sentiment': sentiment
            })
        
        return {
            'count': len(scores),
            'scores': scores,
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        conn.close()


# ═══════════════════════════════════
# ALPACA PORTFOLIO
# ═══════════════════════════════════
@app.get("/portfolio")
def get_portfolio():
    """Get live Alpaca portfolio data."""
    try:
        with open('alpaca_data.json') as f:
            data = json.load(f)
        
        positions = []
        for p in data.get('positions', []):
            positions.append({
                'symbol': p.get('symbol'),
                'quantity': p.get('qty'),
                'entry_price': p.get('avg_entry'),
                'current_price': p.get('current_price'),
                'market_value': p.get('market_value'),
                'unrealized_pl': p.get('unrealized_pl'),
                'unrealized_pl_pct': p.get('unrealized_pl_pct'),
                'change_today': p.get('change_today')
            })
        
        return {
            'equity': data.get('equity'),
            'cash': data.get('cash'),
            'buying_power': data.get('buying_power'),
            'pnl_today': data.get('pnl_today'),
            'positions_count': len(positions),
            'positions': positions,
            'timestamp': data.get('timestamp')
        }
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Alpaca data not available. Run: python live/alpaca_fetcher.py")


# ═══════════════════════════════════
# RIV — REGULATORY IMPACTS
# ═══════════════════════════════════
@app.get("/regulatory")
def get_regulatory():
    """Get RIV scores from Federal Register."""
    conn = get_db()
    try:
        results = conn.execute("""
            SELECT sector, COUNT(*) as count, AVG(impact_direction) as avg_direction
            FROM riv_scores GROUP BY sector ORDER BY count DESC
        """).fetchall()
        
        sectors = []
        for r in results:
            direction = 'tightening' if r[2] < 0 else ('easing' if r[2] > 0 else 'neutral')
            sectors.append({
                'sector': r[0],
                'documents': r[1],
                'direction': direction
            })
        
        return {
            'total_documents': sum(s['documents'] for s in sectors),
            'sectors': sectors,
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        conn.close()


# ═══════════════════════════════════
# CMI — COMPETITIVE INTELLIGENCE
# ═══════════════════════════════════
@app.get("/competitive")
def get_competitive():
    """Get CMI scores from career pages."""
    conn = get_db()
    try:
        results = conn.execute("""
            SELECT ticker, cmi_final FROM cmi_scores ORDER BY cmi_final DESC
        """).fetchall()
        
        companies = []
        for r in results:
            signal = 'expansion' if r[1] > 0.1 else ('contraction' if r[1] < -0.1 else 'neutral')
            companies.append({
                'ticker': r[0],
                'cmi_score': round(r[1], 4),
                'signal': signal
            })
        
        return {
            'count': len(companies),
            'companies': companies,
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        conn.close()


# ═══════════════════════════════════
# MARKET DATA — PRICES
# ═══════════════════════════════════
@app.get("/prices/{ticker}")
def get_prices(ticker: str, days: int = 60):
    """Get OHLCV price data for a ticker."""
    conn = get_db()
    try:
        results = conn.execute("""
            SELECT trade_date, open_price, high_price, low_price, close_price, volume
            FROM price_data WHERE ticker = ? 
            ORDER BY trade_date DESC LIMIT ?
        """, [ticker.upper(), days]).fetchall()
        
        prices = []
        for r in reversed(results):
            prices.append({
                'date': str(r[0]),
                'open': round(r[1], 2) if r[1] else None,
                'high': round(r[2], 2) if r[2] else None,
                'low': round(r[3], 2) if r[3] else None,
                'close': round(r[4], 2) if r[4] else None,
                'volume': r[5]
            })
        
        return {
            'ticker': ticker.upper(),
            'count': len(prices),
            'prices': prices
        }
    finally:
        conn.close()


# ═══════════════════════════════════
# DASHBOARD SUMMARY — All in one call
# ═══════════════════════════════════
@app.get("/dashboard")
def dashboard_summary():
    """Get all dashboard data in one API call."""
    conn = get_db()
    try:
        # Signals
        sigs = conn.execute("""
            SELECT ticker, composite_score, signal_direction FROM composite_signals ORDER BY composite_score DESC
        """).fetchall()
        
        signals = []
        for r in sigs:
            signals.append({
                'ticker': r[0],
                'score': round(r[1], 4),
                'direction': 'LONG' if r[2] == 1 else ('SHORT' if r[2] == -1 else 'NEUTRAL')
            })
        
        # ENS
        ens = conn.execute("""
            SELECT ticker, AVG(tcs_score) FROM ens_scores WHERE id LIKE 'finbert_%' GROUP BY ticker ORDER BY AVG(tcs_score) DESC
        """).fetchall()
        
        # Database stats
        prices = conn.execute("SELECT COUNT(*) FROM price_data").fetchone()[0]
        
        return {
            'signals': {'count': len(signals), 'data': signals},
            'ens_scores': [{'ticker': r[0], 'score': round(r[1], 4)} for r in ens[:10]],
            'price_rows': prices,
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        conn.close()


# ═══════════════════════════════════
# RUN
# ═══════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    print("="*50)
    print("ALETHEIA API SERVER")
    print("="*50)
    print("Endpoints:")
    print("  GET /              — Health check")
    print("  GET /signals       — Composite trading signals")
    print("  GET /ens-scores    — FinBERT GPU scores")
    print("  GET /portfolio     — Live Alpaca portfolio")
    print("  GET /regulatory    — Federal Register RIV")
    print("  GET /competitive   — Career page CMI")
    print("  GET /prices/AAPL   — OHLCV price data")
    print("  GET /dashboard     — All data in one call")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)