#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
REPAIR="$ROOT/repair.sh"
INSTALL="$ROOT/install.sh"

grep -q 'HERE=.*dirname' "$REPAIR" || { echo 'FAIL: repair.sh must resolve its own directory'; exit 1; }
grep -q 'SOURCE_DIR=' "$REPAIR" || { echo 'FAIL: repair.sh must select release or recovery source directory'; exit 1; }
! grep -q "sed -i '/\^\[\[:space:\]\]\*;;/i" "$REPAIR" || { echo 'FAIL: repair.sh uses broad ;; patch'; exit 1; }
! grep -q 'sed -i "/\^\[\[:space:\]\]\*;;/i' "$INSTALL" || { echo 'FAIL: install.sh uses broad ;; patch'; exit 1; }
grep -q 'patch_boot_start' "$REPAIR" || { echo 'FAIL: repair.sh lacks targeted boot patch function'; exit 1; }
grep -q 'patch_boot_start' "$INSTALL" || { echo 'FAIL: install.sh lacks targeted boot patch function'; exit 1; }
echo 'PASS: release safety checks'
grep -q 'install.sh repair.sh status.sh uninstall.sh u1_mjpeg_bridge.py S64u1-camera README.md' "$REPAIR" || { echo 'FAIL: repair.sh must seed the on-printer recovery kit when run from a release'; exit 1; }

# Regression: a stale monitor.jpg must not suppress start_monitor or count as success.
S64="$ROOT/S64u1-camera"
! grep -q 'while \[ ! -f "\$IMAGE" \]' "$S64" || { echo 'FAIL: stale JPEG prevents start_monitor request'; exit 1; }
! grep -q 'if \[ -f "\$IMAGE" \]; then[[:space:]]*$' "$S64" || true
grep -q 'stat -c %Y "\$IMAGE"' "$S64" || { echo 'FAIL: S64 does not verify JPEG freshness'; exit 1; }
grep -q 'NEW_MTIME.*LAST_MTIME' "$S64" || { echo 'FAIL: S64 does not require JPEG timestamp advancement'; exit 1; }
echo 'PASS: stale-JPEG regression checks'
