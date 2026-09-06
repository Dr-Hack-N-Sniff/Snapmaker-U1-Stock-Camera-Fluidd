# Snapmaker U1 Stock Camera Bridge for Fluidd

A self-contained bridge that exposes the Snapmaker U1 built-in MIPI camera in Fluidd while retaining the stock camera service. No Raspberry Pi, external PC, Docker container, or replacement camera firmware is required.

## What it does

The U1 stock service (`unisrv`) captures the MIPI camera to `/tmp/.monitor.jpg`. This project starts the stock LAN monitor through the printer's local MQTT interface, serves that JPEG as an MJPEG/snapshot endpoint on `127.0.0.1:8080`, and uses the U1's existing nginx `/webcam/` proxy and Fluidd camera entry.

`MIPI camera -> unisrv -> /tmp/.monitor.jpg -> Python MJPEG bridge -> nginx /webcam/ -> Fluidd`

The camera has been physically verified at approximately 1 FPS and verified to return automatically after a U1 reboot.

![Built-in U1 camera working in Fluidd](images/u1-camera-fluidd-working.png)

## Fluidd camera settings

Edit the existing **UI Camera** entry:

- Enabled: On
- Stream type: **MJPEG Adaptive**
- FPS Target: **1**
- FPS Target when not in focus: **1**
- Camera URL Stream: `/webcam/?action=stream`
- Camera URL Snapshot: `/webcam/?action=snapshot`
- Flip horizontal/vertical: Off unless desired
- Rotation: None unless desired

![Fluidd camera settings](images/fluidd-camera-settings.png)

## Unofficial Community Project

This project is not affiliated with, endorsed by, or supported by Snapmaker.

It modifies startup configuration on the Snapmaker U1 and is provided as-is. Use it at your own risk. Modifications to your printer may affect support or warranty coverage.

This project does not distribute Snapmaker proprietary firmware files.

## Install

Copy this release directory to the U1, SSH in as root, enter the directory, and run:

```sh
chmod +x install.sh
./install.sh
```

The installer copies the bridge to `/oem/printer_data/u1_camera/`, installs `/etc/init.d/S64u1-camera`, backs up the current `S99_bootcontrol`, and adds only the S64 startup line. It does **not** replace the printer's complete boot-control file and does not remove existing S62/S63 WLED services.

## Status

```sh
./status.sh
```

## Firmware updates and recovery

Firmware updates may replace `/etc/init.d/S64u1-camera` or remove the S64 boot hook. A recovery copy is stored under `/oem/printer_data/u1_camera/recovery/`.

After an update, use:

```sh
cd /oem/printer_data/u1_camera/recovery
./repair.sh
```
### After a Snapmaker Firmware Update

Do not blindly restore older configuration files after a firmware update.

Run the included compatibility and repair checks first. The repair process follows:

**Detect → Validate → Back up → Repair**

If the compatibility checks fail, stop and check this repository for an updated release. The repair system is intentionally designed to avoid forcing an older Snapmaker boot configuration onto firmware it does not recognize.

### Compatibility safety

`repair.sh` follows **detect -> validate -> back up -> repair**. It first verifies the stock `unisrv`, local MQTT tooling, Fluidd/nginx webcam plumbing, and expected `S99_bootcontrol` structure. If those dependencies no longer match, it stops rather than blindly applying an old configuration.

**Never restore an old `S99_bootcontrol` over a newer Snapmaker firmware.** The repair script patches the current firmware's boot file only after compatibility checks pass.

## Uninstall

```sh
./uninstall.sh
```

This stops/removes S64 and removes only its boot-hook line. Recovery files are intentionally preserved.

## Notes

- Designed for the stock Snapmaker U1 software stack observed during development.
- Uses Python standard library only for the MJPEG bridge.
- Uses the printer's existing Mosquitto/unisrv camera RPC interface.
- No private/local IP address is hard-coded in this project.
- Future Snapmaker firmware can change undocumented internal interfaces; use the compatibility checks rather than forcing a repair.

## Release

Initial release: **v1.0.0**.
