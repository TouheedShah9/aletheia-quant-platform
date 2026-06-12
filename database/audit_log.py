"""
Append-Only Audit Log — Immutable event sourcing
Every data change is written to an append-only CSV
"""
import csv
from datetime import datetime
from pathlib import Path

AUDIT_FILE = Path(__file__).parent.parent / 'audit_trail.csv'

def log_event(event_type: str, table: str, record_id: str, action: str, details: str = ""):
    """Append an immutable audit event."""
    existed = AUDIT_FILE.exists()
    with open(AUDIT_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not existed:
            writer.writerow(['timestamp', 'event_type', 'table', 'record_id', 'action', 'details'])
        writer.writerow([datetime.utcnow().isoformat(), event_type, table, record_id, action, details])

def get_audit_trail(table: str = None, limit: int = 100):
    """Read audit trail."""
    if not AUDIT_FILE.exists():
        return []
    with open(AUDIT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if table:
        rows = [r for r in rows if r['table'] == table]
    return rows[-limit:]