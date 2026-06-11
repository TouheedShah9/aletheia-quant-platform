"""
Download real 8-K filing text from SEC EDGAR
Uses SEC Company Facts API (reliable, no CIK issues)
"""
import requests
import duckdb
import time
import re
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'ProjectAletheia research@projectaletheia.dev'}

# CIK numbers (10-digit zero-padded for SEC)
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
    # Get submissions (list of filings)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"{ticker}: HTTP {resp.status_code}")
            continue
        
        data = resp.json()
        filings = data.get('filings', {}).get('recent', {})
        
        forms = filings.get('form', [])
        dates = filings.get('filingDate', [])
        accessions = filings.get('accessionNumber', [])
        primary_docs = filings.get('primaryDocument', [])
        
        print(f"\n{ticker}: {len(forms)} total filings")
        
        # Filter for 8-K filings
        eight_k_count = 0
        for i in range(len(forms)):
            if forms[i] == '8-K' and eight_k_count < 3:  # Get 3 most recent
                filing_date = dates[i]
                accession = accessions[i]
                primary_doc = primary_docs[i]
                
                # Build URL to filing text
                acc_clean = accession.replace('-', '')
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_clean}/{primary_doc}"
                
                print(f"  {filing_date}: {primary_doc[:60]}...")
                
                try:
                    resp2 = requests.get(filing_url, headers=HEADERS, timeout=30)
                    
                    # Parse HTML
                    soup = BeautifulSoup(resp2.text, 'html.parser')
                    text = soup.get_text(separator=' ')
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    # Take first 3000 words
                    words = text.split()[:3000]
                    clean_text = ' '.join(words)
                    word_count = len(words)
                    
                    if word_count > 100:
                        # Store in database
                        conn.execute("""
                            INSERT OR REPLACE INTO transcripts_metadata
                            (id, ticker, company_name, market, event_date, ingestion_timestamp, source, word_count, has_qa_section, checksum, full_text)
                            VALUES (?, ?, ?, 'USA', ?, CURRENT_TIMESTAMP, 'SEC_8K_REAL', ?, TRUE, ?, ?)
                        """, [f"real_{ticker}_{filing_date}", ticker, ticker, filing_date,
                              word_count, f"real_{ticker}_{filing_date}", clean_text])
                        
                        count += 1
                        eight_k_count += 1
                        print(f"    -> {word_count} words stored")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"    Error: {e}")
        
        time.sleep(0.5)
        
    except Exception as e:
        print(f"{ticker}: {e}")

conn.close()
print(f"\nReal 8-K texts downloaded: {count}")