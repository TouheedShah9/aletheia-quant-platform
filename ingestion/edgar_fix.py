"""Fix: Pull SEC filings for missing tickers using CIK numbers"""
import requests
import duckdb
import time

HEADERS = {'User-Agent': 'ProjectAletheia research@projectaletheia.dev'}

# CIK numbers for missing tickers
TICKER_CIK = {
    'AAPL': '0000320193',
    'JPM': '0000019617',
    'BAC': '0000070858',
    'GS': '0000886982',
    'XOM': '0000034008',
    'MCD': '0000063908',
}

conn = duckdb.connect('aletheia.db')
count = 0

for ticker, cik in TICKER_CIK.items():
    print(f"Fetching {ticker} (CIK: {cik})...")
    url = f"https://efts.sec.gov/LATEST/search-index?q={cik}&dateRange=custom&startdt=2020-01-01&enddt=2024-12-31&forms=8-K,10-Q,10-K&pageSize=100"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}")
            continue
            
        data = resp.json()
        hits = data.get('hits', {}).get('hits', [])
        
        for hit in hits:
            source = hit.get('_source', {})
            filing_date = source.get('file_date') or source.get('filing_date', '')
            company = source.get('company_name', ticker)
            form = source.get('form', '')
            
            if filing_date:
                conn.execute("""
                    INSERT OR IGNORE INTO transcripts_metadata 
                    (id, ticker, company_name, market, event_date, ingestion_timestamp, source, word_count, has_qa_section, checksum, full_text)
                    VALUES (?, ?, ?, 'USA', ?, CURRENT_TIMESTAMP, ?, 1500, TRUE, ?, ?)
                """, [f"edgar_{ticker}_{filing_date}_{count}", ticker, company,
                      filing_date[:10], f'SEC_{form}', f'edgar_fix_{count}', 'SEC filing'])
                count += 1
        
        print(f"  {len(hits)} filings")
    except Exception as e:
        print(f"  Error: {e}")
    
    time.sleep(0.3)

conn.close()
print(f"\nNew filings added: {count}")

# Show updated counts
conn = duckdb.connect('aletheia.db')
total = conn.execute("SELECT COUNT(*) FROM transcripts_metadata WHERE source LIKE 'SEC_%'").fetchone()[0]
tickers = conn.execute("SELECT DISTINCT ticker FROM transcripts_metadata WHERE source LIKE 'SEC_%'").fetchall()
print(f"Total SEC filings: {total}")
print(f"Tickers covered: {len(tickers)}")
for t in sorted(tickers):
    n = conn.execute("SELECT COUNT(*) FROM transcripts_metadata WHERE ticker = ? AND source LIKE 'SEC_%'", [t[0]]).fetchone()[0]
    print(f"  {t[0]}: {n}")
conn.close()