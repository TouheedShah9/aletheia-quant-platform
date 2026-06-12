"""
Alpaca Data Fetcher — Runs independently, writes to JSON
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ALPACA_KEY = os.getenv('ALPACA_API_KEY', '')
ALPACA_SECRET = os.getenv('ALPACA_SECRET_KEY', '')
BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

def fetch_alpaca_data():
    try:
        from alpaca_trade_api import REST
        base = BASE_URL.replace('/v2', '').rstrip('/')
        api = REST(ALPACA_KEY, ALPACA_SECRET, base)

        account = api.get_account()
        positions = api.list_positions()

        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'equity': float(account.equity),
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'pnl_today': float(account.equity) - float(account.last_equity),
            'portfolio_value': float(account.portfolio_value),
            'positions': []
        }

        for p in positions:
            try:
                pl_pct = float(p.unrealized_pl) / float(p.cost_basis) * 100 if float(p.cost_basis) != 0 else 0
            except:
                pl_pct = 0

            try:
                change = float(p.change_today) * 100
            except:
                change = 0

            data['positions'].append({
                'symbol': p.symbol,
                'qty': int(float(p.qty)),
                'market_value': float(p.market_value),
                'avg_entry': float(p.avg_entry_price),
                'current_price': float(p.current_price),
                'unrealized_pl': float(p.unrealized_pl),
                'unrealized_pl_pct': round(pl_pct, 2),
                'change_today': round(change, 2)
            })

        return data
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}

if __name__ == "__main__":
    data = fetch_alpaca_data()
    output_path = Path(__file__).parent.parent / 'alpaca_data.json'

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    if 'error' not in data:
        print(f"✅ Alpaca: ${data['equity']:,.2f} equity | {len(data['positions'])} positions | P&L: ${data['pnl_today']:+,.2f}")
    else:
        print(f"❌ Alpaca error: {data['error']}")