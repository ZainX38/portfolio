from contextlib import closing, contextmanager
from datetime import datetime, timezone
import sqlite3
import threading
import time

from fastapi import HTTPException


class UsageLimits:
    def __init__(self, path, daily, per_minute, concurrent):
        self.path = path
        self.daily = daily
        self.per_minute = per_minute
        self.slots = threading.BoundedSemaphore(concurrent)
        self.lock = threading.Lock()
        self.recent = {}
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("CREATE TABLE IF NOT EXISTS usage (day TEXT PRIMARY KEY, attempts INTEGER NOT NULL)")

    @contextmanager
    def reserve(self, ip):
        if not self.slots.acquire(blocking=False):
            raise HTTPException(429, "The demo is busy. Please try again shortly.", headers={"Retry-After": "15"})
        try:
            with self.lock:
                now = time.monotonic()
                self.recent = {key: [timestamp for timestamp in timestamps if timestamp > now - 60] for key, timestamps in self.recent.items() if timestamps[-1] > now - 60}
                timestamps = self.recent.get(ip, [])
                if len(timestamps) >= self.per_minute:
                    raise HTTPException(429, "Too many questions. Please wait a minute.", headers={"Retry-After": "60"})
                day = datetime.now(timezone.utc).date().isoformat()
                # Atomic reservation survives restarts. Failures are counted too,
                # since the model may already have consumed resources.
                with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute("INSERT OR IGNORE INTO usage VALUES (?, 0)", (day,))
                    used = connection.execute("SELECT attempts FROM usage WHERE day = ?", (day,)).fetchone()[0]
                    if used >= self.daily:
                        raise HTTPException(429, "The demo has reached its daily question limit.")
                    connection.execute("UPDATE usage SET attempts = attempts + 1 WHERE day = ?", (day,))
                self.recent[ip] = timestamps + [now]
            yield
        finally:
            self.slots.release()
