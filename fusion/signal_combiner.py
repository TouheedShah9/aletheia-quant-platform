"""Signal Combiner - ENS + RIV + CMI into composite"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import duckdb
import config

def combine():
    conn = duckdb.connect('aletheia.db')
    conn.execute('DELETE FROM composite_signals')
    w = config.REGIME_WEIGHTS['risk_on']
    ens = {r[0]: r[1] for r in conn.execute(
        "SELECT ticker, AVG(ens_final) FROM ens_scores WHERE id LIKE 'earn_%' GROUP BY ticker"
    ).fetchall()}
    cmi = {r[0]: r[1] for r in conn.execute(
        'SELECT ticker, cmi_final FROM cmi_scores'
    ).fetchall()}
    
    for ticker, e in ens.items():
        composite = w['ens']*e + w['riv']*0.02 + w['cmi']*cmi.get(ticker, 0)
        direction = 1 if composite > 0.02 else (-1 if composite < -0.02 else 0)
        conn.execute(
            "INSERT INTO composite_signals (id, ticker, signal_date, market_regime, composite_score, signal_direction) VALUES (?, ?, '2024-12-31', 'risk_on', ?, ?)",
            [f'c_{ticker}', ticker, round(composite, 4), direction]
        )
    
    results = conn.execute("SELECT ticker, composite_score, signal_direction FROM composite_signals ORDER BY composite_score DESC").fetchall()
    print("COMPOSITE SIGNALS:")
    for r in results:
        side = 'LONG' if r[2]==1 else ('SHORT' if r[2]==-1 else 'NEUTRAL')
        print(f"  {r[0]:5s} = {r[1]:+.4f} -> {side}")
    
    conn.close()

if __name__ == "__main__":
    combine()