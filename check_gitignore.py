"""Verify .gitignore protects secrets"""
import os

print("="*50)
print("GITIGNORE AUDIT")
print("="*50)

if os.path.exists('.gitignore'):
    with open('.gitignore') as f:
        content = f.read()
    
    needed = {
        '.env': 'API keys',
        '*.db': 'Database files',
        'alpaca_data.json': 'Alpaca data',
        '__pycache__': 'Python cache',
        'security/': 'User credentials',
        'backups/': 'Database backups',
        'logs/': 'Log files',
        '*.json': 'Result files',
    }
    
    missing = []
    for pattern, reason in needed.items():
        if pattern not in content:
            missing.append((pattern, reason))
            print(f"  ❌ MISSING: {pattern} ({reason})")
        else:
            print(f"  ✅ PROTECTED: {pattern}")
    
    if missing:
        print(f"\n⚠️ {len(missing)} patterns need to be added to .gitignore")
        print("\nAdd these lines to .gitignore:")
        for pattern, reason in missing:
            print(f"  {pattern}  # {reason}")
    else:
        print(f"\n✅ ALL SECRETS PROTECTED")
else:
    print("❌ No .gitignore file!")
    print("\nCreate .gitignore with:")
    print("""
.env
*.db
*.json
alpaca_data.json
__pycache__/
security/
backups/
logs/
""")