"""Loopback-only synthetic admin with atomic persistence and stale-write guards."""
from contextlib import contextmanager
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import tempfile
import threading

from ..domain.fixtures import FIXTURES, expected_catalog, initial_catalog
from ..domain.prices import UnsafeState


def atomic_json(path, data):
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.expected = expected_catalog()
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
            if set(self.data) != set(self.expected):
                raise UnsafeState("State catalog does not match this demo")
        else:
            self.data = initial_catalog()
            for product in self.data.values():
                product["revision"] = 0
            atomic_json(self.path, self.data)

    def save(self, payload):
        with self.lock:
            ref = payload["reference"]
            old = self.data[ref]
            before = {key: old[key] for key in ("regular", "xg", "stock", "revision")}
            if payload["selection"] != [ref] or payload["before"] != before:
                raise UnsafeState("Uncertain selection or stale state")
            if old["regular"] != self.expected[ref]["regular"]:
                raise UnsafeState("Regular prices need manual review")
            if payload["xg"] != self.expected[ref]["xg"]:
                raise UnsafeState("Target differs from synthetic expected fixture")
            if old["xg"] == payload["xg"]:
                raise UnsafeState("Repeated save rejected")
            updated = deepcopy(self.data)
            updated[ref]["xg"] = payload["xg"]
            updated[ref]["revision"] += 1
            atomic_json(self.path, updated)
            self.data = updated


@contextmanager
def serve(state_path):
    store = Store(state_path)
    token = secrets.token_hex(16)
    base = "/" + token + "/"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def reply(self, status, body, kind="application/json"):
            raw = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", kind + "; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path == base:
                self.reply(200, (FIXTURES / "admin.html").read_text(encoding="utf-8"), "text/html")
            elif self.path in (base + "admin.js", base + "admin.css"):
                name = self.path.rsplit("/", 1)[1]
                self.reply(200, (FIXTURES / name).read_text(encoding="utf-8"),
                           "text/javascript" if name.endswith(".js") else "text/css")
            elif self.path == base + "catalog":
                with store.lock:
                    data = json.dumps(store.data)
                self.reply(200, data)
            else:
                self.reply(404, "{}")

        def do_POST(self):
            if self.path != base + "save":
                self.reply(404, "{}")
                return
            origin = self.headers.get("Origin")
            if origin != "http://127.0.0.1:" + str(self.server.server_port):
                self.reply(403, "{}")
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size < 32768:
                    raise UnsafeState("Invalid payload size")
                store.save(json.loads(self.rfile.read(size)))
                self.reply(200, '{"status":"saved"}')
            except (ValueError, KeyError, TypeError):
                self.reply(409, '{"status":"blocked"}')

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_port) + base, store
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
