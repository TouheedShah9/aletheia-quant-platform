import duckdb

conn = duckdb.connect('aletheia.db')
conn.execute('DELETE FROM composite_signals')

w = {'ens': 0.5, 'riv': 0.25, 'cmi': 0.25}

ens = conn.execute("SELECT ticker, AVG(ens_final) FROM ens_scores WHERE id LIKE 'fb_%' GROUP BY ticker").fetchall()
cmi = {c[0]: c[1] for c in conn.execute('SELECT ticker, cmi_final FROM cmi_scores').fetchall()}

for ticker, ens_score in ens:
    composite = w['ens'] * ens_score + w['riv'] * 0.02 + w['cmi'] * cmi.get(ticker, 0)
    direction = 1 if composite > 0.02 else (-1 if composite < -0.02 else 0)
    conn.execute(
        "INSERT INTO composite_signals (id, ticker, signal_date, market_regime, composite_score, signal_direction) VALUES (?, ?, '2024-12-31', 'risk_on', ?, ?)",
        [f'c_{ticker}', ticker, round(composite, 4), direction]
    )
    side = 'LONG' if direction == 1 else ('SHORT' if direction == -1 else 'NEUTRAL')
    print(f'  {ticker:5s} = {composite:+.4f} -> {side}')

conn.close()
print('Composite signals rebuilt with real FinBERT scores')