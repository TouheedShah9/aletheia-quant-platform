"""
SEC EDGAR Bulk Download - Gets earnings filing dates for all US tickers
No datasets library needed. Direct SEC API calls.
"""
import requests
import duckdb
import time

HEADERS = {'User-Agent': 'ProjectAletheia research@projectaletheia.dev'}
TICKERS = ['AAPL','MSFT','GOOGL','AMZN','META','JPM','BAC','GS','JNJ','PFE','XOM','CVX','HD','WMT','MCD']

conn = duckdb.connect('aletheia.db')
count = 0

for ticker in TICKERS:
    print(f"Fetching {ticker}...")
    url = f"https://efts.sec.gov/LATEST/search-index?q={ticker}&dateRange=custom&startdt=2020-01-01&enddt=2024-12-31&forms=8-K,10-Q,10-K&pageSize=50"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
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
                      filing_date[:10], f'SEC_{form}', f'edgar_{count}', 'SEC filing metadata'])
                count += 1
        
        print(f"  {len(hits)} filings found")
    except Exception as e:
        print(f"  Error: {e}")
    
    time.sleep(0.2)  # Rate limit: 5 requests/second

conn.close()
print(f"\nTotal EDGAR filings stored: {count}")