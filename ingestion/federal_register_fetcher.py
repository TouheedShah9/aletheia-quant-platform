"""
Real Federal Register Data Fetcher
Downloads actual SEC/Federal Reserve/CFPB regulatory documents
Replaces hand-written RIV samples with REAL government data

API: federalregister.gov/api/v1 — FREE, NO KEY, LEGALLY PUBLIC
"""
import sys, os, time, json, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import duckdb
from loguru import logger
import config

HEADERS = {
    'User-Agent': f'ProjectAletheia/1.0 ({config.EMAIL})',
    'Accept': 'application/json'
}

BASE_URL = 'https://www.federalregister.gov/api/v1'
RATE_LIMIT = 0.5

AGENCIES = {
    '466': 'SEC',
    '188': 'Federal Reserve',
    '573': 'CFPB',
    '77': 'CFTC',
    '164': 'FDIC',
    '80': 'OCC',
    '497': 'Treasury',
}

SECTORS_KEYWORDS = {
    'banking': ['bank', 'capital requirement', 'deposit', 'lending', 'reserve', 'systemic risk'],
    'insurance': ['insurance', 'annuity', 'underwriting', 'actuarial'],
    'technology': ['fintech', 'cryptocurrency', 'digital asset', 'blockchain', 'AI', 'data privacy'],
    'healthcare': ['pharmaceutical', 'medical device', 'health insurance', 'FDA'],
    'energy': ['oil', 'gas', 'renewable', 'carbon', 'emission', 'pipeline'],
    'consumer': ['consumer protection', 'mortgage', 'credit card', 'student loan'],
    'industrial': ['manufacturing', 'supply chain', 'infrastructure', 'transportation'],
}


class FederalRegisterFetcher:
    def __init__(self):
        self.conn = duckdb.connect('aletheia.db')
        self.count = 0

    def fetch_documents(self, agency_slug, max_pages=2):
        all_docs = []
        for page in range(1, max_pages + 1):
            params = {
                'conditions[agency_ids][]': agency_slug,
                'per_page': 20,
                'page': page,
                'order': 'newest',
            }
            try:
                resp = requests.get(f'{BASE_URL}/articles', headers=HEADERS, params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    docs = data.get('results', [])
                    all_docs.extend(docs)
                    print(f"  {AGENCIES.get(agency_slug, agency_slug)}: page {page} — {len(docs)} docs")
                else:
                    print(f"  {AGENCIES.get(agency_slug, agency_slug)}: HTTP {resp.status_code}")
                    break
            except Exception as e:
                print(f"  {AGENCIES.get(agency_slug, agency_slug)}: {e}")
                break
            time.sleep(RATE_LIMIT)
        return all_docs

    def detect_sectors(self, text):
        text_lower = text.lower()
        found = []
        for sector, keywords in SECTORS_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                found.append((sector, score))
        return sorted(found, key=lambda x: x[1], reverse=True)

    def classify_direction(self, text):
        text_lower = text.lower()
        tightening = ['require', 'mandate', 'prohibit', 'restrict', 'ban', 'limit',
                     'penalty', 'fine', 'enforcement', 'compliance', 'must', 'shall']
        easing = ['relax', 'ease', 'exempt', 'relief', 'streamline', 'simplify',
                 'reduce burden', 'extend deadline', 'transition period']
        tight_score = sum(1 for w in tightening if w in text_lower)
        ease_score = sum(1 for w in easing if w in text_lower)
        if tight_score > ease_score: return -1
        elif ease_score > tight_score: return 1
        return 0

    def process_document(self, doc, agency_name):
        title = doc.get('title', '')
        abstract = doc.get('abstract', '')
        body = doc.get('body_html', '')
        pub_date = doc.get('publication_date', '')[:10]
        doc_id = doc.get('document_number', '')

        full_text = f"{title}. {abstract}"
        if body:
            clean_body = re.sub(r'<[^>]+>', ' ', body)
            full_text += ' ' + clean_body[:2000]

        sectors = self.detect_sectors(full_text)
        direction = self.classify_direction(full_text)

        for sector, relevance in sectors[:3]:
            magnitude = min(1.0, relevance / 10.0)
            self.conn.execute("""
                INSERT INTO riv_scores (id, document_id, jurisdiction, sector, impact_direction, impact_magnitude)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [f'fr_{doc_id}_{sector}', doc_id, 'USA', sector, direction, round(magnitude, 3)])
            self.count += 1
        return True

    def run(self):
        print("="*60)
        print("FEDERAL REGISTER DATA PIPELINE")
        print("="*60)
        print(f"Source: federalregister.gov/api/v1")
        print(f"Legal: US Government public data\n")

        self.conn.execute('DELETE FROM riv_scores')
        total_docs = 0

        for slug, name in AGENCIES.items():
            docs = self.fetch_documents(slug)
            for doc in docs:
                try:
                    self.process_document(doc, name)
                    total_docs += 1
                except:
                    pass
            time.sleep(0.5)

        riv_count = self.conn.execute('SELECT COUNT(*) FROM riv_scores').fetchone()[0]
        sectors = self.conn.execute("""
            SELECT sector, COUNT(*), AVG(impact_direction)
            FROM riv_scores GROUP BY sector ORDER BY COUNT(*) DESC
        """).fetchall()

        print(f"\n{'='*60}")
        print(f"RESULTS")
        print(f"{'='*60}")
        print(f"Documents: {total_docs} | RIV scores: {riv_count}")
        for sector, count, avg_dir in sectors:
            direction = 'TIGHTEN' if avg_dir < 0 else ('EASE' if avg_dir > 0 else 'NEUTRAL')
            print(f"  {sector:15s}: {count:3d} — {direction}")
        print(f"\nReplaces all hand-written RIV samples")
        self.conn.close()
        return riv_count


if __name__ == "__main__":
    FederalRegisterFetcher().run()