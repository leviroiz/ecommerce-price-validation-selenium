"""Durable unique operations, with pending intent before any browser save."""
import hashlib
import json
import sqlite3


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class Journal:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS operations (
            key TEXT PRIMARY KEY, reference TEXT NOT NULL,
            before_json TEXT NOT NULL, target_json TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending', 'verified')))""")
        self.db.commit()

    def get(self, key):
        row = self.db.execute("SELECT before_json, target_json, status FROM operations WHERE key=?", (key,)).fetchone()
        return (json.loads(row[0]), json.loads(row[1]), row[2]) if row else None

    def pending(self, key, ref, before, target):
        with self.db:
            self.db.execute("INSERT INTO operations VALUES (?, ?, ?, ?, 'pending')",
                            (key, ref, json.dumps(before, sort_keys=True), json.dumps(target, sort_keys=True)))

    def verified(self, key):
        with self.db:
            self.db.execute("UPDATE operations SET status='verified' WHERE key=?", (key,))

    def close(self):
        self.db.close()
