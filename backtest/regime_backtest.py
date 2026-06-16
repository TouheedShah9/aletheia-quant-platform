"""
Regime-Specific Backtest — Bull vs Bear vs Sideways
Uses total monthly SPY returns for regime classification
"""
import duckdb, numpy as np, pandas as pd
from collections import defaultdict

conn = duckdb.connect('aletheia.db')

# Get all events with returns
data = conn.execute("""
    SELECT t.ticker, t.event_date, AVG(e.tcs_score) as ens_score
    FROM transcripts_metadata t
    JOIN ens_scores e ON t.id = e.transcript_id
    WHERE e.id LIKE 'finbert_%'
    AND t.event_date IS NOT NULL
    GROUP BY t.ticker, t.event_date
    ORDER BY t.event_date
""").fetchall()

# Get SPY prices for regime detection
spy = conn.execute("SELECT trade_date, adj_close FROM price_data WHERE ticker='SPY' ORDER BY trade_date").fetchall()

# Get first and last price of each month for total monthly return
monthly_prices = {}
for trade_date, adj_close in spy:
    period = str(trade_date)[:7]
    if period not in monthly_prices:
        monthly_prices[period] = {'first': adj_close, 'last': adj_close}
    else:
        monthly_prices[period]['last'] = adj_close

# Classify based on total monthly return
regimes = {}
bull_count = 0
bear_count = 0
sideways_count = 0

for period, prices in sorted(monthly_prices.items()):
    if prices['first'] > 0:
        monthly_ret = (prices['last'] - prices['first']) / prices['first']
        if monthly_ret > 0.02:
            regimes[period] = 'BULL'
            bull_count += 1
        elif monthly_ret < -0.02:
            regimes[period] = 'BEAR'
            bear_count += 1
        else:
            regimes[period] = 'SIDEWAYS'
            sideways_count += 1

print(f"Regime Distribution: {bull_count} BULL, {bear_count} BEAR, {sideways_count} SIDEWAYS")
for period, regime in sorted(regimes.items()):
    if regime != 'SIDEWAYS':
        ret = (monthly_prices[period]['last'] - monthly_prices[period]['first']) / monthly_prices[period]['first']
        emoji = '🟢' if regime == 'BULL' else '🔴'
        print(f"  {emoji} {period}: {regime} ({ret*100:+.1f}%)")

# Group events by period and regime
periods = defaultdict(list)

for ticker, event_date, score in data:
    period = str(event_date)[:7]
    
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
        regime = regimes.get(period, 'SIDEWAYS')
        periods[period].append({
            'ticker': ticker,
            'ens_score': score,
            'forward_return': fwd_return,
            'regime': regime
        })

# Run backtest per regime
results = {}

for regime_name in ['BULL', 'BEAR', 'SIDEWAYS']:
    regime_returns = []
    regime_ens = []
    regime_fwd = []
    period_count = 0
    
    for period, events in sorted(periods.items()):
        regime_events = [e for e in events if e['regime'] == regime_name]
        if len(regime_events) < 5:
            continue
        
        period_count += 1
        events_sorted = sorted(regime_events, key=lambda x: x['ens_score'], reverse=True)
        
        n = len(events_sorted)
        cutoff = max(1, int(n * 0.3))
        longs = events_sorted[:cutoff]
        shorts = events_sorted[-cutoff:]
        
        long_ret = np.mean([e['forward_return'] for e in longs])
        short_ret = np.mean([e['forward_return'] for e in shorts])
        period_return = long_ret - short_ret
        regime_returns.append(period_return)
        
        regime_ens.extend([e['ens_score'] for e in longs + shorts])
        regime_fwd.extend([e['forward_return'] for e in longs] + [-e['forward_return'] for e in shorts])
    
    if len(regime_returns) >= 2:
        rets = np.array(regime_returns)
        sharpe = np.sqrt(12) * np.mean(rets) / (np.std(rets) + 1e-10)
        hit_rate = np.mean(rets > 0) * 100
        ic = np.corrcoef(regime_ens, regime_fwd)[0, 1] if len(regime_ens) > 1 else 0
        
        results[regime_name] = {
            'periods': period_count,
            'sharpe': round(sharpe, 2),
            'hit_rate': round(hit_rate, 1),
            'ic': round(ic, 4),
            'mean_ret': round(np.mean(rets) * 100, 2),
            'total_ret': round((np.cumprod(1 + rets)[-1] - 1) * 100, 1)
        }

print(f"\n{'='*60}")
print(f"REGIME-SPECIFIC BACKTEST RESULTS")
print(f"{'='*60}")

all_pass = True
for regime, metrics in results.items():
    emoji = '🟢' if regime == 'BULL' else ('🔴' if regime == 'BEAR' else '⚪')
    print(f"\n{emoji} {regime} MARKET")
    print(f"   Periods: {metrics['periods']}")
    print(f"   Sharpe: {metrics['sharpe']:.2f}")
    print(f"   Hit Rate: {metrics['hit_rate']:.1f}%")
    print(f"   IC: {metrics['ic']:.4f}")
    print(f"   Mean Return: {metrics['mean_ret']:+.2f}%/period")
    print(f"   Total Return: {metrics['total_ret']:+.1f}%")
    
    passed = metrics['hit_rate'] >= 50 and metrics['periods'] >= 2
    print(f"   Viable: {'✅' if passed else '❌'}")
    if not passed:
        all_pass = False

print(f"\n{'='*60}")
if all_pass:
    print(f"✅ REGIME STABILITY CONFIRMED — Signal works across all 3 regimes")
elif len(results) >= 2:
    print(f"⚠️ PARTIAL STABILITY — Signal works in {sum(1 for m in results.values() if m['hit_rate']>=50)}/{len(results)} regimes")
else:
    print(f"❌ INSUFFICIENT DATA — Need more events across different market conditions")
print(f"{'='*60}")

conn.close()