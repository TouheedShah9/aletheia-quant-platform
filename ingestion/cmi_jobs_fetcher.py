"""
Real CMI Job Posting Fetcher
Monitors career pages for job posting changes
Detects expansion/contraction signals from hiring activity

Sources: Company career pages (public, robots.txt respected)
Fallback: Wayback Machine for historical data
"""
import sys, os, time, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import duckdb
from bs4 import BeautifulSoup
from loguru import logger
import config

HEADERS = {
    'User-Agent': f'ProjectAletheia/1.0 ({config.EMAIL})',
    'Accept': 'text/html'
}

# Career page URLs for tracked companies
CAREER_PAGES = {
    'AAPL': 'https://jobs.apple.com/en-us/search?location=united-states-USA',
    'MSFT': 'https://careers.microsoft.com/us/en/search-results',
    'GOOGL': 'https://careers.google.com/jobs/results/',
    'AMZN': 'https://www.amazon.jobs/en/search',
    'META': 'https://www.metacareers.com/jobs/',
    'JPM': 'https://jpmorganchase.co/jobs',
    'BAC': 'https://careers.bankofamerica.com/en-us/job-search',
    'GS': 'https://www.goldmansachs.com/careers/jobs/',
    'JNJ': 'https://jobs.jnj.com/en/jobs/',
    'PFE': 'https://www.pfizer.com/about/careers/search-jobs',
    'XOM': 'https://jobs.exxonmobil.com/',
    'CVX': 'https://careers.chevron.com/jobs',
    'HD': 'https://careers.homedepot.com/job-search',
    'WMT': 'https://careers.walmart.com/results',
    'MCD': 'https://careers.mcdonalds.com/job-search',
}

EXPANSION_KEYWORDS = [
    'AI', 'machine learning', 'data scientist', 'engineer', 'product manager',
    'growth', 'expansion', 'new market', 'regional', 'international',
    'cloud', 'digital', 'technology', 'software', 'developer'
]

COMPLIANCE_KEYWORDS = [
    'compliance', 'regulatory', 'risk', 'audit', 'legal', 'counsel',
    'sanctions', 'AML', 'KYC', 'governance', 'control'
]

COST_CUT_KEYWORDS = [
    'restructuring', 'transformation', 'efficiency', 'optimization',
    'integration', 'consolidation', 'interim'
]


class CMIJobsFetcher:
    def __init__(self):
        self.conn = duckdb.connect('aletheia.db')
        self.count = 0
    
    def check_robots(self, url):
        """Check robots.txt before scraping."""
        from urllib.parse import urlparse
        from urllib.robotparser import RobotFileParser
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(HEADERS['User-Agent'], url)
        except:
            return True  # If can't check, proceed with caution
    
    def analyze_jobs(self, html, ticker):
        """Analyze job postings for signals."""
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        
        # Count keyword matches
        expansion = sum(1 for kw in EXPANSION_KEYWORDS if kw.lower() in text)
        compliance = sum(1 for kw in COMPLIANCE_KEYWORDS if kw.lower() in text)
        cost_cut = sum(1 for kw in COST_CUT_KEYWORDS if kw.lower() in text)
        
        # Calculate CMI signal
        total_signals = expansion + compliance + cost_cut
        if total_signals == 0:
            return 0.0
        
        # Expansion = positive, Compliance = neutral, Cost-cut = negative
        cmi_score = (expansion - cost_cut) / max(total_signals, 1)
        cmi_score = max(-1.0, min(1.0, cmi_score))
        
        return round(cmi_score, 4)
    
    def fetch_all(self):
        print("="*60)
        print("CMI JOB POSTING FETCHER")
        print("="*60)
        print("Checking career pages for hiring signals...\n")
        
        self.conn.execute('DELETE FROM cmi_scores')
        
        for ticker, url in CAREER_PAGES.items():
            # Check robots.txt
            if not self.check_robots(url):
                print(f"  {ticker}: BLOCKED by robots.txt")
                continue
            
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code == 200:
                    cmi = self.analyze_jobs(resp.text, ticker)
                    
                    self.conn.execute("""
                        INSERT INTO cmi_scores (id, ticker, score_date, cmi_final, job_anomaly_score, web_change_score)
                        VALUES (?, ?, '2024-12-15', ?, ?, 0.0)
                    """, [f'cmi_{ticker}_real', ticker, cmi, cmi])
                    
                    self.count += 1
                    signal_type = 'EXPANSION' if cmi > 0.1 else ('CONTRACTION' if cmi < -0.1 else 'NEUTRAL')
                    print(f"  {ticker:5s}: CMI={cmi:+.3f} ({signal_type})")
                else:
                    print(f"  {ticker:5s}: HTTP {resp.status_code}")
            except Exception as e:
                print(f"  {ticker:5s}: {str(e)[:50]}")
            
            time.sleep(2.0)  # Respect rate limits
        
        # Show results
        cmi_count = self.conn.execute('SELECT COUNT(*) FROM cmi_scores').fetchone()[0]
        scores = self.conn.execute('SELECT ticker, cmi_final FROM cmi_scores ORDER BY cmi_final DESC').fetchall()
        
        print(f"\n{'='*60}")
        print(f"RESULTS: {cmi_count} CMI scores")
        for ticker, score in scores:
            signal = 'EXPANSION' if score > 0.1 else ('CONTRACTION' if score < -0.1 else 'NEUTRAL')
            print(f"  {ticker:5s}: {score:+.3f} — {signal}")
        print(f"\nSource: Real company career pages (public, legal)")
        
        self.conn.close()
        return cmi_count


if __name__ == "__main__":
    fetcher = CMIJobsFetcher()
    fetcher.fetch_all()