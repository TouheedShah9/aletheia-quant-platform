"""
Download 10-K MD&A exhibits from SEC EDGAR
These contain management commentary similar to earnings calls
"""
import requests
import duckdb
import time
import re
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'ProjectAletheia research@projectaletheia.dev'}

TICKERS = {
    'AAPL': '0000320193',
    'MSFT': '0000789019',
    'GOOGL': '0001652044',
    'AMZN': '0001018724',
    'META': '0001326801',
}

conn = duckdb.connect('aletheia.db')
count = 0

for ticker, cik in TICKERS.items():
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            continue
        
        data = resp.json()
        filings = data.get('filings', {}).get('recent', {})
        forms = filings.get('form', [])
        dates = filings.get('filingDate', [])
        accessions = filings.get('accessionNumber', [])
        primary_docs = filings.get('primaryDocument', [])
        
        ten_k_count = 0
        for i in range(len(forms)):
            if forms[i] == '10-K' and ten_k_count < 2:
                filing_date = dates[i]
                accession = accessions[i]
                primary_doc = primary_docs[i]
                
                acc_clean = accession.replace('-', '')
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_clean}/{primary_doc}"
                
                try:
                    resp2 = requests.get(filing_url, headers=HEADERS, timeout=60)
                    soup = BeautifulSoup(resp2.text, 'html.parser')
                    text = soup.get_text(separator=' ')
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    # Find MD&A section (Item 7)
                    mda_start = text.lower().find('item 7')
                    mda_end = text.lower().find('item 8', mda_start + 100) if mda_start > 0 else -1
                    
                    if mda_start > 0:
                        mda_text = text[mda_start:mda_end] if mda_end > 0 else text[mda_start:mda_start+5000]
                    else:
                        mda_text = text[:3000]
                    
                    words = mda_text.split()[:2000]
                    clean_text = ' '.join(words)
                    word_count = len(words)
                    
                    if word_count > 200:
                        conn.execute("""
                            INSERT OR REPLACE INTO transcripts_metadata
                            (id, ticker, company_name, market, event_date, ingestion_timestamp, source, word_count, has_qa_section, checksum, full_text)
                            VALUES (?, ?, ?, 'USA', ?, CURRENT_TIMESTAMP, 'SEC_10K_REAL', ?, TRUE, ?, ?)
                        """, [f"10k_{ticker}_{filing_date}", ticker, ticker, filing_date,
                              word_count, f"10k_{ticker}", clean_text])
                        count += 1
                        ten_k_count += 1
                        print(f"  {ticker} {filing_date}: {word_count} words (MD&A)")
                    
                    time.sleep(0.5)
                except Exception as e:
                    print(f"  {ticker}: {e}")
        
        time.sleep(0.5)
    except Exception as e:
        print(f"{ticker}: {e}")

conn.close()
print(f"\n10-K texts downloaded: {count}")