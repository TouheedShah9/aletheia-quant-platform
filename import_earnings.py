import duckdb
import json

conn = duckdb.connect('aletheia.db')

# Load FinBERT scores
with open('earnings_finbert_scores.json') as f:
    scores = json.load(f)

# Import
for i, s in enumerate(scores):
    conn.execute(
        "INSERT INTO ens_scores (id, transcript_id, ticker, ens_final, tcs_score, fgc_score, tad_score, lhi_score) VALUES (?, ?, ?, ?, ?, 0, 0, 0)",
        [f'earn_{i}', f'earn_{i}', s['ticker'], s['ens'], s['ens']]
    )

print(f'Imported {len(scores)} earnings call scores')

# Rebuild composites
conn.execute('DELETE FROM composite_signals')
w = {'ens': 0.5, 'riv': 0.25, 'cmi': 0.25}

ens = conn.execute("SELECT ticker, AVG(ens_final) FROM ens_scores WHERE id LIKE 'earn_%' GROUP BY ticker").fetchall()
cmi = {c[0]: c[1] for c in conn.execute('SELECT ticker, cmi_final FROM cmi_scores').fetchall()}

print('\nNEW COMPOSITE SIGNALS:')
for ticker, e in ens:
    composite = w['ens'] * e + w['riv'] * 0.02 + w['cmi'] * cmi.get(ticker, 0)
    direction = 1 if composite > 0.02 else (-1 if composite < -0.02 else 0)
    side = 'LONG' if direction == 1 else ('SHORT' if direction == -1 else 'NEUTRAL')
    
    conn.execute(
        "INSERT INTO composite_signals (id, ticker, signal_date, market_regime, composite_score, signal_direction) VALUES (?, ?, '2024-12-31', 'risk_on', ?, ?)",
        [f'e_{ticker}', ticker, round(composite, 4), direction]
    )
    
    emoji = '🟢' if direction == 1 else ('🔴' if direction == -1 else '⚪')
    print(f'  {emoji} {ticker:5s} = {composite:+.4f} -> {side}')

conn.close()
print('\nDone. Portfolio ready.')