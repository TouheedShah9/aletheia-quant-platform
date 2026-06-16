"""Rebuild ALL composite signals with real ENS + real RIV + real CMI"""
import duckdb

conn = duckdb.connect('aletheia.db')
conn.execute('DELETE FROM composite_signals')

w = {'ens': 0.5, 'riv': 0.25, 'cmi': 0.25}

# Real FinBERT GPU scores — average per ticker
ens = conn.execute("SELECT ticker, AVG(tcs_score) FROM ens_scores WHERE id LIKE 'finbert_%' GROUP BY ticker").fetchall()

# Real CMI scores
cmi = {r[0]: r[1] for r in conn.execute('SELECT ticker, cmi_final FROM cmi_scores').fetchall()}

# Real RIV average impact
riv_avg = conn.execute('SELECT AVG(impact_direction * impact_magnitude) FROM riv_scores').fetchone()[0] or 0

print(f"Signal Fusion: ENS=0.5, RIV=0.25, CMI=0.25")
print(f"RIV Impact: {riv_avg:+.4f}")
print(f"Thresholds: LONG>0.05, SHORT<-0.05\n")

long_count = 0
short_count = 0
neutral_count = 0

for ticker, e in ens:
    composite = w['ens'] * e + w['riv'] * riv_avg + w['cmi'] * cmi.get(ticker, 0)
    
    # Stricter thresholds for proper long-short
    if composite > 0.05:
        direction = 1
        long_count += 1
    elif composite < -0.05:
        direction = -1
        short_count += 1
    else:
        direction = 0
        neutral_count += 1
    
    conn.execute(
        "INSERT INTO composite_signals (id, ticker, signal_date, market_regime, composite_score, signal_direction) VALUES (?, ?, '2024-12-31', 'risk_on', ?, ?)",
        [f'c_{ticker}', ticker, round(composite, 4), direction]
    )
    
    side = 'LONG' if direction == 1 else ('SHORT' if direction == -1 else 'NEUTRAL')
    emoji = '🟢' if direction == 1 else ('🔴' if direction == -1 else '⚪')
    print(f"  {emoji} {ticker:5s} = {composite:+.4f} → {side}")

print(f"\n{'='*50}")
print(f"Total: {long_count + short_count + neutral_count} signals")
print(f"  🟢 LONG: {long_count}")
print(f"  🔴 SHORT: {short_count}")
print(f"  ⚪ NEUTRAL: {neutral_count}")
print(f"{'='*50}")

conn.close()