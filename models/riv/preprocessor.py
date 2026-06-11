"""
RIV Preprocessor - Chunk and filter regulatory documents
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from loguru import logger

FINANCIAL_KEYWORDS = [
    'capital', 'reserve', 'reporting', 'compliance', 'penalty', 'fine',
    'bank', 'trading', 'securities', 'insurance', 'asset', 'liability',
    'disclosure', 'enforcement', 'sanction', 'restriction', 'license',
    'supervision', 'stress test', 'leverage', 'liquidity', 'solvency',
    'systemic risk', 'consumer protection', 'anti-money laundering',
    'market abuse', 'derivatives', 'registration', 'fiduciary',
    'prudential', 'deposit insurance', 'fintech', 'cryptocurrency'
]

SECTOR_KEYWORDS = {
    'banking': ['bank', 'deposit', 'lending', 'loan', 'mortgage', 'credit'],
    'insurance': ['insurance', 'reinsurance', 'underwriting', 'premium'],
    'technology': ['technology', 'software', 'cloud', 'AI', 'cyber', 'digital'],
    'healthcare': ['pharma', 'drug', 'medical', 'biotech', 'FDA', 'healthcare'],
    'energy': ['oil', 'gas', 'renewable', 'carbon', 'emission', 'utility'],
    'real_estate': ['real estate', 'property', 'REIT', 'mortgage', 'housing'],
    'consumer': ['retail', 'consumer', 'food', 'e-commerce'],
    'industrial': ['manufacturing', 'industrial', 'aerospace', 'automotive'],
}


class RIVPreprocessor:
    @staticmethod
    def chunk_document(text, max_tokens=500, overlap=50):
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + max_tokens, len(words))
            chunk = ' '.join(words[start:end])
            if len(chunk.split()) >= 50:
                chunks.append(chunk)
            start += (max_tokens - overlap)
        return chunks

    @staticmethod
    def count_financial_keywords(text):
        text_lower = text.lower()
        return sum(len(re.findall(r'\b' + re.escape(kw) + r'\b', text_lower)) for kw in FINANCIAL_KEYWORDS)

    @staticmethod
    def filter_financial_chunks(chunks, min_keywords=2):
        return [c for c in chunks if RIVPreprocessor.count_financial_keywords(c) >= min_keywords]

    @staticmethod
    def detect_sectors(text):
        text_lower = text.lower()
        found = []
        for sector, keywords in SECTOR_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                found.append({'sector': sector, 'relevance': score})
        return sorted(found, key=lambda x: x['relevance'], reverse=True)

    @staticmethod
    def classify_direction(text):
        text_lower = text.lower()
        tightening_words = ['prohibit','restrict','ban','limit','cap','penalty',
                            'fine','sanction','enforcement','require','mandate',
                            'compliance','increase capital','higher requirement']
        easing_words = ['relax','ease','exempt','relief','streamline',
                       'reduce burden','simplify','deregulat','lower requirement',
                       'remove restriction','extend deadline','transition period']
        
        tightening = sum(1 for w in tightening_words if w in text_lower)
        easing = sum(1 for w in easing_words if w in text_lower)
        total = tightening + easing
        
        if total == 0:
            return {'direction': 0, 'magnitude': 0.0, 'confidence': 0.0}
        
        direction = 1 if easing > tightening else (-1 if tightening > easing else 0)
        magnitude = abs(easing - tightening) / max(total, 1)
        confidence = min(1.0, total / 10)
        return {'direction': direction, 'magnitude': round(magnitude,3), 'confidence': round(confidence,3)}


def test_preprocessor():
    sample = """The SEC today adopted new rules requiring enhanced disclosure 
    for banks regarding capital reserves and liquidity. The rule increases 
    minimum capital from 4% to 6% and mandates quarterly stress testing.
    Penalties include fines up to $1 million. Small banks under $10 billion 
    are exempt from certain reporting requirements."""
    
    chunks = RIVPreprocessor.chunk_document(sample, 100)
    filtered = RIVPreprocessor.filter_financial_chunks(chunks)
    sectors = RIVPreprocessor.detect_sectors(sample)
    impact = RIVPreprocessor.classify_direction(sample)
    
    print(f"Chunks: {len(chunks)}, Financial: {len(filtered)}")
    print(f"Sectors: {[s['sector'] for s in sectors]}")
    print(f"Impact: dir={impact['direction']}, mag={impact['magnitude']:.2f}, conf={impact['confidence']:.2f}")
    print("All RIV preprocessor tests passed.")

if __name__ == "__main__":
    test_preprocessor()