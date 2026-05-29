# WRK-194 Core Link Pixel Scene Evidence

Date: 2026-05-29
Repo: `project/corelink`

## Result

Core Link's Wear OS MVP was reworked from a dashboard-first layout into a
single-screen pixel game scene with a Core Link OS recovery boot flow, a
one-question-at-a-time calibration flow, animated pixel companion states, and
bottom command controls for Charge, Repair, Roam, and Scan.

## Build And Test Validation

Command run from this workspace:

```powershell
powershell.exe -NoProfile -Command '& {
  $ErrorActionPreference = "Stop"
  $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  $env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
  .\gradlew.bat :app:testDebugUnitTest :app:assembleDebug
}'
```

Observed result:

- `:app:testDebugUnitTest` passed.
- `:app:assembleDebug` passed.
- Added coverage for the new `Scan` command path in `CoreLinkModelTest`.

## Wear Launch Validation

Commands run from this workspace:

```powershell
powershell.exe -NoProfile -Command '& {
  $ErrorActionPreference = "Stop"
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  & "$env:ANDROID_HOME\platform-tools\adb.exe" devices
  & "$env:ANDROID_HOME\emulator\emulator.exe" -list-avds
}'
```

```powershell
powershell.exe -NoProfile -Command '& {
  $ErrorActionPreference = "Stop"
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  Start-Process -FilePath "$env:ANDROID_HOME\emulator\emulator.exe" -ArgumentList "-avd Wear_OS_XL_Round -no-snapshot-load"
}'
```

```powershell
powershell.exe -NoProfile -Command '& {
  $ErrorActionPreference = "Stop"
  $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  $env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
  .\gradlew.bat :app:installDebug
  & "$env:ANDROID_HOME\platform-tools\adb.exe" -s emulator-5554 shell am start -W -n com.corelink.wear/.MainActivity
  & "$env:ANDROID_HOME\platform-tools\adb.exe" -s emulator-5554 shell pidof com.corelink.wear
}'
```

Observed result:

- `adb devices` initially showed no running watch target.
- `emulator -list-avds` showed `Wear_OS_XL_Round` as an installed Wear AVD.
- The emulator reached `emulator-5554 device`.
- `adb shell getprop ro.build.characteristics` returned `emulator,nosdcard,watch`.
- `:app:installDebug` succeeded on `Wear_OS_XL_Round(AVD)`.
- `am start -W` returned `Status: ok`.
- `pidof com.corelink.wear` returned `2294`, confirming the app was running on the Wear emulator after launch.

## Visual Evidence

Captured screenshot:

- `docs/validation/WRK-194-wear-scene.png`

Observed scene details from the implementation and emulator capture:

- First-run flow is a timed Core Link OS diagnostic boot with scrolling log lines beginning `Initializing Core Link...`.
- Diagnostics explicitly include owner unknown, memory lattice tampering, unstable AI core state, and the two connected resources.
- Recovery transitions into one-question-at-a-time technical calibration prompts.
- Main surface is a watch-sized scene with a centered animated pixel Nanobot Core instead of stacked dashboard cards.
- Bottom command surface is limited to `Charge`, `Repair`, `Roam`, and `Scan`, each with a lightweight pixel icon and short label.
- HUD data for Charge, Scrap, and Condition remains compact and secondary to the scene.

## Guarded Device Feedback

- Haptic feedback uses `ViewCompat.performHapticFeedback(...)` through compatibility constants.
- Lightweight sound cues use `ToneGenerator` and are wrapped in `runCatching` so unsupported devices do not crash.
- Step-sensor access remains optional and guarded by runtime permission checks plus simulator fallback.
