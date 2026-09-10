# Changelog

## v1.0.3 - 2026-09-09

### Changed

- Replaced normal periodic stale-frame monitor restarts with demand-based Fluidd camera wake.
- Fluidd now requests one stock LAN camera monitor start only when an active snapshot or stream request encounters a stale shared camera frame.
- Added a 30-second demand-wake cooldown and a bounded 3-second wait for a fresh frame to prevent repeated MQTT wake requests.
- Preserved the v1.0.2 WAN-session recovery fallback for failed stock-camera sessions.
- Updated camera-start logging to describe the action neutrally rather than attributing every request to the watchdog.
- Removed a duplicate `is_wan_start_log_line()` policy definition with no behavior change.
- Expanded release-safety regression checks for demand-based wake behavior.

### Hardware Testing

- A physical Snapmaker U1 was left with a stale shared camera source for approximately two hours. An active Fluidd request generated exactly one LAN wake request and immediately received a fresh frame.
- No repeating 90-second LAN restart loop occurred with the v1.0.3 bridge.
- Snapmaker Orca reconnected normally after its usual long-idle device/cloud timeout; its camera remained hibernated until Play was selected, then started normally.
- Fluidd remained live while Snapmaker Orca camera access was active.
- The Snapmaker mobile app camera also worked, including concurrent operation with Fluidd and Snapmaker Orca.
- After a normal U1 reboot, the camera bridge was started by the normal boot/service path and Fluidd camera access returned without an additional demand wake.

### Notes

- Demand-based wake reduces unnecessary interaction with Snapmaker's stock camera lifecycle while Fluidd is not being viewed.
- This release does not claim to modify or replace Snapmaker camera encryption, cloud services, or WAN session handling.
- The bridge does not restart `unisrv`, Klipper, Moonraker, or the printer.

## v1.0.2 - 2026-09-07

### Changed

- Improved coexistence between the Fluidd camera bridge and the stock Snapmaker camera service.
- Increased the stale-camera reset window to 90 seconds to avoid unnecessary monitor restarts.
- Added monitoring of stock WAN camera sessions using the U1 `unisrv` camera log.
- Added bounded recovery handling for short failed WAN camera sessions.
- Added protection against duplicate WAN start events resetting the recovery stability timer.
- Added a 10-minute recovery fallback so Fluidd camera access can recover if no stock camera session takes control.
- Added `u1_camera_policy.py` to separate camera recovery policy from the MJPEG bridge.
- Updated install and repair scripts to install, validate, and preserve the policy module.
- Expanded release-safety tests for the v1.0.2 camera recovery behavior.

### Hardware Testing

- Extended hardware testing included approximately six hours of printing with the Snapmaker mobile camera in use while desktop camera access remained stable.
- During recovery testing, a failed desktop camera session was allowed to fully reset before starting the camera from the Snapmaker mobile app.
- The mobile app successfully established a fresh stock camera session, after which camera access worked in both the mobile and desktop applications.
- Fluidd camera access continued to operate alongside the stock Snapmaker camera system during testing.

### Notes

- No nginx configuration changes are required.
- This release does not restart or modify `unisrv`, Klipper, Moonraker, or the printer firmware.
- The Snapmaker mobile app can be useful as a troubleshooting step after a stock camera session has fully reset, but it is not required for normal operation.
- Stock Snapmaker camera behavior can still be affected by the Snapmaker application, account, network, or cloud connectivity.
- v1.0.2 is designed to coexist with the stock Snapmaker camera system rather than replace it.

## v1.0.1 - 2026-09-06

- Added a watchdog for `/tmp/.monitor.jpg` frame freshness.
- Requests the stock `camera.start_monitor` RPC when frames remain stale for 15 seconds.
- Rate-limits recovery attempts to one every 15 seconds.
- Leaves `unisrv`, Klipper, Moonraker, and printer services untouched.
- Logs watchdog detection and recovery requests to the existing camera log.
- Hardware validation passed with four automatic camera recoveries.
- Retains v1.0.0 install, repair, recovery-kit, and uninstall safety behavior.

## v1.0.0

- Initial release of the Snapmaker U1 stock MIPI camera bridge for Fluidd.
