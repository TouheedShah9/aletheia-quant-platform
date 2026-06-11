"""Batch ENS scoring using actual transcript text"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import duckdb
from loguru import logger
from models.ens.ens_composer import ENSComposer

composer = ENSComposer()
conn = duckdb.connect("aletheia.db")

transcripts = conn.execute(
    "SELECT id, ticker, COALESCE(full_text, '') FROM transcripts_metadata"
).fetchall()

logger.info(f"Computing ENS for {len(transcripts)} transcripts...")

# Clear old scores
conn.execute("DELETE FROM ens_scores")

count = 0
for tid, ticker, text in transcripts:
    if not text or len(text) < 100:
        continue
    
    scores = composer.compute(ticker, text)
    
    conn.execute(
        """INSERT INTO ens_scores
        (id, transcript_id, ticker, ens_final, tcs_score, fgc_score, tad_score, lhi_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            f"ens_{tid}", tid, ticker,
            scores["ens_final"], scores["tcs_score"],
            scores["fgc_score"], scores["tad_score"],
            scores["lhi_score"]
        ]
    )
    count += 1
    if count % 15 == 0:
        logger.info(f"  {count}/{len(transcripts)} done")

conn.close()
logger.info(f"Done: {count} ENS scores computed")