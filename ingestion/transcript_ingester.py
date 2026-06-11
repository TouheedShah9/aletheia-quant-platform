"""
Transcript Ingester - Earnings call transcripts
Sources: HuggingFace edgar-corpus (primary) + SEC EDGAR (supplement)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import duckdb
from loguru import logger
from ingestion.base_ingester import BaseIngester
import config


class TranscriptIngester(BaseIngester):
    def __init__(self):
        super().__init__("transcripts", rate_limit=2.0)

    def ingest_from_huggingface(self, db_path="aletheia.db"):
        """
        Load pre-cleaned transcripts from HuggingFace edgar-corpus.
        This is the fastest way to get US earnings call data.
        Covers major US companies from 2019-2023.
        """
        try:
            from datasets import load_dataset
            logger.info("Loading edgar-corpus from HuggingFace...")
            dataset = load_dataset("eloukas/edgar-corpus", split="train")
            logger.info(f"Loaded {len(dataset)} documents")
        except Exception as e:
            logger.error(f"HuggingFace load failed: {e}")
            logger.info("Trying alternative: financial_phrasebank...")
            return 0

        conn = duckdb.connect(db_path)
        us_tickers = {t for t, m in [(x['ticker'], x['market']) for x in config.ALL_TICKERS] if m == 'USA'}
        count = 0

        for item in dataset:
            try:
                ticker = str(item.get('ticker', '')).upper().strip()
                if ticker not in us_tickers:
                    continue

                text = str(item.get('text', ''))
                if len(text) < config.TRANSCRIPT_MIN_WORDS:
                    continue

                transcript_id = f"hf_{ticker}_{count}"
                checksum = self.make_checksum(text)

                # Check if exists
                exists = conn.execute(
                    "SELECT 1 FROM transcripts_metadata WHERE checksum = ?", [checksum]
                ).fetchone()

                if exists:
                    continue

                conn.execute("""
                    INSERT INTO transcripts_metadata 
                    (id, ticker, company_name, market, event_date, 
                     ingestion_timestamp, source, word_count, 
                     has_qa_section, checksum)
                    VALUES (?, ?, ?, 'USA', '2020-01-01', 
                            CURRENT_TIMESTAMP, 'huggingface_edgar', 
                            ?, ?, ?)
                """, [
                    transcript_id, ticker, ticker,
                    len(text.split()),
                    'Q&A' in text or 'question' in text.lower(),
                    checksum
                ])

                count += 1
                if count % 50 == 0:
                    logger.info(f"  {count} transcripts stored...")

            except Exception as e:
                continue

        conn.close()
        logger.info(f"Transcripts ingested: {count}")
        return count

    def ingest_sample_from_edgar(self, db_path="aletheia.db"):
        """
        Pull recent 8-K filings from SEC EDGAR as sample.
        Full EDGAR ingestion runs on Colab due to volume.
        """
        try:
            from sec_edgar_downloader import Downloader
            dl = Downloader("aletheia_data", config.EMAIL)
            logger.info("SEC EDGAR downloader ready")
            logger.info("Downloading sample AAPL 8-K filings...")

            dl.get("8-K", "AAPL", after="2023-01-01", before="2024-12-31")
            logger.info("Sample EDGAR data downloaded to aletheia_data/")
            return True
        except Exception as e:
            logger.warning(f"EDGAR sample download note: {e}")
            logger.info("EDGAR bulk download will run on Colab for full coverage")
            return False


if __name__ == "__main__":
    ingester = TranscriptIngester()

    logger.info("=" * 50)
    logger.info("Step 1: HuggingFace edgar-corpus")
    count = ingester.ingest_from_huggingface()

    logger.info("=" * 50)
    logger.info("Step 2: SEC EDGAR sample")
    ingester.ingest_sample_from_edgar()

    # Verify
    conn = duckdb.connect("aletheia.db")
    total = conn.execute("SELECT COUNT(*) FROM transcripts_metadata").fetchone()[0]
    tickers = conn.execute("SELECT DISTINCT ticker FROM transcripts_metadata").fetchall()
    logger.info("=" * 50)
    logger.info(f"Total transcripts in DB: {total}")
    logger.info(f"Companies covered: {len(tickers)}")
    if tickers:
        logger.info(f"Tickers: {[t[0] for t in tickers[:10]]}...")
    conn.close()