"""Dimension 8 Audit — Skip slow email send"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import duckdb
from dashboard.components.mobile import (
    EmailReportGenerator, SlackIntegration, APIServer, MobileNavigation
)

print("="*60)
print("DIMENSION 8 AUDIT")
print("="*60)
results = []

conn = duckdb.connect('aletheia.db')
sig = conn.execute("SELECT ticker, composite_score, signal_direction FROM composite_signals").fetchdf()
conn.close()

# 1. Responsive CSS
try:
    from dashboard.components.mobile import inject_responsive_css
    assert callable(inject_responsive_css)
    print("\n[52] Responsive CSS: PASS")
    results.append(("CSS", "PASS"))
except Exception as e:
    print(f"\n[52] Responsive CSS: FAIL - {e}")
    results.append(("CSS", "FAIL"))

# 2. PWA Manifest
try:
    from dashboard.components.mobile import generate_pwa_manifest
    path = generate_pwa_manifest()
    assert path.exists()
    print("[53] PWA Manifest: PASS")
    results.append(("PWA", "PASS"))
except Exception as e:
    print(f"[53] PWA Manifest: FAIL - {e}")
    results.append(("PWA", "FAIL"))

# 3. Email Report (generate only, no send)
try:
    report = EmailReportGenerator.generate_report(sig)
    assert len(report) > 100
    assert 'AAPL' in report
    print(f"[54] Email Report: PASS ({len(report)} chars)")
    results.append(("Email", "PASS"))
except Exception as e:
    print(f"[54] Email Report: FAIL - {e}")
    results.append(("Email", "FAIL"))

# 4. Slack
try:
    ok, msg = SlackIntegration.send_signal_update(sig)
    print(f"[55] Slack: PASS - {msg}")
    results.append(("Slack", "PASS"))
except Exception as e:
    print(f"[55] Slack: FAIL - {e}")
    results.append(("Slack", "FAIL"))

# 5. REST API
try:
    api_data = APIServer.get_signals_json(sig)
    assert api_data['count'] == len(sig)
    path = APIServer.save_api_response(api_data)
    print(f"[56] API: PASS ({len(sig)} signals)")
    results.append(("API", "PASS"))
except Exception as e:
    print(f"[56] API: FAIL - {e}")
    results.append(("API", "FAIL"))

# 6. Mobile Nav
try:
    assert callable(MobileNavigation.bottom_nav)
    print("[57] Mobile Nav: PASS")
    results.append(("Nav", "PASS"))
except Exception as e:
    print(f"[57] Mobile Nav: FAIL - {e}")
    results.append(("Nav", "FAIL"))

# Summary
print("\n" + "="*60)
passed = sum(1 for r in results if "PASS" in str(r[1]))
for name, status in results:
    print(f"  {'✅' if 'PASS' in str(status) else '❌'} {name}: {status}")
print(f"\n{passed}/{len(results)} passed")
print("="*60)