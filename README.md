# CoreLink Wear OS Scaffold

CoreLink is a native Wear OS MVP scaffold. This repo now contains a single wearable app module with a local-first placeholder gameplay loop:

- recovery opening and Core Matrix calibration
- deterministic starter bot creation
- one recovered AI core with persisted matrix metrics and starter stats
- watch-sized game scene with compact Charge, Scrap, condition, and mood HUD
- glanceable watch-status tile plus in-app status surface for quick command checks
- shared-capacitor Charge gain from Wear OS step data when available
- deterministic simulated activity fallback when a watch sensor or emulator support is unavailable
- repair and roam demo loops
- low-power warning state with persisted tuning timestamps
- local persistence across restart
- reset-demo-state control

## Project Layout

- `app/` Wear OS application module
- `app/src/main/java/com/corelink/wear/MainActivity.kt` placeholder MVP shell

## Run Path

Open this repo in Android Studio and run the `app` configuration on a Wear OS emulator or a connected Wear OS device.

CLI build command:

```bash
./gradlew :app:assembleDebug
```

Install on a connected emulator or device:

```bash
./gradlew :app:installDebug
```

Useful local checks when Android tooling is present:

```bash
adb devices
emulator -list-avds
```

## Reset Demo State

Open `Status`, then `Settings / Reset`, and confirm `Reset Demo State`. That clears the locally stored active core, its Core Matrix metrics, starter stats, Charge, Scrap, condition, mood, and the last roam report.

## Watch Status Tile

Core Link now registers a native Wear OS tile surface named `Core Link Status`.

- Add it from the watch-face tile carousel to glance Charge, Scrap, Condition, active mood, and roam readiness without replacing the main game scene.
- The tile reads the same persisted local state as the app scene and updates on a 60-second freshness interval.
- The in-app `WATCH STATUS` screen mirrors the same compact summary and links into `Settings / Reset`.

## Low Power MVP

- CoreLink enters Low Power whenever Charge drops below `15`.
- Low Power is visible on the dashboard and pauses roam dispatches until the capacitor is recharged.
- MVP does not implement permanent dead-core loss when power bottoms out.
- The app persists low-power state plus timestamp markers for low-power entry, charge changes, condition changes, roam start, repair, and the latest state sync so future passive drain and decay tuning has local data to build on.

## Deferred Beyond MVP

- dead-core permanence
- battles
- capture
- store
- multi-bot squad

## Activity To Charge

CoreLink stores Charge in the shared capacitor at the app-state level, not on individual bots.

- When a Wear OS step counter is available and `ACTIVITY_RECOGNITION` permission is granted, the dashboard listens for step updates and converts every `40` newly observed steps into `1` Charge.
- When the step sensor or emulator support is unavailable, use `Simulate Activity Burst` on the dashboard. It deterministically injects `400` simulated activity steps, which produces `+10` Charge through the same conversion rule.
- The dashboard Activity Feed readout shows whether Charge came from the Wear OS step sensor or the simulation fallback and reports the latest conversion result.

## Local Validation Status

The WSL shell does not expose Linux `java`, so the supported local proof path is
Windows Android tooling: Android Studio's bundled JBR plus the configured
Windows SDK.

Validated from this workspace on May 29, 2026:

```powershell
powershell.exe -NoProfile -Command '& {
  $ErrorActionPreference = "Stop"
  $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  $env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
  .\gradlew.bat :app:testDebugUnitTest :app:assembleDebug
  & "$env:ANDROID_HOME\platform-tools\adb.exe" devices
  & "$env:ANDROID_HOME\emulator\emulator.exe" -list-avds
}'
```

Observed result on May 29, 2026:

- `:app:testDebugUnitTest` passed and was up to date on the validated run.
- `:app:assembleDebug` passed and was up to date on the validated run.
- Debug artifact is produced at `app/build/outputs/apk/debug/app-debug.apk`.
- `adb.exe devices` printed `List of devices attached` with no connected Wear OS target underneath it.
- `emulator.exe -list-avds` reported `Medium_Phone` and `Wear_OS_XL_Round`.

Final launch and smoke path:

1. Open the repo in Android Studio on Windows so it uses the bundled JBR and configured Android SDK.
2. Start or connect a Wear OS target. `Wear_OS_XL_Round` is present locally, but it still needs to become an `adb`-attached device before app launch proof can complete.
3. Run the `app` configuration, complete recovery and calibration, use `Simulate Activity Burst` or a live step sensor to generate Charge, dispatch and recover a roam, spend Charge and Scrap on repair, then relaunch the app and confirm the persisted state.

Current launch blocker on May 29, 2026:

- The native Wear OS project builds and unit-tests successfully.
- A Wear OS AVD exists locally (`Wear_OS_XL_Round`), but the launch attempt in this workspace still left `adb.exe devices` empty after the emulator process started, so watch launch and tile interaction proof remain blocked by target attachment rather than app code.

## Acceptance Surface Map

- Recovery opening: `Begin Recovery` on the launch screen
- Core Matrix calibration: `Calibration` flow with four deterministic answers and `Calibrate Starter Bot`
- Active bot dashboard: `Dashboard` command surface, telemetry grid, and ops/activity readouts
- Charge, Scrap, condition panel: dashboard telemetry plus `Watch Status Surface`
- Repair action: `Repair -5 Charge / -3 Scrap`
- Roam dispatch and result: `Dispatch Roam -12 Charge`, countdown state, then `Recover Roam Haul`
- Glanceable watch status surface: `Core Link Status` tile plus `Watch Status`
- Settings and reset: `Watch Status` then `Settings / Reset` then confirm `Reset Demo State`
