"""Data Cache Layer — JSON-based with TTL"""
import json, time
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / '.cache'
CACHE_DIR.mkdir(exist_ok=True)

class Cache:
    def __init__(self, ttl=30):
        self.ttl = ttl
    
    def get(self, key):
        path = CACHE_DIR / f"{key}.json"
        if not path.exists():
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            if time.time() - data.get('_cached_at', 0) > self.ttl:
                return None
            return data.get('value')
        except:
            return None
    
    def set(self, key, value):
        with open(CACHE_DIR / f"{key}.json", 'w') as f:
            json.dump({'_cached_at': time.time(), 'value': value}, f)

cache = Cache(ttl=30)