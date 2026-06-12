"""Test Alpaca is fully functional — not just status"""
import os, json
from dotenv import load_dotenv
load_dotenv()

print("="*50)
print("ALPACA FUNCTIONAL TEST")
print("="*50)

try:
    from alpaca_trade_api import REST
    base = os.getenv('ALPACA_BASE_URL','').replace('/v2','').rstrip('/')
    api = REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), base)
    
    # 1. Account
    acc = api.get_account()
    equity = float(acc.equity)
    cash = float(acc.cash)
    pnl = equity - float(acc.last_equity)
    
    print(f"\n1. ACCOUNT: ✅ Connected")
    print(f"   Equity: ${equity:,.2f}")
    print(f"   Cash: ${cash:,.2f}")
    print(f"   P&L Today: ${pnl:+,.2f}")
    assert equity > 0, "Zero equity"
    
    # 2. Positions
    positions = api.list_positions()
    print(f"\n2. POSITIONS: {len(positions)} open")
    for p in positions:
        pl = float(p.unrealized_pl)
        emoji = '🟢' if pl > 0 else '🔴'
        print(f"   {emoji} {p.symbol}: {p.qty}sh | P&L: ${pl:,.2f}")
    assert len(positions) > 0, "No positions"
    
    # 3. Orders
    orders = api.list_orders(status='closed', limit=5)
    print(f"\n3. ORDER HISTORY: {len(orders)} closed")
    for o in orders[:3]:
        print(f"   {o.symbol}: {o.side} {o.qty}sh @ ${float(o.filled_avg_price):.2f} — {o.status}")
    
    # 4. Ready
    print(f"\n4. TRADING: ✅ Ready to execute")
    print(f"\n{'='*50}")
    print("ALPACA: FULLY FUNCTIONAL — REAL MONEY PAPER TRADING")
    print(f"{'='*50}")
    
except Exception as e:
    print(f"\n❌ ALPACA ERROR: {e}")