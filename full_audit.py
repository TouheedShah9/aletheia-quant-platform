import os
import duckdb

print('='*60)
print('FULL SYSTEM AUDIT')
print('='*60)

# Critical files
files = [
    'config.py', '.env', '.gitignore', 'aletheia.db',
    'ingestion/base_ingester.py', 'ingestion/price_ingester.py',
    'ingestion/edgar_bulk.py', 'ingestion/edgar_text_downloader.py',
    'models/ens/section_parser.py', 'models/ens/preprocessor.py',
    'models/ens/ens_scorers.py', 'models/ens/ens_composer.py',
    'models/riv/preprocessor.py', 'models/riv/classifier.py',
    'models/cmi/jobs_analyzer.py', 'models/cmi/web_monitor.py', 'models/cmi/signal_generator.py',
    'causal/ens_causal.py',
    'backtest/data_loader.py', 'backtest/engine.py', 'backtest/production_backtest.py',
    'backtest/walk_forward.py', 'backtest/final_validation.py',
    'portfolio/constructor.py', 'portfolio/risk_engine.py',
    'live/paper_trader.py', 'live/monitor.py',
    'fusion/regime_detector.py', 'fusion/signal_combiner.py',
    'docs/limitations.md', 'docs/results.md', 'docs/production_roadmap.md',
    'README.md',
]

missing = []
for f in files:
    if not os.path.exists(f):
        missing.append(f)

if missing:
    print(f'\nMISSING FILES ({len(missing)}):')
    for f in missing:
        print(f'  MISSING: {f}')
else:
    print('\nAll 32 critical files present')

# Database
conn = duckdb.connect('aletheia.db')
tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
print(f'\nDATABASE: {len(tables)} tables')

for t in tables:
    name = t[0]
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
        if count == 0:
            print(f'  EMPTY: {name}')
        else:
            print(f'  OK: {name} ({count} rows)')
    except:
        print(f'  ERROR: {name}')

# Key metrics
try:
    real_ens = conn.execute("SELECT COUNT(*) FROM ens_scores WHERE id LIKE 'earn_%'").fetchone()[0]
    print(f'\nReal earnings scores: {real_ens}')
except:
    pass

try:
    composites = conn.execute("SELECT COUNT(*) FROM composite_signals").fetchone()[0]
    longs = conn.execute("SELECT COUNT(*) FROM composite_signals WHERE signal_direction=1").fetchone()[0]
    shorts = conn.execute("SELECT COUNT(*) FROM composite_signals WHERE signal_direction=-1").fetchone()[0]
    print(f'Composite signals: {composites} ({longs} long, {shorts} short)')
except:
    pass

conn.close()

# Imports
print('\nIMPORTS:')
for mod in ['numpy','pandas','duckdb','yfinance','requests','loguru','tenacity','dotenv']:
    try:
        __import__(mod)
        print(f'  OK: {mod}')
    except:
        print(f'  FAIL: {mod}')

print('\n' + '='*60)
print('AUDIT COMPLETE')
print('='*60)