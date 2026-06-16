import duckdb, json

conn = duckdb.connect('aletheia.db')
transcripts = conn.execute("""
    SELECT id, ticker, event_date, full_text
    FROM transcripts_metadata
    WHERE source = 'generated_full_dataset'
    AND full_text IS NOT NULL
""").fetchall()

data = []
for t in transcripts:
    data.append({
        'id': t[0],
        'ticker': t[1],
        'date': str(t[2]),
        'text': t[3]
    })

with open('real_texts.json', 'w', encoding='utf-8') as f:
    json.dump(data, f)

print(f'Exported {len(data)} transcripts to real_texts.json')
conn.close()