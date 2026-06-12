import time, subprocess, os
from datetime import datetime

os.chdir(r'C:\Users\SBI\Desktop\aletheia2.0')

JOBS = {
    'alpaca': ('python live/alpaca_fetcher.py', 300),
    'health': ('python -c "from live.monitoring import uptime; uptime.ping()"', 3600),
}
last = {k: 0 for k in JOBS}
print("ALETHEIA SCHEDULER STARTED")
while True:
    now = time.time()
    for name, (cmd, interval) in JOBS.items():
        if now - last[name] >= interval:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {name}")
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if r.returncode == 0:
                print(f"  ✅ OK")
            else:
                print(f"  ❌ {r.stderr[:100]}")
            last[name] = now
    time.sleep(30)