import duckdb
import json

conn = duckdb.connect('aletheia.db')
texts = conn.execute("SELECT id, ticker, event_date, full_text FROM transcripts_metadata WHERE source='SEC_8K_REAL' AND full_text IS NOT NULL").fetchall()

data = []
for t in texts:
    data.append({
        'id': t[0],
        'ticker': t[1],
        'date': str(t[2]),
        'text': t[3]
    })

with open('real_texts.json', 'w', encoding='utf-8') as f:
    json.dump(data, f)

print(f'Exported {len(data)} real EDGAR texts')
conn.close()