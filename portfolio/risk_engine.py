"""
Risk Engine - VaR, Expected Shortfall, Drawdown Monitor
Production-grade risk management
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from loguru import logger
import config


class RiskEngine:
    def __init__(self):
        self.var_window = 250
        self.var_confidence = 0.95

    def calculate_var(self, returns):
        if len(returns) < 10:
            return 0.02
        return abs(np.percentile(returns, (1 - self.var_confidence) * 100))

    def calculate_es(self, returns):
        var = self.calculate_var(returns)
        beyond = [r for r in returns if r < -var]
        return abs(np.mean(beyond)) if beyond else var * 1.5

    def calculate_drawdown(self, values):
        peak = np.maximum.accumulate(values)
        dd = (values - peak) / peak
        return abs(dd.min()), abs(dd[-1])

    def check_limits(self, portfolio_value, pnl_history):
        values = np.array(pnl_history + [portfolio_value])
        returns = np.diff(values) / values[:-1] if len(values) > 1 else np.array([0])

        var = self.calculate_var(returns)
        es = self.calculate_es(returns)
        max_dd, current_dd = self.calculate_drawdown(values)

        breaker = current_dd > config.DRAWDOWN_BREAKER

        print(f"\n{'='*45}")
        print(f"RISK REPORT")
        print(f"{'='*45}")
        print(f"Portfolio:    ${portfolio_value:,.2f}")
        print(f"VaR (95%):    {var*100:.2f}%")
        print(f"Exp Shortfall:{es*100:.2f}%")
        print(f"Max DD:       {max_dd*100:.2f}%")
        print(f"Current DD:   {current_dd*100:.2f}%")
        print(f"DD Limit:     {config.DRAWDOWN_BREAKER*100:.0f}%")
        print(f"Breaker:      {'TRIPPED ⚠️' if breaker else 'OK ✅'}")
        print(f"{'='*45}")

        return {
            'var': round(var, 4), 'es': round(es, 4),
            'max_dd': round(max_dd, 4), 'current_dd': round(current_dd, 4),
            'breaker': breaker
        }


if __name__ == "__main__":
    engine = RiskEngine()
    sample_values = [100000, 101000, 102000, 100500, 99500, 100200, 103000]
    engine.check_limits(103000, sample_values[:-1])