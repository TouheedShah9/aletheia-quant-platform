"""
RIV Classifier - Regulatory Impact Vector scoring
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import duckdb
from loguru import logger
from models.riv.preprocessor import RIVPreprocessor


class RIVClassifier:
    def __init__(self):
        self.preprocessor = RIVPreprocessor()

    def score_document(self, text, jurisdiction="USA"):
        chunks = self.preprocessor.chunk_document(text, 500)
        financial = self.preprocessor.filter_financial_chunks(chunks)
        combined = ' '.join(financial) if financial else text
        sectors = self.preprocessor.detect_sectors(combined)
        direction = self.preprocessor.classify_direction(combined)
        
        results = []
        for s in sectors:
            results.append({
                'sector': s['sector'],
                'direction': direction['direction'],
                'magnitude': round(direction['magnitude'] * s['relevance'] / 10, 3),
                'confidence': direction['confidence']
            })
        return results

    def batch_score(self, db_path="aletheia.db"):
        conn = duckdb.connect(db_path)
        
        samples = [
            {'id':'SEC_2024_001','date':'2024-03-15','jurisdiction':'USA',
             'text':"""SEC adopts final rules increasing capital requirements 
             for banks over $100B. Tier 1 capital ratio from 4.5% to 6%. 
             Enhanced stress testing. Penalties include dividend restrictions."""},
            {'id':'FCA_2024_001','date':'2024-02-20','jurisdiction':'UK',
             'text':"""FCA extends Consumer Duty to closed products. Firms must 
             ensure fair value for legacy products. Enhanced reporting required.
             Implementation extended to July 2025 for small firms."""},
            {'id':'ECB_2024_001','date':'2024-04-10','jurisdiction':'EU',
             'text':"""ECB publishes climate risk stress testing guide. Banks 
             must assess physical and transition risks. First mandatory exercise 
             2025. Proportionate approach for smaller institutions."""},
            {'id':'SECP_2024_001','date':'2024-01-25','jurisdiction':'PAKISTAN',
             'text':"""SECP issues revised corporate governance regulations. 
             Enhanced board independence. Mandatory ESG reporting for top 100. 
             Relaxed filing deadlines for SMEs. New related party rules."""},
        ]
        
        for doc in samples:
            impacts = self.score_document(doc['text'], doc['jurisdiction'])
            for imp in impacts:
                rid = f"riv_{doc['id']}_{imp['sector']}"
                conn.execute("""
                    INSERT INTO riv_scores (id, document_id, jurisdiction, sector, impact_direction, impact_magnitude)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [rid, doc['id'], doc['jurisdiction'], imp['sector'], imp['direction'], imp['magnitude']])
                logger.info(f"  {doc['jurisdiction']}/{imp['sector']}: dir={imp['direction']}, mag={imp['magnitude']:.2f}")
        
        conn.close()
        logger.info(f"RIV done: {len(samples)} documents")


if __name__ == "__main__":
    RIVClassifier().batch_score()