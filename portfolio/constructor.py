"""
Portfolio Constructor - Production-grade position sizing
Converts composite signals into actual dollar allocations
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
from loguru import logger
import config


class PortfolioConstructor:
    def __init__(self, db_path="aletheia.db", capital=100000.0):
        self.db_path = db_path
        self.capital = capital
        self.conn = duckdb.connect(db_path)
        self.sectors = {
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'AMZN': 'Consumer Cyclical', 'META': 'Technology',
            'JPM': 'Financial', 'BAC': 'Financial', 'GS': 'Financial',
            'JNJ': 'Healthcare', 'PFE': 'Healthcare',
            'XOM': 'Energy', 'CVX': 'Energy',
            'HD': 'Consumer Cyclical', 'WMT': 'Consumer Defensive',
            'MCD': 'Consumer Cyclical'
        }

    def get_signals(self):
        return self.conn.execute("""
            SELECT ticker, composite_score, signal_direction
            FROM composite_signals
            ORDER BY ABS(composite_score) DESC
        """).fetchall()

    def calculate_position_size(self, zscore, current_dd):
        strength = min(abs(zscore) / 0.5, 1.0)
        raw_size = strength * config.MAX_POSITION
        if current_dd > config.DRAWDOWN_BREAKER:
            raw_size *= config.POSITION_REDUCTION_ON_BREACH
            logger.warning(f"CIRCUIT BREAKER: DD {current_dd*100:.1f}% > {config.DRAWDOWN_BREAKER*100:.0f}%")
        return round(raw_size, 4)

    def get_price(self, ticker):
        p = self.conn.execute("""
            SELECT adj_close FROM price_data
            WHERE ticker = ? ORDER BY trade_date DESC LIMIT 1
        """, [ticker]).fetchone()
        return p[0] if p else 100.0

    def build_portfolio(self):
        signals = self.get_signals()
        if not signals:
            logger.error("No signals available")
            return []

        current_dd = 0.0
        breaker = current_dd > config.DRAWDOWN_BREAKER

        print(f"\n{'='*55}")
        print(f"PORTFOLIO CONSTRUCTION — ${self.capital:,.0f}")
        print(f"{'='*55}")
        print(f"Drawdown: {current_dd*100:.1f}% | Breaker: {'ON ⚠️' if breaker else 'OFF ✅'}")
        print(f"{'='*55}")

        positions = []
        sector_exp = {}
        allocated = 0.0

        for ticker, score, direction in signals:
            if direction == 0:
                continue

            size = self.calculate_position_size(score, current_dd)
            if size <= 0.001:
                continue

            sector = self.sectors.get(ticker, 'Unknown')
            curr_sec = sector_exp.get(sector, 0.0)
            if curr_sec + size > config.MAX_SECTOR_EXPOSURE:
                size = max(0, config.MAX_SECTOR_EXPOSURE - curr_sec)
                if size <= 0.001:
                    continue

            price = self.get_price(ticker)
            if price <= 0:
                continue

            alloc = size * self.capital
            shares = int(alloc / price)
            if shares <= 0:
                continue

            cost_rate = config.COST_LARGE if price > 100 else config.COST_MID
            cost = alloc * cost_rate * 2

            if allocated + alloc > self.capital:
                continue

            side = 'LONG' if direction == 1 else 'SHORT'
            positions.append({
                'ticker': ticker, 'sector': sector, 'side': side,
                'size_pct': round(size*100, 2), 'allocation': round(alloc, 2),
                'shares': shares, 'price': price, 'cost': round(cost, 2)
            })
            sector_exp[sector] = curr_sec + size
            allocated += alloc

            e = '🟢' if direction == 1 else '🔴'
            print(f"{e} {ticker:5s} {side:5s} {size*100:5.1f}% ${alloc:,.0f} ({shares} sh @ ${price:.2f})")

        print(f"\n{'='*55}")
        print(f"SUMMARY: {len(positions)} positions | ${allocated:,.0f} allocated ({allocated/self.capital*100:.1f}%) | ${self.capital-allocated:,.0f} cash")
        print(f"Sector: " + ', '.join(f"{s}:{e*100:.1f}%" for s,e in sector_exp.items()))
        print(f"{'='*55}")

        self.conn.close()
        return positions


if __name__ == "__main__":
    p = PortfolioConstructor(capital=100000).build_portfolio()
    print("✅ Ready" if p else "⚠️ No positions")