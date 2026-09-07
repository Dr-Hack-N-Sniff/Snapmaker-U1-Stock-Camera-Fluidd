#!/usr/bin/env python3

import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from u1_camera_policy import (
    RESET_WINDOW,
    should_restart_monitor,
    should_release_lan_on_wan_stop,
    is_wan_stop_log_line,
    is_wan_start_log_line,
    is_failed_wan_session,
    should_restart_during_wan_recovery,
    next_wan_start_time,
    should_reopen_log,
)

IMAGE = "/tmp/.monitor.jpg"
HOST = "127.0.0.1"
PORT = 8080
BOUNDARY = "frame"

# If Snapmaker's stock monitor stops updating the JPEG, restart
# the stock LAN monitoring session.
WATCH_INTERVAL = 1.0
RESTART_COOLDOWN = 10.0

STATE_LOCK = threading.Lock()
wan_start_time = None
wan_recovery_started = None



def stop_stock_lan_monitor():
    message = (
        '{"jsonrpc":"2.0","id":30004,'
        '"method":"camera.stop_monitor",'
        '"params":{"domain":"lan"}}'
    )

    try:
        subprocess.run(
            [
                "mosquitto_pub",
                "-h",
                "127.0.0.1",
                "-p",
                "1883",
                "-t",
                "camera/request",
                "-m",
                message,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        print(
            "WAN monitor stopped; released LAN monitor for clean reset",
            flush=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(
            f"LAN monitor release error: {exc}",
            flush=True,
        )


def unisrv_watchdog():
    global wan_start_time, wan_recovery_started

    path = "/userdata/logs/unisrv.log"
    f = None
    open_inode = None

    print("unisrv WAN session watcher active", flush=True)

    while True:
        try:
            st = os.stat(path)
            current_inode = st.st_ino

            if (
                f is None
                or should_reopen_log(open_inode, current_inode)
            ):
                if f is not None:
                    f.close()

                f = open(path, "r", errors="replace")
                f.seek(0, os.SEEK_END)
                open_inode = current_inode

                print("unisrv log opened/reopened", flush=True)

            line = f.readline()

            if not line:
                time.sleep(0.2)
                continue

            now = time.monotonic()

            if is_wan_start_log_line(line):
                with STATE_LOCK:
                    recovery_active = wan_recovery_started is not None
                    previous_start = wan_start_time
                    wan_start_time = next_wan_start_time(
                        recovery_active,
                        previous_start,
                        now,
                    )

                if (
                    recovery_active
                    and previous_start is not None
                ):
                    print(
                        "Detected duplicate WAN start during recovery; "
                        "keeping original stability timer",
                        flush=True,
                    )
                else:
                    print(
                        "Detected Snapmaker WAN monitor start",
                        flush=True,
                    )

                continue

            if is_wan_stop_log_line(line):
                with STATE_LOCK:
                    started = wan_start_time
                    wan_start_time = None

                if started is None:
                    print(
                        "WAN stop seen without tracked WAN start; "
                        "leaving LAN unchanged",
                        flush=True,
                    )
                    continue

                duration = now - started

                if is_failed_wan_session(duration):
                    with STATE_LOCK:
                        if wan_recovery_started is None:
                            wan_recovery_started = now

                    print(
                        f"Snapmaker WAN session failed after "
                        f"{duration:.1f}s; entering recovery",
                        flush=True,
                    )

                    if should_release_lan_on_wan_stop("wan"):
                        stop_stock_lan_monitor()
                else:
                    print(
                        f"Snapmaker WAN session ended normally after "
                        f"{duration:.1f}s; leaving LAN active",
                        flush=True,
                    )

        except FileNotFoundError:
            if f is not None:
                f.close()
                f = None
                open_inode = None
            time.sleep(0.5)

        except OSError as exc:
            print(
                f"unisrv watcher error: {exc}",
                flush=True,
            )
            time.sleep(1.0)


def start_stock_monitor():
    message = (
        '{"jsonrpc":"2.0","id":30003,'
        '"method":"camera.start_monitor",'
        '"params":{"domain":"lan","interval":0}}'
    )

    try:
        result = subprocess.run(
            [
                "mosquitto_pub",
                "-h",
                "127.0.0.1",
                "-p",
                "1883",
                "-t",
                "camera/request",
                "-m",
                message,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )

        if result.returncode == 0:
            print(
                "Camera watchdog requested stock monitor restart",
                flush=True,
            )
            return True

        print(
            "Camera watchdog could not request stock monitor restart "
            f"(exit {result.returncode})",
            flush=True,
        )

    except (OSError, subprocess.SubprocessError) as exc:
        print(
            f"Camera watchdog restart error: {exc}",
            flush=True,
        )

    return False


def camera_watchdog():
    global wan_recovery_started

    last_mtime = None
    last_change = time.monotonic()
    last_restart = 0.0

    print(
        f"Camera watchdog active; reset window={RESET_WINDOW:.0f}s",
        flush=True,
    )

    while True:
        now = time.monotonic()

        try:
            st = os.stat(IMAGE)
            mtime = st.st_mtime_ns

            if mtime != last_mtime:
                last_mtime = mtime
                last_change = now

        except FileNotFoundError:
            pass
        except OSError as exc:
            print(
                f"Camera watchdog image-stat error: {exc}",
                flush=True,
            )

        stale_for = now - last_change

        with STATE_LOCK:
            recovery_started = wan_recovery_started
            active_wan_start = wan_start_time

        # A WAN session that survives the failure threshold means
        # Snapmaker successfully won the clean-start opportunity.
        if (
            recovery_started is not None
            and active_wan_start is not None
            and not is_failed_wan_session(now - active_wan_start)
        ):
            with STATE_LOCK:
                wan_recovery_started = None

            recovery_started = None
            print(
                "Snapmaker WAN session remained stable; "
                "WAN recovery complete",
                flush=True,
            )

        if recovery_started is not None:
            recovery_for = now - recovery_started

            if (
                stale_for >= RESET_WINDOW
                and should_restart_during_wan_recovery(recovery_for)
                and now - last_restart >= RESTART_COOLDOWN
            ):
                print(
                    f"WAN recovery fallback reached after "
                    f"{recovery_for:.1f}s; restoring LAN monitor",
                    flush=True,
                )

                start_stock_monitor()
                last_restart = now

                with STATE_LOCK:
                    wan_recovery_started = None

        elif (
            should_restart_monitor(stale_for)
            and now - last_restart >= RESTART_COOLDOWN
        ):
            print(
                f"Camera source stale for {stale_for:.1f}s; "
                "reset window complete, restarting stock monitor",
                flush=True,
            )

            start_stock_monitor()
            last_restart = now

        time.sleep(WATCH_INTERVAL)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(
            "%s - %s"
            % (self.client_address[0], fmt % args),
            flush=True,
        )

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
                b"U1 MJPEG bridge\n"
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
        self.send_header(
            "Cache-Control",
            "no-store, no-cache, must-revalidate",
        )
        self.end_headers()
        self.wfile.write(data)

    def stream(self):
        self.send_response(200)
        self.send_header(
            "Content-Type",
            f"multipart/x-mixed-replace; boundary={BOUNDARY}",
        )
        self.send_header(
            "Cache-Control",
            "no-store, no-cache, must-revalidate",
        )
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
                        self.wfile.write(
                            b"Content-Type: image/jpeg\r\n"
                        )
                        self.wfile.write(
                            f"Content-Length: {len(data)}"
                            "\r\n\r\n".encode()
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


print(
    f"U1 MJPEG bridge listening on {HOST}:{PORT}",
    flush=True,
)
print(f"Source: {IMAGE}", flush=True)

watchdog = threading.Thread(
    target=camera_watchdog,
    name="u1-camera-watchdog",
    daemon=True,
)
watchdog.start()

unisrv_thread = threading.Thread(
    target=unisrv_watchdog,
    name="u1-camera-unisrv-watchdog",
    daemon=True,
)
unisrv_thread.start()

ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
