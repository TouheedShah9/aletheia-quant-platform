import duckdb, json

conn = duckdb.connect('aletheia.db')

with open('finbert_earnings_scores.json') as f:
    scores = json.load(f)

for s in scores:
    conn.execute("""
        INSERT OR REPLACE INTO ens_scores (id, transcript_id, ticker, ens_final, tcs_score, fgc_score, tad_score, lhi_score)
        VALUES (?, ?, ?, ?, ?, 0, 0, 0)
    """, [f'finbert_{s["id"]}', s['id'], s['ticker'], s['ens_score'], s['ens_score']])

count = conn.execute("SELECT COUNT(*) FROM ens_scores WHERE id LIKE 'finbert_%'").fetchone()[0]
print(f'Imported {count} real FinBERT GPU scores')

# Show all — both bullish and bearish
all_scores = conn.execute("SELECT DISTINCT ticker, tcs_score FROM ens_scores WHERE id LIKE 'finbert_%' ORDER BY tcs_score").fetchall()
for ticker, score in all_scores:
    emoji = '🟢' if score > 0.1 else ('🔴' if score < -0.1 else '⚪')
    print(f"  {emoji} {ticker:5s}: {score:+.4f}")

conn.close()