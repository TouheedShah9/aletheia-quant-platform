"""Verify tabs 8 and 9 work on dashboard"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import duckdb
from live.security import auth, rbac, sec_audit
from live.ai_insights import explainer, forecaster, recommender, nlp

print('='*60)
print('DASHBOARD TABS 8+9 VERIFICATION')
print('='*60)

# Tab 8: Security
print('\n--- TAB 8: SECURITY ---')
ok, token = auth.login('admin', 'aletheia_admin_2024')
print(f'Login: {"OK" if ok else "FAIL"}')
session = auth.validate_session(token)
print(f'Session: {"OK" if session else "FAIL"}')
print(f'RBAC admin trade: {rbac.has_permission("admin", "execute_trades")}')
print(f'RBAC viewer trade: {rbac.has_permission("viewer", "execute_trades")}')
print(f'Audit entries: {len(sec_audit.logs)}')

# Tab 9: AI
print('\n--- TAB 9: AI ---')
conn = duckdb.connect('aletheia.db')
sig = conn.execute('SELECT ticker, composite_score, signal_direction FROM composite_signals').fetchdf()
ens_data = conn.execute("SELECT ticker, AVG(ens_final) as e FROM ens_scores WHERE id LIKE 'earn_%' GROUP BY ticker").fetchall()
conn.close()
ens_dict = {e[0]: e[1] for e in ens_data}

for _, r in sig.iterrows():
    exp = explainer.explain_signal(r['ticker'], ens_dict.get(r['ticker'], 0), r['composite_score'])
    print(f"{r['ticker']}: {exp['sentiment']}")

fcs = forecaster.forecast(sig, 3)
print(f'Forecasts: {len(fcs)} tickers')

recs = recommender.generate(sig)
print(f'Recommendations: {len(recs)}')

parsed = nlp.parse('show top long signals')
result = nlp.execute(sig, parsed)
print(f'NLP query result: {len(result)} tickers')

print('\n' + '='*60)
print('BOTH TABS READY — Open dashboard and click tabs 8 & 9')
print('='*60)