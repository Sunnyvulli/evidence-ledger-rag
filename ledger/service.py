"""Loopback-only JSON interface with bounded requests and hashed-query monitoring."""

import argparse
import hashlib
import json
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .engine import answer, connect, corpus_hash


def server(database, monitor, port=8090):
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *_):
            pass

        def respond(self, status, data):
            raw = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path != "/health":
                return self.respond(404, {"error": "Not found"})
            try:
                with connect(database) as db:
                    data = {"status": "ok", "corpus_sha256": corpus_hash(db)}
                self.respond(200, data)
            except (sqlite3.Error, OSError, TypeError):
                self.respond(503, {"error": "Index unavailable"})

        def do_POST(self):
            if self.path != "/query":
                return self.respond(404, {"error": "Not found"})
            started = time.perf_counter()
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= 4096:
                    raise ValueError("Body size must be 1 to 4096 bytes")
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError("Incomplete body")
                data = json.loads(raw)
                if (
                    not isinstance(data, dict)
                    or not set(data) <= {"query", "k", "method"}
                    or "query" not in data
                ):
                    raise ValueError("Expected query and optional k/method")
                # Invalid inputs receive 400 even when the index is absent.
                from .engine import validate

                validate(data["query"], data.get("k", 3), data.get("method", "hybrid"))
                with connect(database) as db:
                    result = answer(db, **data)
                entry = {
                    "query_sha256": hashlib.sha256(data["query"].encode()).hexdigest(),
                    "corpus_sha256": result["corpus_sha256"],
                    "abstained": result["abstained"],
                    "claim_count": len(result["claims"]),
                    "seconds": time.perf_counter() - started,
                }
                with lock:
                    Path(monitor).parent.mkdir(parents=True, exist_ok=True)
                    with open(monitor, "a") as stream:
                        stream.write(json.dumps(entry) + "\n")
                self.respond(200, result)
            except (ValueError, TypeError, UnicodeError):
                self.respond(400, {"error": "Invalid query or request schema"})
            except (sqlite3.Error, OSError):
                self.respond(503, {"error": "Index or monitor unavailable"})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--database", default=".local/index.sqlite")
    p.add_argument("--monitor", default=".local/monitor.jsonl")
    p.add_argument("--port", type=int, default=8090)
    args = p.parse_args()
    with server(args.database, args.monitor, args.port) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
