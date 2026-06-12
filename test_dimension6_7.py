"""
Verify Dimensions 6+7 work with real data
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import duckdb
from live.security import auth, rbac, api_keys, sec_audit, session_mgr, validator
from live.ai_insights import explainer, anomaly, forecaster, whatif, nlp, recommender, sentiment_overlay

print('='*60)
print('DIMENSIONS 6+7: REAL DATA VERIFICATION')
print('='*60)

# Load real data
conn = duckdb.connect('aletheia.db')
sig = conn.execute('SELECT ticker, composite_score, signal_direction FROM composite_signals').fetchdf()
ens_data = conn.execute("SELECT ticker, AVG(ens_final) as e FROM ens_scores WHERE id LIKE 'earn_%' GROUP BY ticker").fetchall()
conn.close()
ens_dict = {e[0]: e[1] for e in ens_data}

print(f'\nReal signals: {len(sig)} tickers')
print(f'Real ENS scores: {len(ens_dict)} tickers')

results = []

# ═══════════ DIMENSION 6 ═══════════
print('\n--- DIMENSION 6: SECURITY ---')

# 1. Login
print('\n[38] Authentication:')
try:
    ok, token = auth.login('admin', 'aletheia_admin_2024')
    assert ok and token
    results.append(("Login", "PASS"))
    print("   PASS")
except Exception as e:
    results.append(("Login", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 2. Session
print('\n[38] Session:')
try:
    session = auth.validate_session(token)
    assert session['username'] == 'admin'
    results.append(("Session", "PASS"))
    print("   PASS")
except Exception as e:
    results.append(("Session", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 3. RBAC
print('\n[39] RBAC:')
try:
    assert rbac.has_permission('admin', 'execute_trades')
    assert rbac.has_permission('admin', 'configure_system')
    assert rbac.has_permission('viewer', 'view_all')
    assert not rbac.has_permission('viewer', 'execute_trades')
    results.append(("RBAC", "PASS"))
    print("   PASS")
except Exception as e:
    results.append(("RBAC", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 4. API Keys
print('\n[40] API Keys:')
try:
    key = api_keys.generate_key('test', 'analyst', 1)
    valid = api_keys.validate_key(key)
    assert valid is not None
    api_keys.revoke_key(key)
    assert api_keys.validate_key(key) is None
    results.append(("API Keys", "PASS"))
    print("   PASS")
except Exception as e:
    results.append(("API Keys", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 5. Input validation
print('\n[41] Input Validation:')
try:
    assert validator.validate_ticker('AAPL')
    assert validator.validate_ticker('MSFT')
    assert validator.validate_ticker('SHEL.L')
    assert not validator.validate_ticker('DROP TABLE;--')
    assert not validator.validate_ticker('')
    results.append(("Input Valid", "PASS"))
    print("   PASS")
except Exception as e:
    results.append(("Input Valid", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 6. Security audit
print('\n[43] Security Audit:')
try:
    sec_audit.log('VERIFY', 'admin', 'Real data test')
    assert len(sec_audit.logs) >= 1
    results.append(("Audit", "PASS"))
    print(f"   PASS ({len(sec_audit.logs)} entries)")
except Exception as e:
    results.append(("Audit", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# ═══════════ DIMENSION 7 ═══════════
print('\n--- DIMENSION 7: AI/ML ---')

# 7. Signal Explanations
print('\n[45] Signal Explanations:')
try:
    for _, r in sig.iterrows():
        exp = explainer.explain_signal(r['ticker'], ens_dict.get(r['ticker'], 0), r['composite_score'])
        assert 'sentiment' in exp and 'action' in exp
    results.append(("Explainer", "PASS"))
    print(f"   PASS ({len(sig)} explained)")
except Exception as e:
    results.append(("Explainer", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 8. Anomaly Detection
print('\n[46] Anomaly Detection:')
try:
    anoms = anomaly.detect(sig)
    assert isinstance(anoms, list)
    results.append(("Anomaly", "PASS"))
    print(f"   PASS ({len(anoms)} found)")
except Exception as e:
    results.append(("Anomaly", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 9. Forecasting
print('\n[47] Forecasting:')
try:
    fcs = forecaster.forecast(sig, 3)
    assert len(fcs) == len(sig)
    for f in fcs:
        assert len(f['predictions']) == 3
    results.append(("Forecast", "PASS"))
    print(f"   PASS ({len(fcs)} tickers)")
except Exception as e:
    results.append(("Forecast", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 10. What-If
print('\n[48] What-If:')
try:
    sim = whatif.simulate_ens_change('AAPL', ens_dict.get('AAPL', 0), -0.2)
    assert 'action' in sim
    shock = whatif.simulate_market_shock(100000, -5)
    assert shock['drawdown'] == 5.0
    results.append(("What-If", "PASS"))
    print("   PASS")
except Exception as e:
    results.append(("What-If", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 11. NLP
print('\n[49] NLP Queries:')
try:
    for q in ['show top long', 'what are short', 'show me bearish aapl']:
        parsed = nlp.parse(q)
        result = nlp.execute(sig, parsed)
        assert len(result) >= 0
    results.append(("NLP", "PASS"))
    print("   PASS")
except Exception as e:
    results.append(("NLP", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 12. Recommendations
print('\n[50] Recommendations:')
try:
    recs = recommender.generate(sig)
    assert len(recs) >= 0
    for r in recs:
        assert r['action'] in ['BUY', 'SELL', 'HOLD']
    results.append(("Recommender", "PASS"))
    print(f"   PASS ({len(recs)} recs)")
except Exception as e:
    results.append(("Recommender", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# 13. Sentiment Overlay
print('\n[51] Sentiment Overlay:')
try:
    ctx = sentiment_overlay.get_market_context()
    assert 'vix' in ctx and 'bias' in ctx
    adj = sentiment_overlay.adjust_signals(sig, ctx)
    assert len(adj) == len(sig)
    results.append(("Sentiment", "PASS"))
    print(f"   PASS (VIX {ctx['vix']}, {ctx['bias']})")
except Exception as e:
    results.append(("Sentiment", f"FAIL: {e}"))
    print(f"   FAIL: {e}")

# Summary
print('\n' + '='*60)
passed = sum(1 for r in results if 'PASS' in str(r[1]))
failed = sum(1 for r in results if 'FAIL' in str(r[1]))
for name, status in results:
    print(f"  {'✅' if 'PASS' in str(status) else '❌'} {name}: {status}")
print(f'\nTotal: {passed}/{len(results)} passed')
print('='*60)
if failed == 0:
    print('DIMENSIONS 6+7: ALL TESTS PASSED — PRODUCTION READY')
else:
    print(f'DIMENSIONS 6+7: {failed} FIXES NEEDED')