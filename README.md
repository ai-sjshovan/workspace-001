# CoreLink Wear OS Scaffold

CoreLink is a native Wear OS MVP scaffold. This repo now contains a single wearable app module with a local-first placeholder gameplay loop:

- recovery opening and Core Matrix calibration
- deterministic starter bot creation
- one recovered AI core with persisted matrix metrics and starter stats
- dashboard for Charge, Scrap, condition, and mood
- glanceable watch-status surface for quick command checks
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

Open `Settings / Reset` in the watch app, then tap `Reset Demo State`. That clears the locally stored active core, its Core Matrix metrics, starter stats, Charge, Scrap, condition, mood, and the last roam report.

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

The WSL shell does not expose Linux `java`, but the project validates through
Android Studio's bundled Windows JBR and SDK.

Validated on May 28, 2026:

```powershell
$env:JAVA_HOME="C:\Program Files\Android\Android Studio\jbr"
$env:ANDROID_HOME="C:\Users\Sjsho\AppData\Local\Android\Sdk"
$env:ANDROID_SDK_ROOT=$env:ANDROID_HOME
.\gradlew.bat :app:testDebugUnitTest
.\gradlew.bat :app:assembleDebug
```

Both commands completed successfully after Gradle installed the required SDK 36
platform and build tools into the configured Android SDK.

Final launch path on May 28, 2026:

1. Open the repo in Android Studio on Windows so it uses the bundled JBR and configured Android SDK.
2. Run the `app` configuration on a Wear OS emulator or connected Wear OS device.
3. Calibrate one starter bot, dispatch/return a roam, trigger Low Power by draining Charge below `15`, close the app, then relaunch and confirm bot, Charge, Scrap, condition, roam state, repair state, and Low Power all persist.

Current screenshot blocker on May 28, 2026:

- `adb.exe devices` reports no connected devices.
- `emulator.exe -list-avds` reports only `Medium_Phone`.
- No Wear OS emulator or connected Wear OS device is currently available from this workspace, so native watch launch and watch-sized screenshot evidence remain blocked by local tooling inventory rather than app code.

## Acceptance Surface Map

- Recovery opening: `Begin Recovery` on the launch screen
- Core Matrix calibration: `Calibration` flow with four deterministic answers and `Calibrate Starter Bot`
- Active bot dashboard: `Dashboard` command surface, telemetry grid, and ops/activity readouts
- Charge, Scrap, condition panel: dashboard telemetry plus `Watch Status Surface`
- Repair action: `Repair -5 Charge / -3 Scrap`
- Roam dispatch and result: `Dispatch Roam -12 Charge`, countdown state, then `Recover Roam Haul`
- Glanceable watch status surface: `Watch Status Surface`
- Settings and reset: `Settings / Reset` then `Reset Demo State`
