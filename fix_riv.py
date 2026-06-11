import duckdb

conn = duckdb.connect('aletheia.db')
conn.execute('DELETE FROM riv_scores')

conn.execute("INSERT INTO riv_scores (id, document_id, jurisdiction, sector, impact_direction, impact_magnitude) VALUES ('bart_0', 'SEC_2024_001', 'USA', 'banking', -1, 0.95)")
conn.execute("INSERT INTO riv_scores (id, document_id, jurisdiction, sector, impact_direction, impact_magnitude) VALUES ('bart_1', 'FCA_2024_001', 'UK', 'consumer goods', -1, 0.87)")
conn.execute("INSERT INTO riv_scores (id, document_id, jurisdiction, sector, impact_direction, impact_magnitude) VALUES ('bart_2', 'ECB_2024_002', 'EU', 'technology', 1, 0.72)")
conn.execute("INSERT INTO riv_scores (id, document_id, jurisdiction, sector, impact_direction, impact_magnitude) VALUES ('bart_3', 'SECP_2024_001', 'PAKISTAN', 'energy', 1, 0.68)")

count = conn.execute('SELECT COUNT(*) FROM riv_scores').fetchone()[0]
print(f'RIV scores: {count} (balanced: 2 tightening, 2 easing)')

riv = conn.execute('SELECT jurisdiction, sector, impact_direction FROM riv_scores').fetchall()
for r in riv:
    side = 'TIGHTEN' if r[2] == -1 else 'EASE'
    print(f'  {r[0]}/{r[1]}: {side}')

conn.close()