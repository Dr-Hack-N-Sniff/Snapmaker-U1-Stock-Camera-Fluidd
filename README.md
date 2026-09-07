# Snapmaker U1 Stock Camera Bridge for Fluidd

![U1 Stock Camera Bridge for Fluidd](images/u1-stock-camera-fluidd-v1.0.1.png)

**Unofficial community project — not affiliated with or endorsed by Snapmaker.**

A self-contained bridge that exposes the Snapmaker U1 built-in MIPI camera in Fluidd while retaining the stock camera service. No Raspberry Pi, external PC, Docker container, or replacement camera firmware is required.


## What it does

The U1 stock service (`unisrv`) captures the MIPI camera to `/tmp/.monitor.jpg`. This project starts the stock LAN monitor through the printer's local MQTT interface, serves that JPEG as an MJPEG/snapshot endpoint on `127.0.0.1:8080`, and uses the U1's existing nginx `/webcam/` proxy and Fluidd camera entry.

`MIPI camera -> unisrv -> /tmp/.monitor.jpg -> Python MJPEG bridge -> nginx /webcam/ -> Fluidd`

The camera has been physically verified at approximately 1 FPS and verified to return automatically after a U1 reboot.


## v1.0.2 camera coexistence and recovery

v1.0.2 improves coexistence between the Fluidd camera bridge and the stock Snapmaker camera system.

The stale-frame recovery window has been increased to **90 seconds** to avoid unnecessary monitor restarts during temporary interruptions.

The bridge also observes stock WAN camera sessions through the U1's `unisrv` camera log. When a short failed WAN camera session is detected, the bridge can release its LAN monitor request and allow the stock camera system to fully shut down before a fresh camera session is established.

During this recovery period, normal stale-frame restarts are suppressed so the Snapmaker camera gets the first opportunity to establish a fresh session. A **10-minute fallback** allows Fluidd camera recovery if no stock camera session takes control.

The bridge does **not** restart `unisrv`, Klipper, Moonraker, or the printer.


## Hardware testing

v1.0.2 has been tested on a physical Snapmaker U1 with Fluidd, **Snapmaker Orca**, and the Snapmaker mobile app.

Testing included approximately **six hours of printing** with the Snapmaker mobile camera in use while Snapmaker Orca camera access remained stable.

During a later recovery test, the camera in Snapmaker Orca experienced a short failed WAN session. v1.0.2 detected the failed session and released the LAN monitor. The stock camera system then completed a full shutdown.

During this hardware test, the complete shutdown took approximately **6 minutes**.

After the stock camera reached a fully stopped state, starting the camera from the Snapmaker mobile app established a fresh stock camera session. Camera access then worked in both the **Snapmaker mobile app and Snapmaker Orca**.

Fluidd camera access continued to operate alongside the stock Snapmaker camera system during testing.

![Built-in U1 camera working in Fluidd](images/u1-camera-fluidd-working.png)


## Snapmaker Orca camera troubleshooting

The Snapmaker camera depends on more than the local Fluidd bridge. Snapmaker Orca, the Snapmaker mobile app, account connectivity, network connectivity, and Snapmaker cloud services can also affect camera operation.

If the Snapmaker Orca camera fails to start, avoid repeatedly refreshing or restarting the camera while the stock camera session is resetting.

**A complete stock-camera reset can take approximately 6 minutes.**

If the Snapmaker Orca camera does not recover:

1. Stop or close the camera in Snapmaker Orca.
2. **Wait at least 6 minutes** for the stock camera session to fully reset. During hardware testing, a complete shutdown took approximately 6 minutes.
3. Open the Snapmaker mobile app and start the camera.
4. Confirm that the camera works in the mobile app.
5. Try the camera from Snapmaker Orca again.

During hardware testing, this procedure successfully established a fresh stock camera session and restored camera access in both the Snapmaker mobile app and Snapmaker Orca.

The Snapmaker mobile app is **not required for normal operation**. This is a troubleshooting procedure observed to work during testing, not a guaranteed fix for Snapmaker Orca, Snapmaker mobile app, account, network, or cloud-related camera failures.


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


## Install

Copy this release directory to the U1, SSH in as root, enter the directory, and run:

```sh
chmod +x install.sh
./install.sh
```

The installer copies the bridge and camera recovery policy to `/oem/printer_data/u1_camera/`, installs `/etc/init.d/S64u1-camera`, backs up the current `S99_bootcontrol`, and adds only the S64 startup line. It does **not** replace the printer's complete boot-control file and does not remove existing S62/S63 WLED services.


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
- v1.0.2 adds `u1_camera_policy.py` for camera recovery policy.
- No nginx configuration changes are required for v1.0.2.
- The bridge does not restart `unisrv`, Klipper, Moonraker, or the printer.
- Future Snapmaker firmware can change undocumented internal interfaces; use the compatibility checks rather than forcing a repair.


## Release

Current release: **v1.0.2**.

- **v1.0.2:** Improves coexistence with the stock Snapmaker camera, adds WAN-session-aware recovery, a 90-second stale-frame reset window, duplicate WAN-start protection, and a 10-minute recovery fallback.
- **v1.0.1:** Added stale-frame watchdog and rate-limited automatic `camera.start_monitor` recovery. Hardware-tested with four automatic recoveries.
- **v1.0.0:** Initial stock-camera Fluidd bridge release.


## 🖨️ Support the Project

<a href="https://buymeacoffee.com/hacknsniff">
  <img src="images/buy-me-a-roll-of-filament.png" alt="Buy me a roll of filament" width="600">
</a>


## Disclaimer

This is an **unofficial community project** and is not affiliated with, endorsed by, or supported by Snapmaker.

This project modifies startup configuration on the Snapmaker U1 and is provided **as-is**. Use it at your own risk. Modifications to your printer may affect support or warranty coverage.

This project does **not** distribute Snapmaker proprietary firmware files. It uses services and interfaces already present in the stock U1 firmware.
