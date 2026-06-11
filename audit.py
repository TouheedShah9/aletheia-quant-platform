import duckdb, os, json

print('='*60)
print('PROJECT ALETHEIA - FULL SYSTEM AUDIT')
print('='*60)

# Phase 0
print('\n--- PHASE 0: FOUNDATION ---')
print(f'config.py: {os.path.exists("config.py")}')
print(f'aletheia.db: {os.path.exists("aletheia.db")}')

# Phase 1
print('\n--- PHASE 1: DATA PIPELINE ---')
conn = duckdb.connect('aletheia.db')
prices = conn.execute('SELECT COUNT(*) FROM price_data').fetchone()[0]
transcripts = conn.execute('SELECT COUNT(*) FROM transcripts_metadata').fetchone()[0]
tickers_p = conn.execute('SELECT COUNT(DISTINCT ticker) FROM price_data').fetchone()[0]
tickers_t = conn.execute('SELECT COUNT(DISTINCT ticker) FROM transcripts_metadata').fetchone()[0]
has_text = conn.execute("SELECT COUNT(*) FROM transcripts_metadata WHERE full_text IS NOT NULL").fetchone()[0]
print(f'Price rows: {prices:,} | Tickers: {tickers_p}')
print(f'Transcript rows: {transcripts} | Tickers: {tickers_t} | With text: {has_text}')

# Phase 2
print('\n--- PHASE 2: ENS ---')
ens = conn.execute("SELECT ticker, ROUND(AVG(ens_final),4) FROM ens_scores GROUP BY ticker").fetchall()
real_ens = conn.execute("SELECT COUNT(*) FROM ens_scores WHERE id LIKE 'finbert_%'").fetchone()[0]
print(f'ENS scores: {len(ens)*3} total (3 per ticker), {real_ens} from FinBERT')
for e in ens:
    print(f'  {e[0]}: {e[1]:+.4f}')

# Phase 3
print('\n--- PHASE 3: RIV ---')
riv = conn.execute('SELECT jurisdiction, sector, impact_direction, impact_magnitude FROM riv_scores').fetchall()
print(f'RIV scores: {len(riv)}')
for r in riv:
    print(f'  {r[0]}/{r[1]}: dir={r[2]:+d} mag={r[3]:.2f}')

# Phase 4
print('\n--- PHASE 4: CMI ---')
cmi = conn.execute('SELECT ticker, cmi_final FROM cmi_scores').fetchall()
print(f'CMI scores: {len(cmi)}')
for c in cmi:
    print(f'  {c[0]}: {c[1]:+.3f}')

# Phase 5
print('\n--- PHASE 5: CAUSAL ---')
if os.path.exists('phase5_results.json'):
    with open('phase5_results.json') as f:
        causal = json.load(f)
    print(f'Causal effect: {causal.get("causal_effect","?")}')
    print(f'T-test p-value: {causal.get("t_test_p_value","?")}')
    print(f'Placebo: {causal.get("placebo_treatment","?")}')
    print(f'Random cause: {causal.get("random_common_cause","?")}')

# Phase 6
print('\n--- PHASE 6: BACKTEST ---')
print(f'backtest/full_backtest.py: {os.path.exists("backtest/full_backtest.py")}')
print(f'backtest/engine.py: {os.path.exists("backtest/engine.py")}')

# Phase 7
print('\n--- PHASE 7: FUSION ---')
comp = conn.execute('SELECT ticker, composite_score, signal_direction FROM composite_signals').fetchall()
print(f'Composite signals: {len(comp)}')
for c in comp:
    side = 'LONG' if c[2]==1 else ('SHORT' if c[2]==-1 else 'NEUTRAL')
    print(f'  {c[0]}: {c[1]:+.4f} ({side})')

# Missing files
print('\n--- MISSING FILES ---')
needed = [
    'portfolio/constructor.py', 'portfolio/risk_engine.py',
    'live/paper_trader.py', 'live/monitor.py',
    'docs/limitations.md', 'docs/results.md', 'docs/production_roadmap.md',
    'README.md'
]
missing = [f for f in needed if not os.path.exists(f)]
if missing:
    for f in missing:
        print(f'  MISSING: {f}')
else:
    print('  All files present')

conn.close()
print('\n' + '='*60)
print('AUDIT COMPLETE')
print('='*60)