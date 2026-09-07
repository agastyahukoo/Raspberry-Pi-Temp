#!/usr/bin/env bash
# Streams the Pi camera to a laptop over Tailscale.

LAPTOP_IP="100.200.201.202"   # <-- CHANGE THIS. Run 'tailscale ip -4' on Windows.
PORT=5000

WIDTH=1280
HEIGHT=720
FPS=25
BITRATE=2000000               # 2 Mbit/s. Lower this first if video breaks up.

# 1128 fits inside Tailscale's 1280-byte tunnel MTU. Do not increase it.
PKT_SIZE=1128

exec rpicam-vid -t 0 -n --low-latency \
    --width "$WIDTH" --height "$HEIGHT" --framerate "$FPS" \
    --bitrate "$BITRATE" \
    --intra "$FPS" \
    --inline \
    --codec libav --libav-format mpegts \
    -o "udp://${LAPTOP_IP}:${PORT}?pkt_size=${PKT_SIZE}"
