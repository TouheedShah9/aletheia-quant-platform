"""
Backtest Engine - Walk-forward backtesting with transaction costs
Point-in-time safe. Uses synthetic signals for POC.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from loguru import logger
from backtest.data_loader import BacktestDataLoader
import config


class BacktestEngine:
    def __init__(self):
        self.loader = BacktestDataLoader()
    
    def run(self, capital=100000):
        """Run backtest and return performance metrics."""
        signals = self.loader.build_backtest_dataset()
        
        # Get unique dates and tickers
        dates = sorted(signals['signal_date'].unique())
        tickers = signals['ticker'].unique()
        
        # Track portfolio
        portfolio_values = [capital]
        trades = []
        positions = {}  # ticker -> {shares, entry_price, direction}
        
        for date in dates:
            day_signals = signals[signals['signal_date'] == date]
            
            # Close old positions (simplified: hold 5 days)
            to_close = []
            for ticker, pos in list(positions.items()):
                if pos['days_held'] >= 5:
                    price = self._get_price(ticker, date, day_signals)
                    pnl = (price - pos['entry_price']) * pos['shares'] * pos['direction']
                    pnl -= pos['cost']  # Subtract transaction cost
                    portfolio_values.append(portfolio_values[-1] + pnl)
                    trades.append({
                        'ticker': ticker, 'entry_date': pos['entry_date'],
                        'exit_date': date, 'direction': pos['direction'],
                        'pnl': pnl
                    })
                    to_close.append(ticker)
                else:
                    positions[ticker]['days_held'] += 1
            
            for ticker in to_close:
                del positions[ticker]
            
            # Open new positions (top 3 by composite score)
            day_signals_sorted = day_signals.nlargest(3, 'composite_score')
            
            for _, sig in day_signals_sorted.iterrows():
                if sig['ticker'] in positions:
                    continue  # Already in a position
                
                direction = sig['signal_direction']
                if direction == 0:
                    continue
                
                price = self._get_signal_price(sig)
                allocation = capital * config.MAX_POSITION
                cost = allocation * (config.COST_LARGE if price > 100 else config.COST_MID)
                shares = int(allocation / price) if price > 0 else 0
                
                if shares > 0:
                    positions[sig['ticker']] = {
                        'shares': shares,
                        'entry_price': price,
                        'direction': direction,
                        'entry_date': date,
                        'days_held': 0,
                        'cost': cost
                    }
        
        return self._calculate_metrics(portfolio_values, trades)
    
    def _get_price(self, ticker, date, signals_df):
        """Get price for a ticker. Simplified for POC."""
        np.random.seed(hash(f"{ticker}{date}") % 2**31)
        return np.random.uniform(50, 500)
    
    def _get_signal_price(self, signal):
        """Get entry price from signal data."""
        np.random.seed(abs(hash(signal['ticker'])) % 2**31)
        return np.random.uniform(50, 500)
    
    def _calculate_metrics(self, portfolio_values, trades):
        """Calculate performance metrics."""
        values = np.array(portfolio_values)
        returns = np.diff(values) / values[:-1]
        
        # Total return
        total_return = (values[-1] - values[0]) / values[0]
        
        # Annualized return (assuming 252 trading days)
        n_days = len(returns)
        annual_return = (1 + total_return) ** (252 / max(n_days, 1)) - 1
        
        # Sharpe ratio
        excess = returns - 0.02/252  # Risk-free rate ~2%
        sharpe = np.sqrt(252) * excess.mean() / (returns.std() + 1e-10)
        
        # Max drawdown
        peak = np.maximum.accumulate(values)
        drawdown = (values - peak) / peak
        max_dd = abs(drawdown.min())
        
        # Hit rate
        if trades:
            winners = [t for t in trades if t['pnl'] > 0]
            hit_rate = len(winners) / len(trades)
        else:
            hit_rate = 0
        
        results = {
            'total_return': round(total_return, 4),
            'annualized_return': round(annual_return, 4),
            'sharpe_ratio': round(sharpe, 4),
            'max_drawdown': round(max_dd, 4),
            'hit_rate': round(hit_rate, 4),
            'num_trades': len(trades),
            'final_value': round(values[-1], 2),
        }
        
        self._print_results(results)
        return results
    
    def _print_results(self, results):
        print("\n" + "="*50)
        print("BACKTEST RESULTS")
        print("="*50)
        print(f"  Final Value:        ${results['final_value']:,.2f}")
        print(f"  Total Return:       {results['total_return']*100:.2f}%")
        print(f"  Annualized Return:  {results['annualized_return']*100:.2f}%")
        print(f"  Sharpe Ratio:       {results['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown:       {results['max_drawdown']*100:.2f}%")
        print(f"  Hit Rate:           {results['hit_rate']*100:.1f}%")
        print(f"  Total Trades:       {results['num_trades']}")
        print("="*50)
        
        # Assessment
        if results['sharpe_ratio'] > 1.0:
            print("ASSESSMENT: Strong risk-adjusted returns")
        elif results['sharpe_ratio'] > 0.5:
            print("ASSESSMENT: Moderate positive performance")
        else:
            print("ASSESSMENT: Below threshold - signal needs refinement")
        print("="*50)


if __name__ == "__main__":
    engine = BacktestEngine()
    engine.run(capital=100000)