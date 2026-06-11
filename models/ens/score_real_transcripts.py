"""Score real EDGAR transcripts with ENS pipeline"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import duckdb
from models.ens.section_parser import SectionParser
from models.ens.preprocessor import ENSPreprocessor
from models.ens.ens_scorers import ToneConfidenceScorer

conn = duckdb.connect('aletheia.db')

transcripts = conn.execute("""
    SELECT id, ticker, event_date, full_text
    FROM transcripts_metadata
    WHERE source = 'SEC_8K_REAL' AND full_text IS NOT NULL
""").fetchall()

print(f"Real transcripts: {len(transcripts)}")

preprocessor = ENSPreprocessor()

for tid, ticker, date, text in transcripts:
    parser = SectionParser(ticker)
    sections = parser.parse(text)
    cleaned = preprocessor.clean(text)
    tcs = ToneConfidenceScorer.score(cleaned)
    
    conn.execute("""
        INSERT INTO ens_scores (id, transcript_id, ticker, ens_final, tcs_score, fgc_score, tad_score, lhi_score)
        VALUES (?, ?, ?, ?, ?, 0, 0, 0)
    """, [f"real_{tid}", tid, ticker, round(tcs, 4), round(tcs, 4)])
    
    print(f"  {ticker:5s} {date}: TCS={tcs:+.3f} | {len(cleaned.split())} words")

total = conn.execute("SELECT COUNT(*) FROM ens_scores WHERE id LIKE 'real_%'").fetchone()[0]
conn.close()
print(f"\nReal ENS scores: {total}")