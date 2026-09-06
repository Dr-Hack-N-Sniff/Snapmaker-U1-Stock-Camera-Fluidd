#!/usr/bin/env python3

import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

IMAGE = "/tmp/.monitor.jpg"
HOST = "127.0.0.1"
PORT = 8080
BOUNDARY = "frame"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("%s - %s" % (self.client_address[0], fmt % args), flush=True)

    def _action(self):
        q = parse_qs(urlparse(self.path).query)
        return q.get("action", [""])[0]

    def do_GET(self):
        action = self._action()

        if action == "snapshot":
            self.snapshot()
        elif action == "stream":
            self.stream()
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(
                b"U1 temporary MJPEG bridge\n"
                b"Use /?action=snapshot or /?action=stream\n"
            )

    def snapshot(self):
        try:
            with open(IMAGE, "rb") as f:
                data = f.read()
        except OSError:
            self.send_error(503, "Camera image unavailable")
            return

        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.end_headers()
        self.wfile.write(data)

    def stream(self):
        self.send_response(200)
        self.send_header(
            "Content-Type",
            f"multipart/x-mixed-replace; boundary={BOUNDARY}"
        )
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.end_headers()

        last_mtime = None

        try:
            while True:
                try:
                    st = os.stat(IMAGE)
                    mtime = st.st_mtime_ns

                    if mtime != last_mtime:
                        with open(IMAGE, "rb") as f:
                            data = f.read()

                        self.wfile.write(
                            f"--{BOUNDARY}\r\n".encode()
                        )
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(
                            f"Content-Length: {len(data)}\r\n\r\n".encode()
                        )
                        self.wfile.write(data)
                        self.wfile.write(b"\r\n")
                        self.wfile.flush()

                        last_mtime = mtime

                except FileNotFoundError:
                    pass

                time.sleep(0.05)

        except (BrokenPipeError, ConnectionResetError):
            pass


print(f"U1 MJPEG bridge listening on {HOST}:{PORT}", flush=True)
print(f"Source: {IMAGE}", flush=True)

ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
