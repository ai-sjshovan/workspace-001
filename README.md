# CoreLink Wear OS Scaffold

CoreLink is a native Wear OS MVP scaffold. This repo now contains a single wearable app module with a local-first placeholder gameplay loop:

- recovery opening and Core Matrix calibration
- deterministic starter bot creation
- one recovered AI core with persisted matrix metrics and starter stats
- dashboard for Charge, Scrap, condition, and mood
- simulated activity-to-Charge gain
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

## Local Validation Status

Validation in this workspace is currently blocked by missing local Android build prerequisites:

- `java -version` failed on May 28, 2026 with `/bin/bash: java: command not found`
- `gradle -v` failed on May 28, 2026 with `/bin/bash: gradle: command not found`
- `./gradlew :app:assembleDebug` failed on May 28, 2026 with `JAVA_HOME is not set and no 'java' command could be found in your PATH`
- `ANDROID_SDK_ROOT` and `ANDROID_HOME` are unset
- a Windows Android SDK path exists at `/mnt/c/Users/Sjsho/AppData/Local/Android/Sdk`

Next unblock step:

1. Install or expose a JDK 17 runtime in this shell.
2. Export `ANDROID_SDK_ROOT=/mnt/c/Users/Sjsho/AppData/Local/Android/Sdk`.
3. Let Android Studio install the Wear OS SDK platform, build-tools, emulator, and a Wear OS AVD if they are not already present.
4. Re-run `./gradlew :app:assembleDebug` or launch the `app` run configuration from Android Studio.
