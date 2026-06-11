"""
Paper Trader - Executes trades on Alpaca Paper Trading
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

ALPACA_KEY = os.getenv('ALPACA_API_KEY', '')
ALPACA_SECRET = os.getenv('ALPACA_SECRET_KEY', '')
ALPACA_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

SIMULATION = False
api = None

if not ALPACA_KEY or not ALPACA_SECRET:
    logger.warning("Alpaca keys missing. Running simulation.")
    SIMULATION = True
else:
    try:
        from alpaca_trade_api import REST
        base = ALPACA_URL.replace('/v2', '').rstrip('/')
        api = REST(ALPACA_KEY, ALPACA_SECRET, base)
        account = api.get_account()
        logger.info(f"Alpaca connected. Cash: ${float(account.cash):,.2f}")
    except Exception as e:
        logger.error(f"Alpaca error: {e}")
        SIMULATION = True


class PaperTrader:
    def __init__(self, capital=100000):
        self.capital = capital
        self.orders = []

    def get_portfolio(self):
        from portfolio.constructor import PortfolioConstructor
        return PortfolioConstructor(capital=self.capital).build_portfolio()

    def execute(self):
        target = self.get_portfolio()
        if not target:
            return

        mode = 'ALPACA PAPER' if not SIMULATION else 'SIMULATION'
        print(f"\n{'='*50}")
        print(f"EXECUTING — {mode}")
        print(f"{'='*50}")

        for pos in target:
            if SIMULATION:
                print(f"  [SIM] {pos['side']:5s} {pos['ticker']:5s} {pos['shares']}sh @ ${pos['price']:.2f}")
                self.orders.append(pos)
            else:
                try:
                    side = 'buy' if pos['side'] == 'LONG' else 'sell'
                    order = api.submit_order(
                        symbol=pos['ticker'], qty=pos['shares'],
                        side=side, type='market', time_in_force='day'
                    )
                    print(f"  ✅ {pos['side']:5s} {pos['ticker']:5s} {pos['shares']}sh — ID: {order.id}")
                    self.orders.append(pos)
                except Exception as e:
                    print(f"  ❌ {pos['ticker']}: {e}")

        placed = len(self.orders)
        print(f"\n{placed} orders placed")
        if not SIMULATION:
            try:
                acc = api.get_account()
                print(f"Equity: ${float(acc.equity):,.2f} | Cash: ${float(acc.cash):,.2f}")
            except:
                pass


if __name__ == "__main__":
    print(f"\nPROJECT ALETHEIA — PAPER TRADER")
    print(f"Keys: {'✅' if ALPACA_KEY else '❌'} | Mode: {'LIVE PAPER' if not SIMULATION else 'SIMULATION'}")
    PaperTrader(100000).execute()