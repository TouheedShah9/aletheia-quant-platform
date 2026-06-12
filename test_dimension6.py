"""
Dimension 6 Audit — Test every security feature
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("DIMENSION 6 AUDIT — SECURITY & AUTHENTICATION")
print("="*60)
results = []

# 1. Login success
print("\n[38] LOGIN SUCCESS:")
try:
    from live.security import auth
    ok, token = auth.login('admin', 'aletheia_admin_2024')
    assert ok, "Login failed"
    assert token is not None
    results.append(("Login Success", "PASS"))
    print(f"   PASS — Token: {token[:20]}...")
except Exception as e:
    results.append(("Login Success", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 2. Login failure
print("\n[38] LOGIN FAILURE (wrong password):")
try:
    ok, msg = auth.login('admin', 'wrong_password')
    assert not ok, "Should have failed"
    results.append(("Login Failure", "PASS"))
    print(f"   PASS — Message: {msg}")
except Exception as e:
    results.append(("Login Failure", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 3. Account lockout
print("\n[38] ACCOUNT LOCKOUT:")
try:
    for _ in range(6):
        auth.login('admin', 'wrong_password')
    ok, msg = auth.login('admin', 'aletheia_admin_2024')
    assert not ok, "Should be locked"
    assert 'locked' in msg.lower()
    results.append(("Account Lockout", "PASS"))
    print(f"   PASS — {msg}")
    # Reset for further tests
    auth.users['admin']['failed_attempts'] = 0
    auth.users['admin']['locked_until'] = None
    auth._save_users(auth.users)
except Exception as e:
    results.append(("Account Lockout", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 4. Session validation
print("\n[38] SESSION VALIDATION:")
try:
    session = auth.validate_session(token)
    assert session is not None
    assert session['username'] == 'admin'
    results.append(("Session Valid", "PASS"))
    print(f"   PASS — User: {session['username']}, Role: {session['role']}")
except Exception as e:
    results.append(("Session Valid", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 5. Logout
print("\n[38] LOGOUT:")
try:
    auth.logout(token)
    session = auth.validate_session(token)
    assert session is None
    results.append(("Logout", "PASS"))
    print("   PASS — Session destroyed")
except Exception as e:
    results.append(("Logout", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 6. RBAC permissions
print("\n[39] RBAC PERMISSIONS:")
try:
    from live.security import rbac
    assert rbac.has_permission('admin', 'execute_trades')
    assert not rbac.has_permission('viewer', 'execute_trades')
    assert rbac.has_permission('viewer', 'view_all')
    results.append(("RBAC", "PASS"))
    print("   PASS — Admin can trade, viewer cannot")
except Exception as e:
    results.append(("RBAC", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 7. API key generation
print("\n[40] API KEY:")
try:
    from live.security import api_keys
    key = api_keys.generate_key('test', 'analyst', 1)
    valid = api_keys.validate_key(key)
    assert valid is not None
    results.append(("API Key", "PASS"))
    print(f"   PASS — Key valid: {valid['name']}")
except Exception as e:
    results.append(("API Key", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 8. API key revocation
print("\n[40] API KEY REVOCATION:")
try:
    api_keys.revoke_key(key)
    valid = api_keys.validate_key(key)
    assert valid is None
    results.append(("API Revoke", "PASS"))
    print("   PASS — Key revoked")
except Exception as e:
    results.append(("API Revoke", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 9. Input validation
print("\n[41] INPUT VALIDATION:")
try:
    from live.security import validator
    assert validator.validate_ticker('AAPL')
    assert validator.validate_ticker('MSFT')
    assert validator.validate_ticker('SHEL.L')
    assert not validator.validate_ticker('DROP TABLE;--')
    assert not validator.validate_ticker('')
    assert not validator.validate_ticker(None)
    results.append(("Input Valid", "PASS"))
    print("   PASS — Valid tickers accepted, injections blocked")
except Exception as e:
    results.append(("Input Valid", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 10. SQL sanitization
print("\n[41] SQL SANITIZATION:")
try:
    dirty = "AAPL; DROP TABLE users; --"
    clean = validator.sanitize_sql(dirty)
    assert 'DROP' not in clean
    assert ';' not in clean
    results.append(("SQL Sanitize", "PASS"))
    print(f"   PASS — '{dirty}' -> '{clean}'")
except Exception as e:
    results.append(("SQL Sanitize", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 11. Security audit log
print("\n[43] SECURITY AUDIT:")
try:
    from live.security import sec_audit
    sec_audit.log('TEST_COMPLETE', 'audit_script', 'All tests passed')
    assert len(sec_audit.logs) >= 1
    results.append(("Audit Log", "PASS"))
    print(f"   PASS — {len(sec_audit.logs)} entries")
except Exception as e:
    results.append(("Audit Log", f"FAIL: {e}"))
    print(f"   FAIL — {e}")

# 12. Security files exist
print("\n[FILES] SECURITY FILES:")
for f in ['security/users.json', 'security/sessions.json', 'security/api_keys.json', 'security/security_audit.json']:
    exists = os.path.exists(f)
    results.append((f"File: {f}", "PASS" if exists else "FAIL"))
    print(f"   {'PASS' if exists else 'FAIL'} — {f}")

# Summary
print("\n" + "="*60)
passed = sum(1 for r in results if "PASS" in str(r[1]))
failed = sum(1 for r in results if "FAIL" in str(r[1]))
for name, status in results:
    print(f"  {'✅' if 'PASS' in str(status) else '❌'} {name}: {status}")
print(f"\nTotal: {passed}/{len(results)} passed")
print("="*60)
if failed == 0:
    print("DIMENSION 6: ALL TESTS PASSED — PRODUCTION READY")
else:
    print(f"DIMENSION 6: {failed} FIXES NEEDED")