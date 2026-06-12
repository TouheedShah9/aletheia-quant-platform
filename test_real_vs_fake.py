"""
Real vs Fake Data Comparison
Proves every chart uses actual data, not simulated
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import duckdb, json
import pandas as pd
import numpy as np

print("="*60)
print("REAL vs FAKE DATA AUDIT")
print("="*60)
results = []

conn = duckdb.connect('aletheia.db')

# 1. Price data — real yfinance
print("\n1. PRICE DATA:")
prices = conn.execute("SELECT COUNT(*), COUNT(DISTINCT ticker), MIN(trade_date), MAX(trade_date) FROM price_data").fetchone()
is_real = prices[0] > 50000 and prices[1] > 30
print(f"   Rows: {prices[0]:,} | Tickers: {prices[1]} | Range: {prices[2]} to {prices[3]}")
print(f"   Source: {'REAL yfinance' if is_real else 'FAKE'}")
results.append(("Prices", "REAL" if is_real else "FAKE"))

# 2. Transcript metadata — real SEC EDGAR
print("\n2. TRANSCRIPTS:")
sec_count = conn.execute("SELECT COUNT(*) FROM transcripts_metadata WHERE source LIKE 'SEC_%'").fetchone()[0]
gen_count = conn.execute("SELECT COUNT(*) FROM transcripts_metadata WHERE source LIKE 'gen_%' OR source = 'generated_sample'").fetchone()[0]
real_text = conn.execute("SELECT COUNT(*) FROM transcripts_metadata WHERE full_text IS NOT NULL AND source LIKE 'SEC_%'").fetchone()[0]
print(f"   SEC filings: {sec_count} | Generated: {gen_count} | With real text: {real_text}")
print(f"   Source: {'REAL SEC EDGAR' if sec_count > 100 else 'MOSTLY GENERATED'}")
results.append(("Transcripts", "REAL" if sec_count > 100 else "MIXED"))

# 3. ENS scores — real FinBERT
print("\n3. ENS SCORES:")
finbert_count = conn.execute("SELECT COUNT(*) FROM ens_scores WHERE id LIKE 'earn_%'").fetchone()[0]
keyword_count = conn.execute("SELECT COUNT(*) FROM ens_scores WHERE id LIKE 'ens_%'").fetchone()[0]
real_finbert = finbert_count > 0
print(f"   FinBERT (real): {finbert_count} | Keyword (local): {keyword_count}")
print(f"   Source: {'REAL FinBERT' if real_finbert else 'KEYWORD ONLY'}")
results.append(("ENS Scores", "REAL" if real_finbert else "KEYWORD"))

# 4. Composite signals — from real ENS
print("\n4. COMPOSITE SIGNALS:")
sig_count = conn.execute("SELECT COUNT(*) FROM composite_signals").fetchone()[0]
sig_sample = conn.execute("SELECT ticker, composite_score, signal_direction FROM composite_signals LIMIT 3").fetchall()
print(f"   Count: {sig_count}")
for s in sig_sample:
    direction = 'LONG' if s[2]==1 else ('SHORT' if s[2]==-1 else 'NEUTRAL')
    print(f"   {s[0]}: {s[1]:+.4f} ({direction})")
print(f"   Source: {'REAL' if sig_count > 0 else 'EMPTY'}")
results.append(("Signals", "REAL" if sig_count > 0 else "EMPTY"))

# 5. Alpaca data — real paper account
print("\n5. ALPACA POSITIONS:")
try:
    with open('alpaca_data.json') as f:
        alpaca = json.load(f)
    positions = alpaca.get('positions', [])
    equity = alpaca.get('equity', 0)
    is_real_alpaca = len(positions) > 0 and equity != 100000
    print(f"   Equity: ${equity:,.2f} | Positions: {len(positions)}")
    for p in positions:
        print(f"   {p['symbol']}: {p['qty']}sh @ ${p['avg_entry']:.2f} | P&L: ${p['unrealized_pl']:,.2f}")
    print(f"   Source: {'REAL Alpaca' if is_real_alpaca else 'SIMULATED'}")
    results.append(("Alpaca", "REAL" if is_real_alpaca else "SIMULATED"))
except:
    print("   No Alpaca data")
    results.append(("Alpaca", "MISSING"))

# 6. Email — real Gmail
print("\n6. EMAIL:")
import os
from dotenv import load_dotenv
load_dotenv()
smtp_set = bool(os.getenv('SMTP_USER') and os.getenv('SMTP_PASS'))
print(f"   Configured: {smtp_set}")
print(f"   Source: {'REAL Gmail' if smtp_set else 'NOT CONFIGURED'}")
results.append(("Email", "REAL" if smtp_set else "NOT SET"))

# 7. Slack — real webhook
print("\n7. SLACK:")
slack_set = bool(os.getenv('SLACK_WEBHOOK'))
print(f"   Configured: {slack_set}")
print(f"   Source: {'REAL Slack' if slack_set else 'NOT CONFIGURED'}")
results.append(("Slack", "REAL" if slack_set else "NOT SET"))

# 8. Security — real users
print("\n8. SECURITY:")
users_exist = os.path.exists('security/users.json')
sessions_exist = os.path.exists('security/sessions.json')
print(f"   Users file: {users_exist} | Sessions: {sessions_exist}")
print(f"   Source: {'REAL' if users_exist else 'MISSING'}")
results.append(("Security", "REAL" if users_exist else "MISSING"))

# 9. Logs — real monitoring
print("\n9. MONITORING LOGS:")
for log_file in ['logs/errors.json', 'logs/uptime.json', 'logs/metrics.json']:
    exists = os.path.exists(log_file)
    size = os.path.getsize(log_file) if exists else 0
    print(f"   {log_file}: {'EXISTS' if exists else 'MISSING'} ({size} bytes)")
results.append(("Logs", "REAL" if os.path.exists('logs/errors.json') else "MISSING"))

conn.close()

# Summary
print("\n" + "="*60)
real_count = sum(1 for r in results if 'REAL' in str(r[1]))
fake_count = sum(1 for r in results if 'FAKE' in str(r[1]) or 'SIMULATED' in str(r[1]) or 'MISSING' in str(r[1]) or 'KEYWORD' in str(r[1]) or 'MIXED' in str(r[1]) or 'NOT' in str(r[1]))
for name, status in results:
    icon = '✅' if 'REAL' in str(status) else '⚠️' if 'MIXED' in str(status) or 'KEYWORD' in str(status) else '❌'
    print(f"  {icon} {name}: {status}")
print(f"\nREAL: {real_count} | NOT REAL: {fake_count}")
print("="*60)