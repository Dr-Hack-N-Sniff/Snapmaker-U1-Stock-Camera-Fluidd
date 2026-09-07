#!/bin/sh
set -eu
BASE=/oem/printer_data/u1_camera
REC="$BASE/recovery"
INIT=/etc/init.d/S64u1-camera
BOOT=/etc/init.d/S99_bootcontrol
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LINE='        /etc/init.d/S64u1-camera start'
SOURCE_DIR="$HERE"

fail(){ echo "ERROR: $*"; echo 'No compatibility repair was forced. Check GitHub for an updated release.'; exit 1; }

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
# repair.sh may be run directly from an extracted release or from the on-printer recovery kit.
if [ ! -f "$SOURCE_DIR/S64u1-camera" ] || [ ! -f "$SOURCE_DIR/u1_mjpeg_bridge.py" ] || [ ! -f "$SOURCE_DIR/u1_camera_policy.py" ]; then
  SOURCE_DIR="$REC"
fi
[ -f "$SOURCE_DIR/S64u1-camera" ] || fail 'Recovery S64u1-camera is missing.'
[ -f "$SOURCE_DIR/u1_mjpeg_bridge.py" ] || fail 'Recovery Python bridge is missing.'
[ -f "$SOURCE_DIR/u1_camera_policy.py" ] || fail 'Recovery camera policy module is missing.'
[ -x /usr/bin/unisrv ] || fail '/usr/bin/unisrv is missing; firmware camera stack changed.'
command -v mosquitto_pub >/dev/null 2>&1 || fail 'mosquitto_pub is missing; local MQTT interface changed.'
command -v awk >/dev/null 2>&1 || fail 'awk is missing; cannot safely patch boot configuration.'
[ -f /etc/nginx/sites-available/fluidd ] || fail 'Fluidd nginx configuration is missing.'
grep -q 'mjpgstreamer1' /etc/nginx/sites-available/fluidd || fail 'Expected Fluidd webcam upstream is missing.'
[ -f "$BOOT" ] || fail 'S99_bootcontrol is missing.'
grep -q '^[[:space:]]*start)' "$BOOT" || fail 'S99_bootcontrol no longer has the expected start) structure.'

# Build and validate the proposed boot file before modifying any stock configuration.
TMP="/tmp/S99_bootcontrol.camera-repair.$$"
trap 'rm -f "$TMP"' EXIT
if grep -Fq '/etc/init.d/S64u1-camera start' "$BOOT"; then
  cp "$BOOT" "$TMP"
else
  patch_boot_start "$BOOT" "$TMP" || fail 'Could not safely identify exactly one start) branch in S99_bootcontrol.'
fi
sh -n "$TMP" || fail 'Proposed S99_bootcontrol patch failed syntax validation.'
sh -n "$SOURCE_DIR/S64u1-camera" || fail 'Recovery S64 service failed syntax validation.'
python3 -m py_compile "$SOURCE_DIR/u1_mjpeg_bridge.py" "$SOURCE_DIR/u1_camera_policy.py" || fail 'Recovery camera files failed Python validation.'

mkdir -p "$REC"
if [ "$SOURCE_DIR" != "$REC" ]; then
  for f in install.sh repair.sh status.sh uninstall.sh u1_mjpeg_bridge.py u1_camera_policy.py S64u1-camera README.md CHANGELOG.md; do
    [ -f "$SOURCE_DIR/$f" ] && cp "$SOURCE_DIR/$f" "$REC/"
  done
  chmod 755 "$REC"/*.sh "$REC/S64u1-camera" "$REC/u1_mjpeg_bridge.py" 2>/dev/null || true
fi
STAMP=$(date +%Y%m%d%H%M%S)
cp "$BOOT" "$REC/S99_bootcontrol.before-repair.$STAMP"
cp "$SOURCE_DIR/S64u1-camera" "$INIT"
cp "$SOURCE_DIR/u1_mjpeg_bridge.py" "$BASE/u1_mjpeg_bridge.py"
cp "$SOURCE_DIR/u1_camera_policy.py" "$BASE/u1_camera_policy.py"
chmod 755 "$INIT" "$BASE/u1_mjpeg_bridge.py"
chmod 644 "$BASE/u1_camera_policy.py"
if ! cmp -s "$BOOT" "$TMP"; then
  cp "$TMP" "$BOOT"
fi
"$INIT" restart
echo 'Repair complete.'
