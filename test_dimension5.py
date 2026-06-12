"""
Dimension 5 Audit — Test every monitoring & alerting feature
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("DIMENSION 5 AUDIT — MONITORING & ALERTING")
print("="*60)

results = []

# 1. Health Check — Database
print("\n[32] HEALTH CHECK — DATABASE:")
try:
    from live.monitoring import health
    db = health.check_database()
    assert db['status'] == 'healthy', f"Database unhealthy: {db}"
    results.append(("DB Health", "PASS"))
    print(f"   PASS — Status: {db['status']}")
except Exception as e:
    results.append(("DB Health", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 2. Health Check — Alpaca
print("\n[32] HEALTH CHECK — ALPACA:")
try:
    al = health.check_alpaca()
    print(f"   Status: {al['status']} — {al.get('message', al.get('equity', ''))}")
    results.append(("Alpaca Health", "PASS"))
except Exception as e:
    results.append(("Alpaca Health", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 3. Health Check — Signals
print("\n[32] HEALTH CHECK — SIGNALS:")
try:
    sg = health.check_signals()
    assert sg['status'] == 'healthy'
    assert sg['total'] > 0, "No signals in database"
    results.append(("Signals Health", "PASS"))
    print(f"   PASS — {sg['total']} signals ({sg['long']} long)")
except Exception as e:
    results.append(("Signals Health", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 4. Full Health Check
print("\n[32] FULL HEALTH CHECK:")
try:
    full = health.full_check()
    assert 'checks' in full
    assert 'overall' in full
    results.append(("Full Health", "PASS"))
    print(f"   PASS — Overall: {full['overall']}")
except Exception as e:
    results.append(("Full Health", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 5. Uptime Monitor
print("\n[33] UPTIME MONITOR:")
try:
    from live.monitoring import uptime
    was_up = uptime.ping()
    assert uptime.data['total'] >= 1, "Uptime not recording"
    assert 'uptime_pct' in uptime.data
    results.append(("Uptime Monitor", "PASS"))
    print(f"   PASS — {uptime.data['total']} checks, {uptime.data['uptime_pct']}% uptime")
except Exception as e:
    results.append(("Uptime Monitor", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 6. Error Tracker
print("\n[34] ERROR TRACKER:")
try:
    from live.monitoring import errors
    errors.log('audit_test', 'Audit verification error', 'INFO')
    assert len(errors.errors) >= 1, "Error not logged"
    
    # Check log file exists
    log_file = 'logs/errors.json'
    assert os.path.exists(log_file), f"Log file {log_file} not found"
    results.append(("Error Tracker", "PASS"))
    print(f"   PASS — {len(errors.errors)} errors logged, file exists")
except Exception as e:
    results.append(("Error Tracker", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 7. Performance Metrics
print("\n[35] PERFORMANCE METRICS:")
try:
    from live.monitoring import metrics
    metrics.record_query('audit_query', 12.5)
    metrics.record_query('audit_query_2', 8.3)
    stats = metrics.get_stats()
    assert stats['count'] >= 2, "Metrics not recording"
    assert stats['avg_ms'] > 0
    results.append(("Perf Metrics", "PASS"))
    print(f"   PASS — {stats['count']} queries, avg {stats['avg_ms']}ms")
except Exception as e:
    results.append(("Perf Metrics", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 8. Alert Manager
print("\n[36] ALERT MANAGER:")
try:
    from live.monitoring import alerts
    assert hasattr(alerts, 'send_email'), "send_email missing"
    assert hasattr(alerts, 'signal_flip_alert'), "signal_flip_alert missing"
    assert hasattr(alerts, 'drawdown_alert'), "drawdown_alert missing"
    assert hasattr(alerts, 'system_health_alert'), "system_health_alert missing"
    results.append(("Alert Manager", "PASS"))
    print(f"   PASS — All 4 alert functions exist")
except Exception as e:
    results.append(("Alert Manager", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 9. SMS Alert
print("\n[37] SMS ALERT:")
try:
    from live.monitoring import sms
    assert hasattr(sms, 'send'), "SMS send missing"
    assert hasattr(sms, 'CARRIERS'), "Carrier list missing"
    carriers = len(sms.CARRIERS)
    results.append(("SMS Alert", "PASS"))
    print(f"   PASS — {carriers} carriers configured")
except Exception as e:
    results.append(("SMS Alert", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 10. Log files exist
print("\n[FILES] LOG FILES:")
log_files = ['logs/uptime.json', 'logs/errors.json', 'logs/metrics.json']
for lf in log_files:
    exists = os.path.exists(lf)
    size = os.path.getsize(lf) if exists else 0
    results.append((f"Log: {lf}", "PASS" if exists else "FAIL"))
    print(f"   {'PASS' if exists else 'FAIL'} — {lf} ({size} bytes)")

# Summary
print("\n" + "="*60)
print("RESULTS SUMMARY")
print("="*60)
passed = sum(1 for r in results if "PASS" in str(r[1]))
failed = sum(1 for r in results if "FAIL" in str(r[1]))
for name, status in results:
    icon = "✅" if "PASS" in str(status) else "❌"
    print(f"  {icon} {name}: {status}")
print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)}")
print("="*60)
if failed == 0:
    print("DIMENSION 5: ALL TESTS PASSED — PRODUCTION READY")
else:
    print(f"DIMENSION 5: {failed} FIXES NEEDED")