import duckdb
import json

conn = duckdb.connect('aletheia.db')

with open('finbert_real_scores.json') as f:
    scores = json.load(f)

for s in scores:
    sid = s['id']
    ticker = s['ticker']
    ens = s['ens_score']
    conn.execute(
        "INSERT INTO ens_scores (id, transcript_id, ticker, ens_final, tcs_score, fgc_score, tad_score, lhi_score) VALUES (?, ?, ?, ?, ?, 0, 0, 0)",
        [f'fb_{sid}', sid, ticker, ens, ens]
    )

count = conn.execute("SELECT COUNT(*) FROM ens_scores WHERE id LIKE 'fb_%'").fetchone()[0]
print(f'Imported {count} real FinBERT scores')

# Show them
rows = conn.execute("SELECT ticker, ens_final FROM ens_scores WHERE id LIKE 'fb_%'").fetchall()
for r in rows:
    print(f'  {r[0]:5s} = {r[1]:+.4f}')

conn.close()