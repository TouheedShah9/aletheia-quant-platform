"""
Calibrated Backtest — Uses actual return data to set LONG/SHORT thresholds
Instead of fixed >0.05 / <-0.05, uses percentile-based ranking
Top quintile = LONG, Bottom quintile = SHORT
"""
import duckdb, numpy as np, pandas as pd
from collections import defaultdict

conn = duckdb.connect('aletheia.db')

# Get ALL individual transcript scores with returns
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

# Group by month
periods = defaultdict(list)

for ticker, event_date, score in data:
    period = str(event_date)[:7]
    
    # Get forward return
    p_start = conn.execute("""
        SELECT adj_close FROM price_data
        WHERE ticker = ? AND trade_date >= ?
        ORDER BY trade_date LIMIT 1
    """, [ticker, str(event_date)]).fetchone()
    
    p_end = conn.execute("""
        SELECT adj_close FROM price_data
        WHERE ticker = ? AND trade_date >= ?
        ORDER BY trade_date LIMIT 1 OFFSET 20
    """, [ticker, str(event_date)]).fetchone()
    
    if p_start and p_end and p_start[0] > 0:
        fwd_return = (p_end[0] - p_start[0]) / p_start[0]
        periods[period].append({
            'ticker': ticker,
            'ens_score': score,
            'forward_return': fwd_return
        })

# For each period: rank by ENS, long top 30%, short bottom 30%
portfolio_returns = []
all_ens = []
all_returns = []

for period, events in sorted(periods.items()):
    if len(events) < 5:
        continue
    
    # Sort by ENS score
    events_sorted = sorted(events, key=lambda x: x['ens_score'], reverse=True)
    
    # Top 30% = long, bottom 30% = short
    n = len(events_sorted)
    cutoff = max(1, int(n * 0.3))
    
    longs = events_sorted[:cutoff]
    shorts = events_sorted[-cutoff:]
    
    long_ret = np.mean([e['forward_return'] for e in longs])
    short_ret = np.mean([e['forward_return'] for e in shorts])
    
    period_return = long_ret - short_ret
    portfolio_returns.append(period_return)
    
    all_ens.extend([e['ens_score'] for e in longs])
    all_ens.extend([e['ens_score'] for e in shorts])
    all_returns.extend([e['forward_return'] for e in longs])
    all_returns.extend([-e['forward_return'] for e in shorts])

returns = np.array(portfolio_returns)
sharpe = np.sqrt(12) * np.mean(returns) / (np.std(returns) + 1e-10)
hit_rate = np.mean(returns > 0) * 100
ic = np.corrcoef(all_ens, all_returns)[0, 1] if len(all_ens) > 1 else 0

# Quintile analysis
all_events = []
for events in periods.values():
    all_events.extend(events)

df_all = pd.DataFrame(all_events)
df_all['quintile'] = pd.qcut(df_all['ens_score'], 5, labels=['Q1','Q2','Q3','Q4','Q5'], duplicates='drop')
quintile_returns = df_all.groupby('quintile')['forward_return'].mean()

print(f"\n{'='*60}")
print(f"CALIBRATED BACKTEST — Percentile-Based Long/Short")
print(f"{'='*60}")
print(f"Periods: {len(returns)}")
print(f"Avg events/period: {sum(len(e) for e in periods.values())//len(periods)}")
print(f"Sharpe: {sharpe:.2f}")
print(f"Hit Rate: {hit_rate:.1f}%")
print(f"IC: {ic:.4f}")
print(f"Mean Return: {np.mean(returns)*100:.2f}%/period")
print(f"Cumulative: {(np.cumprod(1+returns)[-1]-1)*100:.1f}%")

print(f"\nQuintile Analysis:")
for q, r in quintile_returns.items():
    bar = '█' * int(abs(r)*500)
    print(f"  {q}: {r*100:+5.2f}% {bar}")
spread = quintile_returns.iloc[-1] - quintile_returns.iloc[0]
print(f"  Q5-Q1 Spread: {spread*100:.2f}%")

print(f"\nPer Period:")
for i, (period, ret) in enumerate(zip(sorted(periods.keys()), returns)):
    if i >= len(returns): break
    emoji = '🟢' if ret > 0 else '🔴'
    print(f"  {emoji} {period}: {ret*100:+.2f}%")

print(f"\n{'='*60}")
if sharpe > 0.8:
    print(f"✅ Sharpe {sharpe:.2f} > 0.8 — Institutional threshold met")
elif sharpe > 0.3:
    print(f"⚠️ Sharpe {sharpe:.2f} — Promising, needs more differentiation")
else:
    print(f"❌ Sharpe {sharpe:.2f} — Below threshold. Quintile spread={spread*100:.2f}%")
print(f"{'='*60}")

conn.close()