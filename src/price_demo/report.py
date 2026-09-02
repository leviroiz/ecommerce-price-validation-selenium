"""Append-only JSONL audit, flushed before a browser mutation."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid


class Audit:
    def __init__(self, path):
        self.path = Path(path)
        self.run_id = str(uuid.uuid4())

    def record(self, **event):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {"run_id": self.run_id, "at": datetime.now(timezone.utc).isoformat(), **event}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())


@contextmanager
def single_run(path):
    """One CLI execution per checkout; a stale lock requires manual inspection."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    try:
        yield
    finally:
        path.unlink()
