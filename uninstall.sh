#!/bin/sh
set -eu
INIT=/etc/init.d/S64u1-camera
BOOT=/etc/init.d/S99_bootcontrol
[ "$(id -u)" = 0 ] || { echo 'ERROR: Run as root.'; exit 1; }
[ -x "$INIT" ] && "$INIT" stop || true
if [ -f "$BOOT" ]; then sed -i '\|/etc/init.d/S64u1-camera start|d' "$BOOT"; sh -n "$BOOT"; fi
rm -f "$INIT"
echo 'Camera bridge removed. Recovery files under /oem/printer_data/u1_camera were preserved.'
