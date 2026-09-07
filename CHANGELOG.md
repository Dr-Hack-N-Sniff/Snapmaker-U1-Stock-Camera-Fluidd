# Changelog

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
