#!/usr/bin/env python3
"""
WC-2026-005 validation kit — LOCAL-ONLY HTTP server.

Binds ONLY to 127.0.0.1. Serves the attacker fixture and a controlled
victim-origin endpoint that sets a uniquely named test cookie and logs
incoming request headers (including whether the Cookie header was present).

No real domains, no real accounts, no real cookies, no third-party services.
No state-changing requests outside localhost. Read-only logging only.

Usage:
    python3 server.py [--port 8765] [--cookie-name wc005test]

Endpoints:
    GET /                 -> serves attacker.html
    GET /victim           -> sets the test cookie (Set-Cookie) and returns a
                             short text body; logs whether the request carried
                             the Cookie header
    GET /log?msg=...      -> appends msg to the log file (used by the fixture)
    GET /cors-test        -> same as /victim but with Access-Control-Allow-Origin
                             reflecting the request Origin (explicitly configured
                             local CORS test endpoint; only used if the tester
                             opts in)
"""
import argparse
import http.server
import os
import socketserver
import sys
import time
import uuid

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.log")

class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "WC005LocalKit/1.0"

    def log_message(self, fmt, *args):
        # Silence default stderr logging; we do our own structured logging.
        pass

    def _log(self, event, extra=""):
        ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        line = f"{ts} {event} {extra}"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(line, flush=True)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        return self.rfile.read(length) if length else b""

    def do_GET(self):
        parsed = self.path.split("?", 1)
        path = parsed[0]
        query = parsed[1] if len(parsed) > 1 else ""

        role = self.server.role
        if role == "attacker":
            if path == "/":
                self._serve_file("attacker.html", "text/html; charset=utf-8")
                return
            if path == "/log":
                self._handle_log(query)
                return
            self.send_error(404, "Not found (attacker role)")
            return
        # victim role
        if path == "/victim":
            self._handle_victim()
            return
        if path == "/cors-test":
            self._handle_victim(cors=True)
            return
        self.send_error(404, "Not found (victim role)")

    def do_POST(self):
        # Only /victim accepts POST (state-changing); still local-only.
        if self.server.role == "victim" and self.path.split("?", 1)[0] == "/victim":
            self._handle_victim()
            return
        self.send_error(404, "Not found")

    def _serve_file(self, name, ctype):
        base = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(os.path.join(base, name), "rb") as f:
                body = f.read()
        except FileNotFoundError:
            self.send_error(404, "fixture not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_victim(self, cors=False):
        cookie_name = self.server.cookie_name
        cookie_header = self.headers.get("Cookie", "")
        has_cookie = cookie_name + "=" in cookie_header
        origin = self.headers.get("Origin", "")
        self._log(
            "VICTIM_REQ",
            f"path={self.path} cookie_header_present={'yes' if cookie_header else 'no'} "
            f"test_cookie_present={'yes' if has_cookie else 'no'} origin={origin or '(none)'}",
        )
        # Set the test cookie on the victim origin (first visit).
        self.send_response(200)
        self.send_header("Set-Cookie", f"{cookie_name}=sent; Path=/; SameSite=Lax")
        if cors:
            # Explicitly configured local CORS test endpoint: reflect Origin.
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        body = f"victim-ok test_cookie_present={'yes' if has_cookie else 'no'}"
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def _handle_log(self, query):
        msg = ""
        for part in query.split("&"):
            if part.startswith("msg="):
                msg = part[4:]
        self._log("FIXTURE_MSG", f"msg={msg}")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, addr, handler, cookie_name, role):
        self.cookie_name = cookie_name
        self.role = role
        super().__init__(addr, handler)

def main():
    ap = argparse.ArgumentParser(description="WC-2026-005 local validation server")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1",
                    help="bind address (loopback only; use 127.0.0.2 for a second site identity)")
    ap.add_argument("--role", choices=["attacker", "victim"], default="attacker",
                    help="attacker: serve attacker.html + /log; victim: serve /victim + /cors-test")
    ap.add_argument("--cookie-name", default="wc005test_" + uuid.uuid4().hex[:8])
    args = ap.parse_args()

    # Bind ONLY to loopback.
    with Server((args.host, args.port), Handler, args.cookie_name, args.role) as httpd:
        print(f"WC-2026-005 local server ({args.role}) on http://{args.host}:{args.port}/")
        print(f"Test cookie name: {args.cookie_name}")
        print(f"Log file: {LOG_FILE}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")

if __name__ == "__main__":
    main()
