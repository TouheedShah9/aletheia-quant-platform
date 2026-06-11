"""
ENS Composer - Combines 4 dimensions into final ENS score
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import duckdb
from loguru import logger
import config
from models.ens.section_parser import SectionParser
from models.ens.preprocessor import ENSPreprocessor
from models.ens.ens_scorers import (
    ToneConfidenceScorer, ForwardGuidanceScorer,
    TopicAvoidanceScorer, LinguisticHedgingScorer
)


class ENSComposer:
    def __init__(self):
        self.weights = config.ENS_DIM
        self.section_weights = config.ENS_SEC
        self.preprocessor = ENSPreprocessor()

    def compute(self, ticker: str, text: str) -> dict:
        parser = SectionParser(ticker)
        sections = parser.parse(text)
        prepared_text = self.preprocessor.clean(
            sections['prepared_ceo'] + ' ' + sections['prepared_cfo']
        )
        qa_text = self.preprocessor.clean(sections['qa_section'])
        
        tcs_prepared = ToneConfidenceScorer.score(prepared_text)
        fgc_prepared = ForwardGuidanceScorer.score(prepared_text)
        lhi_prepared = LinguisticHedgingScorer.score(prepared_text)
        
        tcs_qa = ToneConfidenceScorer.score(qa_text) if qa_text else 0.0
        fgc_qa = ForwardGuidanceScorer.score(qa_text) if qa_text else 0.0
        tad_score = TopicAvoidanceScorer.score(sections['qa_section'], sections['qa_section']) if sections['has_qa'] else 0.0
        lhi_qa = LinguisticHedgingScorer.score(qa_text) if qa_text else 0.0
        
        ens_prepared = (
            self.weights['tcs'] * tcs_prepared +
            self.weights['fgc'] * fgc_prepared +
            self.weights['lhi'] * lhi_prepared
        ) / (self.weights['tcs'] + self.weights['fgc'] + self.weights['lhi'])
        
        ens_qa = (
            self.weights['tcs'] * tcs_qa +
            self.weights['fgc'] * fgc_qa +
            self.weights['tad'] * (1.0 - tad_score) +
            self.weights['lhi'] * lhi_qa
        ) / (self.weights['tcs'] + self.weights['fgc'] + self.weights['tad'] + self.weights['lhi'])
        
        if sections['has_qa']:
            ens_final = self.section_weights['prepared'] * ens_prepared + self.section_weights['qa'] * ens_qa
        else:
            ens_final = ens_prepared
        
        ens_final = max(-1.0, min(1.0, ens_final))
        
        return {
            'ens_final': round(ens_final, 4),
            'tcs_score': round((tcs_prepared + tcs_qa) / 2 if qa_text else tcs_prepared, 4),
            'fgc_score': round((fgc_prepared + fgc_qa) / 2 if qa_text else fgc_prepared, 4),
            'tad_score': round(tad_score, 4),
            'lhi_score': round((lhi_prepared + lhi_qa) / 2 if qa_text else lhi_prepared, 4),
        }

    def batch_compute(self, db_path="aletheia.db"):
        conn = duckdb.connect(db_path)
        transcripts = conn.execute("""
            SELECT id, ticker FROM transcripts_metadata
            WHERE id NOT IN (SELECT COALESCE(transcript_id,'') FROM ens_scores)
        """).fetchall()
        
        logger.info(f"Computing ENS for {len(transcripts)} transcripts...")
        
        for i, (tid, ticker) in enumerate(transcripts):
            text = f"Sample transcript for {ticker}"
            scores = self.compute(ticker, text)
            
            conn.execute("""
                INSERT OR REPLACE INTO ens_scores
                (id, transcript_id, ticker, ens_final, tcs_score, fgc_score, tad_score, lhi_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [f"ens_{tid}", tid, ticker, scores['ens_final'],
                  scores['tcs_score'], scores['fgc_score'],
                  scores['tad_score'], scores['lhi_score']])
            
            if (i + 1) % 10 == 0:
                logger.info(f"  {i+1}/{len(transcripts)} done")
        
        conn.close()
        logger.info(f"ENS done: {len(transcripts)} scores")


if __name__ == "__main__":
    # Quick test
    composer = ENSComposer()
    sample = "CEO: Record revenue. We are confident. CFO: Margins expanded. Q&A Analyst: Outlook? CEO: Strong growth ahead."
    result = composer.compute('AAPL', sample)
    print(f"ENS: {result['ens_final']:.4f} (TCS={result['tcs_score']:.3f}, FGC={result['fgc_score']:.3f}, TAD={result['tad_score']:.3f}, LHI={result['lhi_score']:.3f})")