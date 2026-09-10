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

grep -q 'install.sh repair.sh status.sh uninstall.sh u1_mjpeg_bridge.py u1_camera_policy.py S64u1-camera README.md CHANGELOG.md' "$REPAIR" || {
  echo 'FAIL: repair.sh must seed the on-printer recovery kit when run from a release'
  exit 1
}

# Regression: a stale monitor.jpg must not suppress start_monitor or count as success.
S64="$ROOT/S64u1-camera"
! grep -q 'while \[ ! -f "\$IMAGE" \]' "$S64" || { echo 'FAIL: stale JPEG prevents start_monitor request'; exit 1; }
! grep -q 'if \[ -f "\$IMAGE" \]; then[[:space:]]*$' "$S64" || true
grep -q 'stat -c %Y "\$IMAGE"' "$S64" || { echo 'FAIL: S64 does not verify JPEG freshness'; exit 1; }
grep -q 'NEW_MTIME.*LAST_MTIME' "$S64" || { echo 'FAIL: S64 does not require JPEG timestamp advancement'; exit 1; }
echo 'PASS: stale-JPEG regression checks'

# v1.0.2 watchdog and WAN-session regression requirements.
BRIDGE="$ROOT/u1_mjpeg_bridge.py"
POLICY="$ROOT/u1_camera_policy.py"

grep -q 'RESET_WINDOW = 90.0' "$POLICY" || { echo 'FAIL: policy lacks 90-second reset window'; exit 1; }
grep -q 'WAN_RECOVERY_FALLBACK = 600.0' "$POLICY" || { echo 'FAIL: policy lacks WAN recovery fallback'; exit 1; }
grep -q 'WAN_FAILURE_THRESHOLD = 15.0' "$POLICY" || { echo 'FAIL: policy lacks WAN failure threshold'; exit 1; }

grep -q 'camera.start_monitor' "$BRIDGE" || { echo 'FAIL: bridge cannot request stock monitor recovery'; exit 1; }
grep -q 'camera.stop_monitor' "$BRIDGE" || { echo 'FAIL: bridge cannot release stock LAN monitor'; exit 1; }
grep -q 'unisrv_watchdog' "$BRIDGE" || { echo 'FAIL: bridge lacks WAN-session watcher'; exit 1; }
grep -q 'next_wan_start_time' "$BRIDGE" || { echo 'FAIL: bridge lacks duplicate WAN-start protection'; exit 1; }
grep -q 'camera_watchdog' "$BRIDGE" || { echo 'FAIL: bridge lacks camera watchdog'; exit 1; }

echo 'PASS: v1.0.2 watchdog and WAN-session checks'

# v1.0.2 policy-module release requirements.
[ -f "$POLICY" ] || { echo 'FAIL: v1.0.2 policy module is missing from release'; exit 1; }
grep -q 'u1_camera_policy.py' "$INSTALL" || { echo 'FAIL: install.sh does not install u1_camera_policy.py'; exit 1; }
grep -q 'u1_camera_policy.py' "$REPAIR" || { echo 'FAIL: repair.sh does not restore u1_camera_policy.py'; exit 1; }

echo 'PASS: v1.0.2 policy release checks'

# v1.0.3 demand-based wake regression requirements.
grep -q 'WAKE_COOLDOWN = 30.0' "$BRIDGE" || { echo 'FAIL: bridge lacks demand-wake cooldown'; exit 1; }
grep -q 'WAKE_WAIT = 3.0' "$BRIDGE" || { echo 'FAIL: bridge lacks bounded demand-wake wait'; exit 1; }
grep -q 'def ensure_camera_awake' "$BRIDGE" || { echo 'FAIL: bridge lacks demand-based wake helper'; exit 1; }
grep -q 'Fluidd requested stale camera source' "$BRIDGE" || { echo 'FAIL: bridge lacks stale-demand wake path'; exit 1; }
grep -q 'Fluidd demand wake received a fresh camera frame' "$BRIDGE" || { echo 'FAIL: bridge lacks fresh-frame confirmation'; exit 1; }
grep -q 'Normal stale-source recovery is intentionally demand-driven' "$BRIDGE" || { echo 'FAIL: background stale recovery is not demand-driven'; exit 1; }
! grep -q 'reset window complete, restarting stock monitor' "$BRIDGE" || { echo 'FAIL: old periodic stale restart path remains'; exit 1; }
grep -q 'ensure_camera_awake()' "$BRIDGE" || { echo 'FAIL: HTTP camera requests do not invoke demand wake'; exit 1; }
[ "$(grep -c '^def is_wan_start_log_line' "$POLICY")" -eq 1 ] || { echo 'FAIL: WAN-start policy definition must appear exactly once'; exit 1; }
echo 'PASS: v1.0.3 demand-based wake checks'
