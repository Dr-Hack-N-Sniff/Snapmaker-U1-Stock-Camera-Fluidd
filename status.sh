#!/bin/sh
INIT=/etc/init.d/S64u1-camera
[ -x "$INIT" ] && "$INIT" status || echo 'Camera service is not installed.'
ss -ltnp 2>/dev/null | grep ':8080' || echo 'Port 8080 is not listening.'
if [ -f /tmp/.monitor.jpg ]; then stat -Lc 'Camera frame: %s bytes, %y' /tmp/.monitor.jpg; else echo 'Camera frame is unavailable.'; fi
