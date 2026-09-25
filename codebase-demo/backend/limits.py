from contextlib import closing, contextmanager
from datetime import datetime, timezone
import sqlite3
import threading
import time

from fastapi import HTTPException


class UsageReservation:
    def __init__(self, limits, ip, visitor_id):
        self.limits = limits
        self.ip = ip
        self.visitor_id = visitor_id
        self.accepted = False

    def accept(self):
        if self.accepted:
            raise RuntimeError("Usage reservation was already accepted")
        remaining = self.limits._accept(self.ip, self.visitor_id)
        self.accepted = True
        return remaining


class UsageLimits:
    def __init__(self, path, daily, per_minute, concurrent, anonymous_limit=3):
        self.path = path
        self.daily = daily
        self.per_minute = per_minute
        self.anonymous_limit = anonymous_limit
        self.slots = threading.BoundedSemaphore(concurrent)
        self.lock = threading.Lock()
        self.recent = {}
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("CREATE TABLE IF NOT EXISTS usage (day TEXT PRIMARY KEY, attempts INTEGER NOT NULL)")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS visitor_daily_usage ("
                "visitor_id TEXT NOT NULL, day TEXT NOT NULL, accepted_questions INTEGER NOT NULL, "
                "PRIMARY KEY (visitor_id, day))"
            )

    def remaining(self, visitor_id):
        day = datetime.now(timezone.utc).date().isoformat()
        with closing(sqlite3.connect(self.path, timeout=5)) as connection:
            row = connection.execute(
                "SELECT accepted_questions FROM visitor_daily_usage WHERE visitor_id = ? AND day = ?",
                (visitor_id, day),
            ).fetchone()
        return max(0, self.anonymous_limit - (row[0] if row else 0))

    def _prune_and_check_ip(self, ip, now):
        self.recent = {
            key: [timestamp for timestamp in timestamps if timestamp > now - 60]
            for key, timestamps in self.recent.items()
            if timestamps[-1] > now - 60
        }
        timestamps = self.recent.get(ip, [])
        if len(timestamps) >= self.per_minute:
            raise HTTPException(429, "Too many questions. Please wait a minute.", headers={"Retry-After": "60"})
        return timestamps

    def _check_persistent_limits(self, visitor_id):
        day = datetime.now(timezone.utc).date().isoformat()
        with closing(sqlite3.connect(self.path, timeout=5)) as connection:
            visitor = connection.execute(
                "SELECT accepted_questions FROM visitor_daily_usage WHERE visitor_id = ? AND day = ?",
                (visitor_id, day),
            ).fetchone()
            accepted = visitor[0] if visitor else 0
            daily = connection.execute("SELECT attempts FROM usage WHERE day = ?", (day,)).fetchone()
        if accepted >= self.anonymous_limit:
            raise HTTPException(429, {
                "message": "You have used all three AI questions available today.",
                "questions_remaining": 0,
            })
        if daily and daily[0] >= self.daily:
            raise HTTPException(429, "The demo has reached its daily question limit.")

    def _accept(self, ip, visitor_id):
        with self.lock:
            now = time.monotonic()
            timestamps = self._prune_and_check_ip(ip, now)
            day = datetime.now(timezone.utc).date().isoformat()
            with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("INSERT OR IGNORE INTO usage VALUES (?, 0)", (day,))
                connection.execute(
                    "INSERT OR IGNORE INTO visitor_daily_usage VALUES (?, ?, 0)",
                    (visitor_id, day),
                )
                accepted = connection.execute(
                    "SELECT accepted_questions FROM visitor_daily_usage WHERE visitor_id = ? AND day = ?",
                    (visitor_id, day),
                ).fetchone()[0]
                if accepted >= self.anonymous_limit:
                    raise HTTPException(429, {
                        "message": "You have used all three AI questions available today.",
                        "questions_remaining": 0,
                    })
                used = connection.execute("SELECT attempts FROM usage WHERE day = ?", (day,)).fetchone()[0]
                if used >= self.daily:
                    raise HTTPException(429, "The demo has reached its daily question limit.")
                connection.execute("UPDATE usage SET attempts = attempts + 1 WHERE day = ?", (day,))
                connection.execute(
                    "UPDATE visitor_daily_usage SET accepted_questions = accepted_questions + 1 "
                    "WHERE visitor_id = ? AND day = ?",
                    (visitor_id, day),
                )
            self.recent[ip] = timestamps + [now]
        return self.anonymous_limit - accepted - 1

    @contextmanager
    def reserve(self, ip, visitor_id="legacy"):
        if not self.slots.acquire(blocking=False):
            raise HTTPException(429, "The demo is busy. Please try again shortly.", headers={"Retry-After": "15"})
        try:
            with self.lock:
                now = time.monotonic()
                self._prune_and_check_ip(ip, now)
                self._check_persistent_limits(visitor_id)
            yield UsageReservation(self, ip, visitor_id)
        finally:
            self.slots.release()
