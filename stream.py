#!/usr/bin/env python3
"""
stream.py - Serve the Pi camera as video any browser can watch.

Nothing needs to be installed on the Windows side.


SETUP - run once on the Pi
--------------------------

    # Tailscale (opens a sign-in URL - use the same account as the laptop)
    curl -fsSL https://tailscale.com/install.sh | sh
    sudo tailscale up

    # Camera check - look for a line containing "imx708"
    rpicam-hello --list-cameras

    # Packages
    sudo apt update
    sudo apt install -y python3-picamera2 python3-venv

    # Virtual environment
    cd ~/drone-stream
    python3 -m venv --system-site-packages .venv
    source .venv/bin/activate

    --system-site-packages is REQUIRED. picamera2 relies on the libcamera
    bindings that ship with Raspberry Pi OS and are not available on PyPI,
    so a plain isolated venv will not be able to see the camera at all.


RUN
---

    source .venv/bin/activate      # needed in each new terminal
    python stream.py

    Then open the URL it prints in any browser on the laptop:
        http://<pi-tailscale-ip>:8000

    Ctrl-C to stop.
"""

import io
import socketserver
import subprocess
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

# ---- settings ----
WIDTH = 1280
HEIGHT = 720
FPS = 25
QUALITY = 75      # 50-90. Lower = less bandwidth.
PORT = 8000
# ------------------

PAGE = f"""<!DOCTYPE html>
<html><head><title>Drone feed</title>
<style>
 body{{background:#111;margin:0;display:flex;justify-content:center;align-items:center;
       height:100vh}}
 img{{max-width:100%;max-height:100%}}
</style></head>
<body><img src="stream.mjpg"></body></html>
"""


class Output(io.BufferedIOBase):
    """Holds the newest JPEG frame and wakes up any waiting viewers."""

    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


output = Output()


class Handler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            page = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(page))
            self.end_headers()
            self.wfile.write(page)

        elif self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Type",
                             "multipart/x-mixed-replace; boundary=FRAME")
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except Exception:
                pass   # viewer closed the tab

        else:
            self.send_error(404)

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def tailscale_ip():
    try:
        return subprocess.check_output(
            ["tailscale", "ip", "-4"], text=True, timeout=5).strip()
    except Exception:
        return None


def main():
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(
        main={"size": (WIDTH, HEIGHT)},
        controls={"FrameDurationLimits": (int(1e6 / FPS), int(1e6 / FPS))},
    ))
    picam2.start_recording(JpegEncoder(q=QUALITY), FileOutput(output))

    ip = tailscale_ip()
    print(f"\nStreaming {WIDTH}x{HEIGHT} @ {FPS}fps")
    if ip:
        print(f"Open this on your laptop:  http://{ip}:{PORT}")
    else:
        print(f"Open http://<pi-tailscale-ip>:{PORT} on your laptop")
    print("Ctrl-C to stop.\n")

    try:
        Server(("0.0.0.0", PORT), Handler).serve_forever()
    finally:
        picam2.stop_recording()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("stopped")
