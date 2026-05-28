# CoreLink Wear OS Scaffold

CoreLink is a native Wear OS MVP scaffold. This repo now contains a single wearable app module with a local-first placeholder gameplay loop:

- recovery opening and Core Matrix calibration
- deterministic starter bot creation
- one recovered AI core with persisted matrix metrics and starter stats
- dashboard for Charge, Scrap, condition, and mood
- shared-capacitor Charge gain from Wear OS step data when available
- deterministic simulated activity fallback when a watch sensor or emulator support is unavailable
- repair and roam demo loops
- low-power warning state
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

Current screenshot blocker on May 28, 2026:

- `adb devices` reports only `Medium_Phone`.
- `emulator -list-avds` reports only `Medium_Phone`.
- No Wear OS emulator or connected Wear OS device is currently available from this workspace, so watch-sized screenshot evidence could not be captured in this run.
