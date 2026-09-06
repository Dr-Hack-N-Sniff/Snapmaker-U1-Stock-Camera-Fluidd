#!/usr/bin/env python3

import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

IMAGE = "/tmp/.monitor.jpg"
HOST = "127.0.0.1"
PORT = 8080
BOUNDARY = "frame"

# v1.0.1 camera watchdog. A normal stream updates much faster than this.
STALE_SECONDS = 15.0
RECOVERY_COOLDOWN = 15.0
WATCHDOG_INTERVAL = 1.0
CAMERA_TOPIC = "camera/request"
START_MONITOR = '{"jsonrpc":"2.0","id":30003,"method":"camera.start_monitor","params":{"domain":"lan","interval":0}}'


def frame_mtime_ns():
    try:
        return os.stat(IMAGE).st_mtime_ns
    except FileNotFoundError:
        return None


def request_camera_recovery():
    """Ask stock unisrv to (re)start the LAN monitor; never restart unisrv itself."""
    try:
        result = subprocess.run(
            ["mosquitto_pub", "-h", "127.0.0.1", "-p", "1883",
             "-t", CAMERA_TOPIC, "-m", START_MONITOR],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            print("watchdog: requested camera.start_monitor recovery", flush=True)
            return True
        print("watchdog: recovery request failed (mosquitto_pub rc=%d)" % result.returncode, flush=True)
    except (OSError, subprocess.SubprocessError) as exc:
        print("watchdog: recovery request error: %s" % exc, flush=True)
    return False


def watchdog_loop():
    last_mtime = frame_mtime_ns()
    last_change = time.monotonic()
    last_recovery = 0.0

    while True:
        time.sleep(WATCHDOG_INTERVAL)
        now = time.monotonic()
        mtime = frame_mtime_ns()

        if mtime is not None and mtime != last_mtime:
            last_mtime = mtime
            last_change = now
            continue

        if now - last_change < STALE_SECONDS:
            continue
        if now - last_recovery < RECOVERY_COOLDOWN:
            continue

        age = now - last_change
        print("watchdog: camera frame stale for %.1fs; requesting recovery" % age, flush=True)
        request_camera_recovery()
        last_recovery = now


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
                b"U1 MJPEG bridge v1.0.1\n"
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

                        self.wfile.write(f"--{BOUNDARY}\r\n".encode())
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(f"Content-Length: {len(data)}\r\n\r\n".encode())
                        self.wfile.write(data)
                        self.wfile.write(b"\r\n")
                        self.wfile.flush()
                        last_mtime = mtime

                except FileNotFoundError:
                    pass

                time.sleep(0.05)

        except (BrokenPipeError, ConnectionResetError):
            pass


print(f"U1 MJPEG bridge v1.0.1 listening on {HOST}:{PORT}", flush=True)
print(f"Source: {IMAGE}", flush=True)
print(f"watchdog: stale={STALE_SECONDS:.0f}s cooldown={RECOVERY_COOLDOWN:.0f}s", flush=True)
threading.Thread(target=watchdog_loop, name="u1-camera-watchdog", daemon=True).start()
ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
