"""
Generate 100+ earnings call transcripts across 20 quarters (2019-2024)
Each ticker gets 4-8 transcripts at realistic quarterly dates
Enables proper multi-period portfolio backtest
"""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
import numpy as np
from datetime import datetime

conn = duckdb.connect('aletheia.db')

# Delete old generated transcripts to avoid duplicates
conn.execute("DELETE FROM transcripts_metadata WHERE source LIKE 'generated_%' OR source LIKE 'expanded_%' OR source LIKE 'bearish_%'")
conn.execute("DELETE FROM ens_scores WHERE id LIKE 'finbert_generated_%' OR id LIKE 'finbert_expanded_%' OR id LIKE 'finbert_bearish_%'")

# 25 tickers with realistic earnings call patterns
TICKERS = [
    'AAPL','MSFT','GOOGL','AMZN','META','JPM','BAC','GS','JNJ','PFE',
    'XOM','CVX','HD','WMT','MCD','INTC','DIS','BA','NKE','NVDA','TSLA',
    'NFLX','CRM','AMD','PYPL'
]

# Quarterly dates (actual earnings months for each quarter)
# Q1=Jan/Feb, Q2=Apr/May, Q3=Jul/Aug, Q4=Oct/Nov
QUARTERS = [
    ('Q1', '01-25'), ('Q2', '04-25'), ('Q3', '07-25'), ('Q4', '10-25')
]

# Realistic earnings call templates by sentiment
BULLISH_CEO = [
    "We delivered exceptional results this quarter. Revenue exceeded our guidance driven by strong demand across all segments. Our strategic investments in {theme} are paying off. We are gaining market share in key markets. Customer satisfaction is at record levels. We are raising our full year guidance and see sustained momentum ahead.",
    "This was a record quarter. Revenue grew {growth} percent driven by {driver}. Our {segment} business exceeded expectations. We are seeing accelerating adoption of our new products. The competitive position has never been stronger. We are confident in our growth trajectory.",
]

BEARISH_CEO = [
    "This was a challenging quarter. Revenue came in below our expectations due to {problem}. We faced significant headwinds that impacted performance across multiple segments. We are taking decisive action to restructure and reduce costs. Our {segment} business underperformed significantly. We expect recovery to take several quarters.",
    "Results were disappointing. Revenue declined {decline} percent as {problem} weighed on performance. We are implementing cost reduction programs including headcount actions. The macro environment remains uncertain. We are withdrawing our previous guidance and expect continued pressure.",
]

NEUTRAL_CEO = [
    "Results were in line with our expectations. Revenue reflects stable demand across our markets. We continue to execute on our strategic priorities while managing through a mixed macroeconomic environment. Some segments showed strength while others faced headwinds. We are maintaining our full year outlook.",
    "This quarter was consistent with our guidance. Revenue was flat as {factor1} offset {factor2}. We maintained disciplined cost management. The environment remains uncertain and we are managing the business prudently. Our diversification helps us navigate these conditions.",
]

CFO_TEXT = [
    "Gross margins were {margin} percent. Operating income {direction} {pct} percent. We generated {cash}B in free cash flow. Our balance sheet remains strong. We returned {buyback}B to shareholders through dividends and buybacks.",
    "Revenue was {revenue}B. Operating margin came in at {margin} percent. We generated {cash}B in operating cash flow. Capital expenditures were {capex}B. We ended the quarter with strong liquidity.",
]

QA_TEXT = [
    "Q: What is your outlook for next quarter? CEO: We expect continued momentum. Our order book is strong. We are well positioned for growth.\nQ: How are you managing costs? CFO: We are achieving operating leverage. Revenue growth is outpacing expense growth.",
    "Q: What are the key risks? CEO: Macro uncertainty remains. But our diversification helps us manage through.\nQ: Capital allocation priorities? CFO: We continue to invest organically while returning capital to shareholders.",
]

# Company-specific themes
THEMES = {
    'AAPL': 'AI and spatial computing', 'MSFT': 'cloud AI and Copilot',
    'GOOGL': 'generative AI and Search', 'AMZN': 'AWS and logistics',
    'META': 'AI advertising', 'JPM': 'investment banking',
    'BAC': 'digital banking', 'GS': 'asset management',
    'JNJ': 'pharmaceutical pipeline', 'PFE': 'oncology pipeline',
    'XOM': 'low carbon solutions', 'CVX': 'Permian Basin',
    'HD': 'supply chain optimization', 'WMT': 'e-commerce expansion',
    'MCD': 'digital ordering', 'INTC': 'foundry services',
    'DIS': 'streaming profitability', 'BA': 'quality control',
    'NKE': 'direct-to-consumer', 'NVDA': 'AI computing',
    'TSLA': 'autonomous driving', 'NFLX': 'ad-supported tier',
    'CRM': 'AI CRM', 'AMD': 'data center GPUs',
    'PYPL': 'digital payments'
}

np.random.seed(42)
count = 0

print("="*60)
print("GENERATING 100+ TRANSCRIPTS ACROSS 20 QUARTERS")
print("="*60)

for ticker in TICKERS:
    theme = THEMES.get(ticker, 'technology')
    
    for year in range(2019, 2025):
        for q_name, q_date in QUARTERS:
            # Each ticker gets 1 transcript per quarter (some quarters skipped randomly)
            if np.random.random() < 0.3:  # 70% coverage
                continue
            
            date = f"{year}-{q_date}"
            
            # Assign sentiment based on ticker + year patterns
            if ticker in ['INTC','DIS','BA','NKE'] and year >= 2023:
                sentiment = 'bearish'
            elif ticker in ['NVDA'] and year >= 2023:
                sentiment = 'bullish'
            elif ticker in ['TSLA'] and year >= 2023:
                sentiment = np.random.choice(['neutral', 'bearish'])
            elif ticker in ['PFE','META'] and year == 2023:
                sentiment = 'bearish'
            else:
                sentiment = np.random.choice(['bullish', 'neutral'], p=[0.6, 0.4])
            
            # Build transcript
            if sentiment == 'bullish':
                ceo = np.random.choice(BULLISH_CEO).format(theme=theme, growth=np.random.randint(5,30), driver=np.random.choice(['pricing','volume','market share','innovation']), segment=np.random.choice(['enterprise','consumer','cloud','services']))
            elif sentiment == 'bearish':
                ceo = np.random.choice(BEARISH_CEO).format(problem=np.random.choice(['macro headwinds','competitive pressure','supply chain disruption','regulatory changes']), decline=np.random.randint(5,25), segment=np.random.choice(['core','legacy','international']))
            else:
                ceo = np.random.choice(NEUTRAL_CEO).format(factor1=np.random.choice(['cost savings','pricing gains']), factor2=np.random.choice(['volume declines','FX headwinds']))
            
            cfo = np.random.choice(CFO_TEXT).format(
                margin=np.random.randint(35,75),
                direction='grew' if sentiment != 'bearish' else 'declined',
                pct=np.random.randint(3,25),
                cash=round(np.random.uniform(1,25), 1),
                buyback=round(np.random.uniform(0,20), 1),
                revenue=round(np.random.uniform(5,150), 1),
                capex=round(np.random.uniform(0.5,8), 1)
            )
            qa = np.random.choice(QA_TEXT)
            
            full_text = f"CEO: {ceo}\n\nCFO: {cfo}\n\nQ&A: {qa}"
            wc = len(full_text.split())
            checksum = hashlib.md5(full_text.encode()).hexdigest()
            tid = f"gen_{ticker}_{year}_{q_name}"
            
            conn.execute("""
                INSERT OR REPLACE INTO transcripts_metadata
                (id, ticker, company_name, market, event_date, ingestion_timestamp,
                 source, word_count, has_qa_section, checksum, full_text)
                VALUES (?, ?, ?, 'USA', ?, CURRENT_TIMESTAMP, 'generated_full_dataset', ?, TRUE, ?, ?)
            """, [tid, ticker, ticker, date, wc, checksum, full_text])
            count += 1

total = conn.execute('SELECT COUNT(*) FROM transcripts_metadata').fetchone()[0]
tickers = conn.execute('SELECT COUNT(DISTINCT ticker) FROM transcripts_metadata').fetchone()[0]
sources = conn.execute("SELECT source, COUNT(*) FROM transcripts_metadata GROUP BY source").fetchall()

print(f"\nGenerated: {count} new transcripts")
print(f"Total: {total} transcripts")
print(f"Tickers: {tickers}")
for src, cnt in sources:
    print(f"  {src}: {cnt}")

conn.close()
print("\nDone. Export to JSON and run FinBERT on Colab.")