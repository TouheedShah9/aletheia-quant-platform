"""
DuckDB Schema - Project Aletheia
"""
import duckdb
from loguru import logger

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS transcripts_metadata (
    id VARCHAR PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    company_name VARCHAR,
    market VARCHAR NOT NULL,
    event_date DATE NOT NULL,
    ingestion_timestamp TIMESTAMP NOT NULL,
    source VARCHAR NOT NULL,
    word_count INTEGER,
    has_qa_section BOOLEAN,
    checksum VARCHAR
);

CREATE TABLE IF NOT EXISTS price_data (
    id VARCHAR PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    trade_date DATE NOT NULL,
    adj_close DOUBLE NOT NULL,
    volume BIGINT,
    ingestion_timestamp TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS abnormal_returns (
    transcript_id VARCHAR,
    ticker VARCHAR NOT NULL,
    event_date DATE NOT NULL,
    horizon_days INTEGER NOT NULL,
    abnormal_return DOUBLE,
    PRIMARY KEY (transcript_id, horizon_days)
);

CREATE TABLE IF NOT EXISTS ens_scores (
    id VARCHAR PRIMARY KEY,
    transcript_id VARCHAR,
    ticker VARCHAR NOT NULL,
    ens_final DOUBLE NOT NULL,
    tcs_score DOUBLE,
    fgc_score DOUBLE,
    tad_score DOUBLE,
    lhi_score DOUBLE,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS riv_scores (
    id VARCHAR PRIMARY KEY,
    document_id VARCHAR NOT NULL,
    jurisdiction VARCHAR NOT NULL,
    sector VARCHAR NOT NULL,
    impact_direction INTEGER,
    impact_magnitude DOUBLE,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cmi_scores (
    id VARCHAR PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    score_date DATE NOT NULL,
    cmi_final DOUBLE NOT NULL,
    job_anomaly_score DOUBLE,
    web_change_score DOUBLE,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS composite_signals (
    id VARCHAR PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    signal_date DATE NOT NULL,
    market_regime VARCHAR NOT NULL,
    composite_score DOUBLE NOT NULL,
    signal_direction INTEGER,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backtest_trades (
    id VARCHAR PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    entry_date DATE NOT NULL,
    exit_date DATE,
    direction INTEGER NOT NULL,
    pnl DOUBLE,
    regime VARCHAR
);

CREATE TABLE IF NOT EXISTS backtest_results (
    backtest_id VARCHAR PRIMARY KEY,
    sharpe_ratio DOUBLE,
    max_drawdown DOUBLE,
    hit_rate DOUBLE,
    num_trades INTEGER,
    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingestion_audit_log (
    id VARCHAR PRIMARY KEY,
    operation VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    records_succeeded INTEGER,
    records_failed INTEGER,
    completed_at TIMESTAMP
);
"""

def init_db(path="aletheia.db"):
    conn = duckdb.connect(path)
    conn.execute(SCHEMA_SQL)
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()
    print(f"Database ready: {len(tables)} tables created")
    for t in tables:
        print(f"  - {t[0]}")
    return conn

if __name__ == "__main__":
    conn = init_db()
    conn.close()
    print("Done.")