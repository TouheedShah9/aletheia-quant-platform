"""Import REAL Fama-French factors from Colab download"""
import duckdb, json

conn = duckdb.connect('aletheia.db')

# Create table if not exists
conn.execute("""
    CREATE TABLE IF NOT EXISTS fama_french_factors (
        factor_date DATE PRIMARY KEY,
        mkt_rf DOUBLE,
        smb DOUBLE,
        hml DOUBLE,
        rmw DOUBLE,
        cma DOUBLE,
        umd DOUBLE,
        rf DOUBLE
    )
""")

# Clear old data
conn.execute('DELETE FROM fama_french_factors')

# Load real data
with open('fama_french_real.json') as f:
    data = json.load(f)

count = 0
for r in data:
    # Fix date format: "2019-01" -> "2019-01-01"
    date_str = r['date'] + '-01'
    conn.execute(
        'INSERT INTO fama_french_factors VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [date_str, r['mkt_rf'], r['smb'], r['hml'], r['rmw'], r['cma'], r['umd'], r['rf']]
    )
    count += 1

# Verify
total = conn.execute('SELECT COUNT(*) FROM fama_french_factors').fetchone()[0]
sample = conn.execute('SELECT * FROM fama_french_factors LIMIT 1').fetchone()

print(f'✅ Imported {total} months of REAL Fama-French factors')
print(f'   Sample: {sample[0]} | Mkt-RF={sample[1]:+.4f} | SMB={sample[2]:+.4f} | HML={sample[3]:+.4f}')
print(f'   Source: Kenneth French Data Library')
print(f'   This is the same data every quant fund uses')

conn.close()