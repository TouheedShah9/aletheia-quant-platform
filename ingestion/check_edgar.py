import duckdb

conn = duckdb.connect('aletheia.db')

total = conn.execute('SELECT COUNT(*) FROM transcripts_metadata').fetchone()[0]
real = conn.execute("SELECT COUNT(*) FROM transcripts_metadata WHERE source LIKE 'SEC_%'").fetchone()[0]
tickers = conn.execute("SELECT DISTINCT ticker FROM transcripts_metadata WHERE source LIKE 'SEC_%'").fetchall()

print(f'Total transcripts: {total}')
print(f'Real SEC filings: {real}')
print(f'Tickers with SEC data: {len(tickers)}')
for t in tickers:
    n = conn.execute("SELECT COUNT(*) FROM transcripts_metadata WHERE ticker = ? AND source LIKE 'SEC_%'", [t[0]]).fetchone()[0]
    print(f'  {t[0]}: {n} filings')

conn.close()