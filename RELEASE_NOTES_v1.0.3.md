# v1.0.4 - Snapmaker U1 Firmware 2.0.0 Compatibility

v1.0.4 validates the existing camera bridge and recovery system on **Snapmaker U1 firmware 2.0.0**.

No camera streaming or demand-wake behavior has changed from v1.0.3.

## Hardware validation

Tested on a physical Snapmaker U1 during an actual firmware upgrade from **1.6.0 to 2.0.0**:

- Persistent camera files under `/oem/printer_data/u1_camera/` survived the firmware update.
- Firmware 2.0.0 removed the live `/etc/init.d/S64u1-camera` service.
- The firmware update replaced `S99_bootcontrol`, removing the S64 camera startup hook.
- The existing recovery kit under `/oem/printer_data/u1_camera/recovery/` survived.
- The existing `repair.sh` successfully validated the firmware 2.0.0 environment before making changes.
- `S64u1-camera` was restored.
- The repair safely added the camera startup hook to firmware 2.0.0's **current** `S99_bootcontrol`.
- `/etc/init.d/S64u1-camera start` was verified in the current boot configuration.
- The Fluidd **UI Camera** feed was physically verified working normally after recovery.

## Recovery after firmware 2.0.0

If a firmware update removes the camera service or boot hook, use the existing recovery kit:

```sh
cd /oem/printer_data/u1_camera/recovery
./repair.sh



# v1.0.3 - Demand-Based Camera Wake

v1.0.3 changes normal Fluidd camera recovery from periodic background monitor restarts to **demand-based wake**.

When an active Fluidd snapshot or stream request encounters a stale shared camera frame, the bridge requests one stock LAN camera monitor start, waits briefly for a fresh frame, and applies a cooldown to avoid repeated MQTT wake requests. When Fluidd is not being viewed, normal stale-frame recovery leaves Snapmaker's camera lifecycle alone.

## Hardware validation

Tested on a physical Snapmaker U1:

- Approximately two hours of stale camera-source time before Fluidd demand recovery.
- Exactly one demand-based LAN wake restored fresh Fluidd frames.
- No repeating 90-second LAN restart loop with the v1.0.3 bridge.
- Snapmaker Orca camera playback continued to work normally.
- Snapmaker mobile app camera playback continued to work normally.
- Fluidd, Snapmaker Orca, and the mobile app were verified working concurrently.
- A normal U1 reboot started the modified bridge through the normal service path; Fluidd camera access returned without another demand wake.

## Also changed

- Preserves the v1.0.2 WAN-session-aware recovery fallback.
- Uses a 30-second demand-wake cooldown and a bounded 3-second fresh-frame wait.
- Clarifies the stock LAN monitor-start log message.
- Removes a duplicate `is_wan_start_log_line()` definition from the policy module with no behavior change.
- Adds v1.0.3 release-safety regression checks.

This release does not modify or replace Snapmaker camera encryption or cloud services and does not restart `unisrv`, Klipper, Moonraker, or the printer.
