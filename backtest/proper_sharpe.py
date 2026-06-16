"""
Proper Sharpe Calculation — Portfolio-level backtest
Multiple positions per period, weighted by signal strength
"""
import duckdb, numpy as np, pandas as pd

conn = duckdb.connect('aletheia.db')

# Get ALL transcripts with dates and scores
data = conn.execute("""
    SELECT t.ticker, t.event_date, AVG(e.tcs_score) as ens_score
    FROM transcripts_metadata t
    JOIN ens_scores e ON t.id = e.transcript_id
    WHERE e.id LIKE 'finbert_%'
    AND t.event_date IS NOT NULL
    GROUP BY t.ticker, t.event_date
    ORDER BY t.event_date
""").fetchall()

print(f"Total events: {len(data)}")

# Group by month (portfolio period)
from collections import defaultdict
periods = defaultdict(list)

for ticker, event_date, score in data:
    # Extract year-month as period
    period = str(event_date)[:7]
    periods[period].append({
        'ticker': ticker,
        'ens_score': score,
        'event_date': str(event_date)
    })

# For each period, build a portfolio
portfolio_returns = []

for period, events in sorted(periods.items()):
    if len(events) < 2:  # Need at least 2 stocks for long-short
        continue
    
    # Sort by signal strength
    events_sorted = sorted(events, key=lambda x: x['ens_score'], reverse=True)
    
    # Long top half, short bottom half
    split = len(events_sorted) // 2
    longs = events_sorted[:split]
    shorts = events_sorted[split:]
    
    # Calculate equal-weighted returns
    long_return = 0
    short_return = 0
    count = 0
    
    for ev in longs:
        p_start = conn.execute("""
            SELECT adj_close FROM price_data
            WHERE ticker = ? AND trade_date >= ?
            ORDER BY trade_date LIMIT 1
        """, [ev['ticker'], ev['event_date']]).fetchone()
        
        p_end = conn.execute("""
            SELECT adj_close FROM price_data
            WHERE ticker = ? AND trade_date >= ?
            ORDER BY trade_date LIMIT 1 OFFSET 20
        """, [ev['ticker'], ev['event_date']]).fetchone()
        
        if p_start and p_end and p_start[0] > 0:
            ret = (p_end[0] - p_start[0]) / p_start[0]
            long_return += ret
            count += 1
    
    for ev in shorts:
        p_start = conn.execute("""
            SELECT adj_close FROM price_data
            WHERE ticker = ? AND trade_date >= ?
            ORDER BY trade_date LIMIT 1
        """, [ev['ticker'], ev['event_date']]).fetchone()
        
        p_end = conn.execute("""
            SELECT adj_close FROM price_data
            WHERE ticker = ? AND trade_date >= ?
            ORDER BY trade_date LIMIT 1 OFFSET 20
        """, [ev['ticker'], ev['event_date']]).fetchone()
        
        if p_start and p_end and p_start[0] > 0:
            ret = (p_end[0] - p_start[0]) / p_start[0]
            short_return += ret
            count += 1
    
    if count >= 2:
        period_return = (long_return - short_return) / count
        portfolio_returns.append({
            'period': period,
            'return': period_return,
            'positions': len(events)
        })

if portfolio_returns:
    df = pd.DataFrame(portfolio_returns)
    returns = df['return'].values
    
    # Annualized metrics
    sharpe = np.sqrt(12) * np.mean(returns) / (np.std(returns) + 1e-10)
    hit_rate = np.mean(returns > 0) * 100
    
    # Cumulative return
    cumulative = np.cumprod(1 + returns) - 1
    
    print(f"\n{'='*60}")
    print(f"PROPER PORTFOLIO BACKTEST")
    print(f"{'='*60}")
    print(f"Periods: {len(df)}")
    print(f"Avg positions per period: {df['positions'].mean():.0f}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Hit Rate: {hit_rate:.1f}%")
    print(f"Mean Return: {np.mean(returns)*100:.2f}%")
    print(f"Volatility: {np.std(returns)*100:.2f}%")
    print(f"Total Return: {cumulative[-1]*100:.2f}%")
    print(f"\nPer period:")
    for _, row in df.iterrows():
        emoji = '🟢' if row['return'] > 0 else '🔴'
        print(f"  {emoji} {row['period']}: {row['return']*100:+.2f}% ({row['positions']} positions)")
    
    print(f"\n{'='*60}")
    if sharpe > 0.8:
        print(f"✅ Sharpe {sharpe:.2f} > 0.8 — Institutional threshold met")
    elif sharpe > 0.3:
        print(f"⚠️ Sharpe {sharpe:.2f} — Promising, needs more data")
    else:
        print(f"❌ Sharpe {sharpe:.2f} — Below threshold")
    print(f"{'='*60}")

conn.close()