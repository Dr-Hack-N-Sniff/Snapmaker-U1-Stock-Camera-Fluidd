# Changelog

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
