import duckdb

conn = duckdb.connect('aletheia.db')
conn.execute("DELETE FROM composite_signals")

ens = {r[0]: r[1] for r in conn.execute(
    "SELECT ticker, AVG(ens_final) FROM ens_scores GROUP BY ticker").fetchall()}
cmi = {r[0]: r[1] for r in conn.execute(
    "SELECT ticker, cmi_final FROM cmi_scores").fetchall()}
riv_avg = conn.execute(
    "SELECT AVG(impact_direction*impact_magnitude) FROM riv_scores").fetchone()[0] or 0

w = {'ens': 0.5, 'riv': 0.25, 'cmi': 0.25}

for ticker in ens:
    composite = w['ens'] * ens[ticker] + w['riv'] * riv_avg + w['cmi'] * cmi.get(ticker, 0)
    direction = 1 if composite > 0.02 else (-1 if composite < -0.02 else 0)
    conn.execute(
        "INSERT INTO composite_signals (id, ticker, signal_date, market_regime, composite_score, signal_direction) VALUES (?, ?, '2024-06-15', 'risk_on', ?, ?)",
        [f"comp_{ticker}", ticker, round(composite, 4), direction]
    )

results = conn.execute(
    "SELECT ticker, composite_score, signal_direction FROM composite_signals ORDER BY composite_score DESC"
).fetchall()

print("COMPOSITE SIGNALS (Real FinBERT + BART):")
for r in results:
    side = "LONG" if r[2] == 1 else ("SHORT" if r[2] == -1 else "NEUTRAL")
    print(f"  {r[0]:5s} = {r[1]:+.4f} -> {side}")

conn.close()