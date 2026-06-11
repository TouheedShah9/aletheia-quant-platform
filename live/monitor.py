"""
Live Monitor - Daily health checks, P&L, risk alerts
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

ALPACA_KEY = os.getenv('ALPACA_API_KEY', '')
ALPACA_SECRET = os.getenv('ALPACA_SECRET_KEY', '')
ALPACA_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')


class Monitor:
    def __init__(self):
        self.api = None
        if ALPACA_KEY and ALPACA_SECRET:
            try:
                from alpaca_trade_api import REST
                base = ALPACA_URL.replace('/v2', '').rstrip('/')
                self.api = REST(ALPACA_KEY, ALPACA_SECRET, base)
            except:
                pass

    def check(self):
        print(f"\n{'='*50}")
        print(f"PROJECT ALETHEIA — DAILY MONITOR")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*50}")

        checks = {}

        # 1. Alpaca connection
        if self.api:
            try:
                acc = self.api.get_account()
                equity = float(acc.equity)
                cash = float(acc.cash)
                buying_power = float(acc.buying_power)
                pnl_today = equity - float(acc.last_equity)

                print(f"\n[ACCOUNT]")
                print(f"  Equity:      ${equity:,.2f}")
                print(f"  Cash:        ${cash:,.2f}")
                print(f"  Buying Power:${buying_power:,.2f}")
                print(f"  P&L Today:   ${pnl_today:,.2f}")
                checks['account'] = 'OK'
            except Exception as e:
                print(f"  ❌ Alpaca error: {e}")
                checks['account'] = 'ERROR'
        else:
            print(f"\n[ACCOUNT] Simulation mode")
            checks['account'] = 'SIMULATION'

        # 2. Positions
        if self.api:
            try:
                positions = self.api.list_positions()
                print(f"\n[POSITIONS] {len(positions)} open")
                for pos in positions[:5]:
                    pnl = float(pos.unrealized_pl)
                    emoji = '🟢' if pnl > 0 else '🔴'
                    print(f"  {emoji} {pos.symbol:5s} {pos.qty}sh | P&L: ${pnl:,.2f}")
                checks['positions'] = len(positions)
            except Exception as e:
                print(f"  ❌ Error: {e}")
                checks['positions'] = 'ERROR'

        # 3. Database health
        try:
            import duckdb
            conn = duckdb.connect('aletheia.db')
            tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
            print(f"\n[DATABASE] {len(tables)} tables OK")
            conn.close()
            checks['database'] = 'OK'
        except Exception as e:
            print(f"\n[DATABASE] ❌ {e}")
            checks['database'] = 'ERROR'

        # 4. Recent signals
        try:
            import duckdb
            conn = duckdb.connect('aletheia.db')
            sigs = conn.execute("SELECT COUNT(*) FROM composite_signals").fetchone()[0]
            ens = conn.execute("SELECT COUNT(*) FROM ens_scores WHERE id LIKE 'real_%'").fetchone()[0]
            print(f"\n[SIGNALS]")
            print(f"  Composite: {sigs}")
            print(f"  Real ENS:  {ens}")
            conn.close()
            checks['signals'] = f'{sigs} composite, {ens} real'
        except:
            checks['signals'] = 'ERROR'

        # Summary
        print(f"\n{'='*50}")
        print(f"HEALTH CHECK")
        for check, status in checks.items():
            icon = '✅' if status == 'OK' or isinstance(status, int) else ('⚠️' if status == 'SIMULATION' else '❌')
            print(f"  {icon} {check}: {status}")
        print(f"{'='*50}")


if __name__ == "__main__":
    Monitor().check()