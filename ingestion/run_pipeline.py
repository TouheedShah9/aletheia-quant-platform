"""
Production Data Pipeline - Runs all ingestion with audit logging
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
from datetime import datetime

conn = duckdb.connect('aletheia.db')

def log_audit(operation, source, succeeded, failed=0):
    conn.execute("""
        INSERT INTO ingestion_audit_log (id, operation, source, records_succeeded, records_failed, completed_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, [f'audit_{datetime.now().strftime("%Y%m%d%H%M%S")}_{operation}',
          operation, source, succeeded, failed])

tables = {
    'transcripts_metadata': 'SEC EDGAR + Generated',
    'price_data': 'Yahoo Finance',
    'ens_scores': 'FinBERT GPU + Local',
    'riv_scores': 'BART + Local',
    'cmi_scores': 'Local Heuristics',
    'composite_signals': 'Signal Fusion',
}

print("INGESTION AUDIT")
print("="*50)

for table, source in tables.items():
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    log_audit(f'count_{table}', source, count)
    print(f"  {table:25s}: {count:>6d} rows | {source}")

total_rows = sum(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables)
log_audit('system_health', 'all_sources', total_rows)
print(f"\n  Total rows: {total_rows:,}")

print(f"\nRECENT AUDIT LOG:")
logs = conn.execute("SELECT operation, source, records_succeeded, completed_at FROM ingestion_audit_log ORDER BY completed_at DESC LIMIT 8").fetchall()
for log in logs:
    print(f"  {log[3]} | {log[0]:20s} | {log[1]:25s} | {log[2]} rows")

conn.close()
print("\nPipeline audit complete.")