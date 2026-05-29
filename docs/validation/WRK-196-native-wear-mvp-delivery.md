# WRK-196 Core Link Native Wear MVP Delivery

Date: May 29, 2026
Repo: `project/corelink`

## Scope

- Core Link OS boot and recovery flow on first launch
- One-question-at-a-time Core Matrix calibration into one starter AI core
- Single watch-sized scene with an animated pixel Nanobot Core and compact HUD
- Charge, Repair, Scan, and Roam command loop with local persistence
- Wear OS build, install, and launch proof on the local watch emulator

## Build And Unit Test Validation

Command run from this workspace:

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

Observed result:

- `:app:testDebugUnitTest` passed.
- `:app:assembleDebug` passed.
- Debug APK produced at `app/build/outputs/apk/debug/app-debug.apk`.
- `adb.exe devices` initially printed `List of devices attached` with no active target.
- `emulator.exe -list-avds` reported `Medium_Phone` and `Wear_OS_XL_Round`.

## Wear Emulator Install And Launch Proof

Command run from this workspace:

```powershell
powershell.exe -NoProfile -Command '& {
  $ErrorActionPreference = "Stop"
  $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  $env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
  $adb = Join-Path $env:ANDROID_HOME "platform-tools\adb.exe"
  $emulator = Join-Path $env:ANDROID_HOME "emulator\emulator.exe"
  Start-Process -FilePath $emulator -ArgumentList "-avd Wear_OS_XL_Round -no-snapshot-load -no-boot-anim" | Out-Null
  Start-Sleep -Seconds 35
  & $adb devices
  .\gradlew.bat :app:installDebug
  & $adb -s emulator-5554 shell am start -W -n com.corelink.wear/.MainActivity
  & $adb -s emulator-5554 shell pidof com.corelink.wear
  & $adb -s emulator-5554 shell getprop ro.build.characteristics
}'
```

Observed result:

- `adb.exe devices` showed `emulator-5554 device`.
- `:app:installDebug` installed successfully on `Wear_OS_XL_Round(AVD)`.
- `am start -W -n com.corelink.wear/.MainActivity` returned `Status: ok`.
- `pidof com.corelink.wear` returned a live process id, confirming the app was running after launch.
- `getprop ro.build.characteristics` returned `emulator,nosdcard,watch`, confirming the target was the watch emulator.

## Acceptance Coverage

- First launch boot/recovery: `RecoveryScreen()` reveals timed Core Link OS diagnostics beginning with `Initializing Core Link...` and shows owner unknown, memory lattice tampering, unstable AI core state, and connected recovered resources.
- Calibration flow: `CalibrationScreen()` presents one technical question at a time and writes one deterministic starter AI core into local state through `starterStateFromAnswers(...)`.
- Single-scene HUD: `GameSceneScreen()` keeps Charge, Scrap, and Condition compact while the main visual focus stays on the central `PixelScene(...)`.
- Animated pixel Nanobot Core: `PixelScene(...)` renders idle pulse, scan, low-power flicker, repair glow, roam drift, and recovered glow states.
- Charge from activity: `applyWearStepSample(...)` converts live watch steps into Charge, and the `Charge` command uses `applySimulatedActivityBurst(...)` as the deterministic fallback.
- Repair consumes Scrap and Charge: `repairBot(...)` spends `5` Charge and `3` Scrap for `+12` Condition.
- Roam consumes Charge and returns Scrap: `dispatchRoam(...)` spends `12` Charge, then `resolveRoamReturn(...)` returns deterministic Scrap and progress after the roam timer completes.
- Local persistence: `CoreLinkPrefs` stores the full `CoreLinkState` through `CoreLinkStateCodec`, including the recovered core, timers, activity carryover, and warning state.
- Glanceable watch status and reset: `CoreLinkStatusTileService`, `WatchStatusScreen()`, and `SettingsScreen()` provide the tile, mirrored summary surface, and reset-demo-state flow without replacing the main scene.

## Residual Notes

- The validation run emitted existing deprecation warnings from `CoreLinkStatusTileService.kt` around deprecated tile resource APIs, but they did not block build, install, or launch for this issue.
