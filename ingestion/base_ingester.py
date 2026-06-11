"""
Base Ingester - All data collectors inherit from this
Handles: retry, rate limiting, robots.txt, logging
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import config


class BaseIngester:
    def __init__(self, source_name, rate_limit=1.0):
        self.source_name = source_name
        self.rate_limit = rate_limit
        self._last_request = {}
        self._robots_cache = {}
        self.headers = {
            'User-Agent': config.SEC_UA,
            'Accept': 'text/html,application/json,*/*'
        }
        logger.info(f"Ingester ready: {source_name}")

    def check_robots(self, url):
        parsed = urlparse(url)
        host = f"{parsed.scheme}://{parsed.netloc}"
        if host in self._robots_cache:
            return self._robots_cache[host].can_fetch(self.headers['User-Agent'], url)
        try:
            rp = RobotFileParser()
            rp.set_url(f"{host}/robots.txt")
            rp.read()
            self._robots_cache[host] = rp
            return rp.can_fetch(self.headers['User-Agent'], url)
        except:
            return True

    def _rate_limit(self, host):
        if host in self._last_request:
            elapsed = time.time() - self._last_request[host]
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)
        self._last_request[host] = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type((
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError
        ))
    )
    def safe_get(self, url, params=None, timeout=30):
        host = urlparse(url).netloc
        if not self.check_robots(url):
            raise PermissionError(f"robots.txt blocks: {url}")
        self._rate_limit(host)
        logger.debug(f"GET {url}")
        resp = requests.get(url, headers=self.headers, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp

    @staticmethod
    def make_checksum(content):
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def utc_now():
        return datetime.now(timezone.utc)


if __name__ == "__main__":
    ing = BaseIngester("test", rate_limit=0.5)
    print("BaseIngester initialized successfully.")
    print(f"Source: {ing.source_name}")