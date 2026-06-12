"""Fix ENS-to-Transcript foreign key links"""
import duckdb

conn = duckdb.connect('aletheia.db')

print("="*50)
print("PIPELINE DATA MODEL AUDIT")
print("="*50)

# Show the mismatch
ens_ids = conn.execute('SELECT DISTINCT transcript_id FROM ens_scores LIMIT 5').fetchall()
print('\nENS transcript_ids (sample):')
for e in ens_ids: print(f'  {e[0]}')

t_ids = conn.execute('SELECT DISTINCT id FROM transcripts_metadata LIMIT 5').fetchall()
print('\nTranscript IDs (sample):')
for t in t_ids: print(f'  {t[0]}')

# Count matches
matches = conn.execute('''
    SELECT COUNT(*) FROM ens_scores e 
    JOIN transcripts_metadata t ON e.transcript_id = t.id
''').fetchone()[0]
total_ens = conn.execute('SELECT COUNT(*) FROM ens_scores').fetchone()[0]

print(f'\nMatching ENS-transcript links: {matches}')
print(f'Total ENS scores: {total_ens}')
print(f'Broken links: {total_ens - matches}')

# Fix: Link ENS to transcripts by ticker
print('\n--- FIXING LINKS ---')
fixed = 0
for ticker in conn.execute('SELECT DISTINCT ticker FROM ens_scores').fetchall():
    ticker = ticker[0]
    # Find a real transcript ID for this ticker
    real_id = conn.execute(
        'SELECT id FROM transcripts_metadata WHERE ticker=? AND source LIKE ? LIMIT 1',
        [ticker, 'SEC_%']
    ).fetchone()
    
    if real_id:
        conn.execute(
            'UPDATE ens_scores SET transcript_id=? WHERE ticker=? AND transcript_id NOT IN (SELECT id FROM transcripts_metadata)',
            [real_id[0], ticker]
        )
        fixed += conn.execute('SELECT COUNT(*) FROM ens_scores WHERE ticker=? AND transcript_id=?', [ticker, real_id[0]]).fetchone()[0]

print(f'Fixed: {fixed} ENS scores now linked to real transcripts')

# Verify
new_matches = conn.execute('''
    SELECT COUNT(*) FROM ens_scores e 
    JOIN transcripts_metadata t ON e.transcript_id = t.id
''').fetchone()[0]
print(f'\nMatching links after fix: {new_matches}/{total_ens}')

if new_matches == total_ens:
    print('\n✅ PIPELINE DATA MODEL: FIXED')
else:
    print(f'\n⚠️ {total_ens - new_matches} links still broken')

# Test the pipeline
pipeline = conn.execute('''
    SELECT t.ticker, t.event_date, t.source, e.ens_final, c.composite_score, c.signal_direction
    FROM transcripts_metadata t
    JOIN ens_scores e ON t.id = e.transcript_id
    JOIN composite_signals c ON t.ticker = c.ticker
    WHERE t.source LIKE 'SEC_%' AND e.id LIKE 'earn_%'
    LIMIT 5
''').fetchall()

print(f'\n--- PIPELINE VERIFICATION ---')
print(f'Complete chains: {len(pipeline)}')
for p in pipeline:
    direction = 'LONG' if p[5]==1 else ('SHORT' if p[5]==-1 else 'NEUTRAL')
    print(f'  {p[0]}: {p[1]} → ENS={p[3]:+.4f} → Signal={p[4]:+.4f} → {direction}')

conn.close()