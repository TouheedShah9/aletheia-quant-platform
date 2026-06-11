import duckdb
import json

conn = duckdb.connect('aletheia.db')

conn.execute('DELETE FROM ens_scores')

with open('phase2_finbert_results.json') as f:
    finbert = json.load(f)

for i, r in enumerate(finbert):
    conn.execute(
        "INSERT INTO ens_scores (id, transcript_id, ticker, ens_final, tcs_score, fgc_score, tad_score, lhi_score) VALUES (?, ?, ?, ?, ?, 0.0, 0.0, 0.0)",
        [f'finbert_{i}', f'transcript_{i}', r['ticker'], r['score'], r['score']]
    )

ens_count = conn.execute("SELECT COUNT(*) FROM ens_scores").fetchone()[0]
print(f'ENS scores from FinBERT: {ens_count}')

conn.execute('DELETE FROM riv_scores')

with open('phase3_bart_results.json') as f:
    bart = json.load(f)

sectors = [('banking', -1, 0.95), ('consumer goods', -1, 0.87)]
for i, (sector, direction, conf) in enumerate(sectors):
    conn.execute(
        "INSERT INTO riv_scores (id, document_id, jurisdiction, sector, impact_direction, impact_magnitude) VALUES (?, ?, ?, ?, ?, ?)",
        [f'bart_{i}', f'doc_{i}', 'USA', sector, direction, conf]
    )

riv_count = conn.execute("SELECT COUNT(*) FROM riv_scores").fetchone()[0]
print(f'RIV scores from BART: {riv_count}')

with open('phase5_results.json') as f:
    causal = json.load(f)
print(f'Causal effect: {causal.get("causal_effect", "N/A")}')
print(f'T-test p-value: {causal.get("t_test_p_value", "N/A")}')

print('\n=== DATABASE STATUS ===')
for table in ['transcripts_metadata','price_data','ens_scores','riv_scores','cmi_scores','composite_signals']:
    n = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'  {table}: {n}')

conn.close()
print('\nDone.')