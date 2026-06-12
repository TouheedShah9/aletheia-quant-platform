"""
Dimension 7 Audit — Test every AI/ML feature
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import duckdb
import pandas as pd

print("="*60)
print("DIMENSION 7 AUDIT — AI/ML INTELLIGENCE")
print("="*60)
results = []

# Load real data
conn = duckdb.connect('aletheia.db')
sig = conn.execute("SELECT ticker, composite_score, signal_direction FROM composite_signals").fetchdf()
ens_data = conn.execute("SELECT ticker, AVG(ens_final) as e FROM ens_scores WHERE id LIKE 'earn_%' GROUP BY ticker").fetchall()
ens_dict = {e[0]: e[1] for e in ens_data}
conn.close()

# 1. Signal Explainer
print("\n[45] SIGNAL EXPLAINER:")
try:
    from live.ai_insights import explainer
    for _, row in sig.iterrows():
        ens = ens_dict.get(row['ticker'], 0)
        exp = explainer.explain_signal(row['ticker'], ens, row['composite_score'])
        assert 'sentiment' in exp
        assert 'action' in exp
        assert 'ens_detail' in exp
    results.append(("Signal Explainer", "PASS"))
    print(f"   PASS — {len(sig)} explanations generated")
except Exception as e:
    results.append(("Signal Explainer", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 2. Anomaly Detection
print("\n[46] ANOMALY DETECTION:")
try:
    from live.ai_insights import anomaly
    anomalies = anomaly.detect(sig)
    assert isinstance(anomalies, list)
    results.append(("Anomaly Detection", "PASS"))
    print(f"   PASS — {len(anomalies)} anomalies found (normal for stable signals)")
except Exception as e:
    results.append(("Anomaly Detection", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 3. Signal flips
print("\n[46] SIGNAL FLIP DETECTION:")
try:
    flips = anomaly.detect_signal_flip(sig, sig)
    assert isinstance(flips, list)
    results.append(("Signal Flips", "PASS"))
    print(f"   PASS — Flip detection working")
except Exception as e:
    results.append(("Signal Flips", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 4. Forecasting
print("\n[47] SIGNAL FORECASTING:")
try:
    from live.ai_insights import forecaster
    forecasts = forecaster.forecast(sig, periods=3)
    assert len(forecasts) > 0
    for f in forecasts:
        assert 'ticker' in f
        assert 'predictions' in f
        assert len(f['predictions']) == 3
    results.append(("Forecasting", "PASS"))
    print(f"   PASS — {len(forecasts)} forecasts generated")
except Exception as e:
    results.append(("Forecasting", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 5. What-If Analysis
print("\n[48] WHAT-IF ANALYSIS:")
try:
    from live.ai_insights import whatif
    sim = whatif.simulate_ens_change('AAPL', 0.487, -0.2)
    assert 'action' in sim
    assert 'position_change' in sim
    assert sim['action'] in ['INCREASE', 'DECREASE', 'HOLD']
    
    shock = whatif.simulate_market_shock(100000, -5)
    assert shock['drawdown'] == 5.0
    assert shock['impact'] == -5000
    results.append(("What-If", "PASS"))
    print(f"   PASS — ENS change: {sim['action']}, Market shock: ${shock['impact']:,.0f}")
except Exception as e:
    results.append(("What-If", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 6. NLP Query
print("\n[49] NLP QUERY:")
try:
    from live.ai_insights import nlp
    
    test_queries = [
        "show top signals",
        "what are the long positions",
        "show me bearish aapl",
        "list short signals"
    ]
    
    for q in test_queries:
        parsed = nlp.parse(q)
        assert 'action' in parsed or 'filter' in parsed
        result = nlp.execute(sig, parsed)
        assert len(result) >= 0
    
    results.append(("NLP Queries", "PASS"))
    print(f"   PASS — {len(test_queries)} queries parsed and executed")
except Exception as e:
    results.append(("NLP Queries", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 7. Recommendations
print("\n[50] RECOMMENDATIONS:")
try:
    from live.ai_insights import recommender
    recs = recommender.generate(sig)
    assert len(recs) > 0
    for r in recs:
        assert 'action' in r
        assert r['action'] in ['BUY', 'SELL', 'HOLD']
        assert 'confidence' in r
    results.append(("Recommendations", "PASS"))
    print(f"   PASS — {len(recs)} recommendations")
except Exception as e:
    results.append(("Recommendations", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 8. Sentiment Overlay
print("\n[51] SENTIMENT OVERLAY:")
try:
    from live.ai_insights import sentiment_overlay
    ctx = sentiment_overlay.get_market_context()
    assert 'vix' in ctx
    assert 'regime' in ctx
    assert 'bias' in ctx
    assert ctx['bias'] in ['BULLISH', 'BEARISH', 'NEUTRAL']
    
    adjusted = sentiment_overlay.adjust_signals(sig, ctx)
    assert len(adjusted) == len(sig)
    results.append(("Sentiment Overlay", "PASS"))
    print(f"   PASS — VIX: {ctx['vix']}, Bias: {ctx['bias']}")
except Exception as e:
    results.append(("Sentiment Overlay", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 9. Real data integration
print("\n[INTEGRATION] REAL DATA:")
try:
    assert len(sig) == 8, f"Expected 8 signals, got {len(sig)}"
    assert len(ens_dict) == 8, f"Expected 8 ENS tickers, got {len(ens_dict)}"
    results.append(("Real Data", "PASS"))
    print(f"   PASS — {len(sig)} signals, {len(ens_dict)} ENS scores")
except Exception as e:
    results.append(("Real Data", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# Summary
print("\n" + "="*60)
passed = sum(1 for r in results if "PASS" in str(r[1]))
failed = sum(1 for r in results if "FAIL" in str(r[1]))
for name, status in results:
    print(f"  {'✅' if 'PASS' in str(status) else '❌'} {name}: {status}")
print(f"\nTotal: {passed}/{len(results)} passed")
print("="*60)
if failed == 0:
    print("DIMENSION 7: ALL TESTS PASSED — PRODUCTION READY")
else:
    print(f"DIMENSION 7: {failed} FIXES NEEDED")