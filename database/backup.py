"""
Automated Backup — Google Drive sync
Run daily via Windows Task Scheduler
"""
import duckdb, os, shutil
from datetime import datetime
from pathlib import Path

def backup():
    src = Path(__file__).parent.parent / 'aletheia.db'
    dst_dir = Path(os.getenv('GOOGLE_DRIVE_PATH', str(Path.home() / 'GoogleDrive' / 'MyDrive' / 'aletheia_data')))
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    dst = dst_dir / f'aletheia_backup_{timestamp}.db'
    
    shutil.copy2(src, dst)
    print(f"Backup saved: {dst}")
    
    # Keep only last 7 backups
    backups = sorted(dst_dir.glob('aletheia_backup_*.db'))
    for old in backups[:-7]:
        old.unlink()
        print(f"Removed old: {old}")

if __name__ == "__main__":
    backup()