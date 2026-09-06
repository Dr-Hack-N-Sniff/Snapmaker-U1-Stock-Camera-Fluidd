#!/bin/sh
set -eu
BASE=/oem/printer_data/u1_camera
REC="$BASE/recovery"
INIT=/etc/init.d/S64u1-camera
BOOT=/etc/init.d/S99_bootcontrol
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LINE='        /etc/init.d/S64u1-camera start'

fail(){ echo "ERROR: $*"; echo 'No stock boot configuration was changed.'; exit 1; }

patch_boot_start() {
    src=$1
    dst=$2
    awk -v line="$LINE" '
      BEGIN { in_start=0; inserted=0; found_start=0 }
      /^[[:space:]]*start\)/ { in_start=1; found_start++; print; next }
      in_start && /^[[:space:]]*;;[[:space:]]*$/ {
        if (!inserted) { print line; inserted=1 }
        in_start=0
        print
        next
      }
      { print }
      END { if (found_start != 1 || inserted != 1) exit 42 }
    ' "$src" > "$dst" || return 1
}

[ "$(id -u)" = 0 ] || fail 'Run as root.'
for f in "$HERE/u1_mjpeg_bridge.py" "$HERE/S64u1-camera" "$BOOT"; do
  [ -f "$f" ] || fail "Missing required file: $f"
done
command -v mosquitto_pub >/dev/null 2>&1 || fail 'mosquitto_pub not found; unsupported firmware.'
command -v awk >/dev/null 2>&1 || fail 'awk not found; cannot safely patch boot configuration.'
[ -x /usr/bin/unisrv ] || fail '/usr/bin/unisrv not found; unsupported firmware.'
[ -f /etc/nginx/sites-available/fluidd ] || fail 'Fluidd nginx configuration is missing.'
grep -q 'mjpgstreamer1' /etc/nginx/sites-available/fluidd || fail 'Expected Fluidd webcam upstream is missing.'
grep -q '^[[:space:]]*start)' "$BOOT" || fail 'Expected start) section not found in S99_bootcontrol.'

TMP="/tmp/S99_bootcontrol.camera.$$"
trap 'rm -f "$TMP"' EXIT
if grep -Fq '/etc/init.d/S64u1-camera start' "$BOOT"; then
  cp "$BOOT" "$TMP"
else
  patch_boot_start "$BOOT" "$TMP" || fail 'Could not safely identify exactly one start) branch in S99_bootcontrol.'
fi
sh -n "$TMP" || fail 'Proposed S99_bootcontrol patch failed syntax validation.'
sh -n "$HERE/S64u1-camera" || fail 'S64 service failed syntax validation.'
python3 -m py_compile "$HERE/u1_mjpeg_bridge.py" || fail 'Python bridge failed validation.'

mkdir -p "$REC"
STAMP=$(date +%Y%m%d%H%M%S)
cp "$BOOT" "$REC/S99_bootcontrol.pre-camera.$STAMP"
cp "$HERE/u1_mjpeg_bridge.py" "$BASE/u1_mjpeg_bridge.py"
cp "$HERE/S64u1-camera" "$INIT"
chmod 755 "$BASE/u1_mjpeg_bridge.py" "$INIT"
if ! cmp -s "$BOOT" "$TMP"; then
  cp "$TMP" "$BOOT"
fi
cp "$HERE/install.sh" "$HERE/repair.sh" "$HERE/status.sh" "$HERE/uninstall.sh" \
   "$HERE/u1_mjpeg_bridge.py" "$HERE/S64u1-camera" "$HERE/README.md" "$REC/"
chmod 755 "$REC"/*.sh "$REC/S64u1-camera" "$REC/u1_mjpeg_bridge.py"
"$INIT" restart
echo "Installed. Recovery kit saved to $REC"
echo 'Open Fluidd and configure UI Camera per README.md.'
