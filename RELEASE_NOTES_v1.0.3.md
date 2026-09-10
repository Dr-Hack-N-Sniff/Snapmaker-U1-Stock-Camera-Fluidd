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
