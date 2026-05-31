# WRK-199 Native Wear Boot, Calibration, And Single-Scene Loop

Date: June 1, 2026
Repo: `project/corelink`

## Result

Core Link's existing native Wear OS implementation already satisfies the
`WRK-199` acceptance slice. On `Wear_OS_XL_Round`, the app built, installed,
and launched through the native watch path; a cleared first launch showed the
Core Link OS recovery boot, exposed the recover prompt, advanced into the
calibration handoff, and reached the `CORE MATRIX` question flow.

No web substitute, WebView, or phone-only fallback was used.

## Build, Install, And Launch Validation

Command run from this workspace:

```powershell
powershell.exe -NoProfile -Command '& {
  $ErrorActionPreference = "Stop"
  $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  $env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
  $adb = Join-Path $env:ANDROID_HOME "platform-tools\adb.exe"
  $emulator = Join-Path $env:ANDROID_HOME "emulator\emulator.exe"
  & $adb devices
  & $emulator -list-avds
  Start-Process -FilePath $emulator -ArgumentList "-avd Wear_OS_XL_Round -no-snapshot-load -no-boot-anim" | Out-Null
  Start-Sleep -Seconds 35
  & $adb devices
  .\gradlew.bat :app:testDebugUnitTest :app:assembleDebug :app:installDebug
  & $adb -s emulator-5554 shell am start -W -n com.corelink.wear/.MainActivity
  & $adb -s emulator-5554 shell pidof com.corelink.wear
  & $adb -s emulator-5554 shell getprop ro.build.characteristics
}'
```

Observed result:

- `emulator.exe -list-avds` reported `Medium_Phone` and `Wear_OS_XL_Round`.
- `adb.exe devices` showed `emulator-5554 device` after the Wear emulator booted.
- `:app:testDebugUnitTest` passed.
- `:app:assembleDebug` passed.
- `:app:installDebug` installed successfully on `Wear_OS_XL_Round(AVD)`.
- `am start -W -n com.corelink.wear/.MainActivity` returned `Status: ok`.
- `pidof com.corelink.wear` returned a live process id.
- `getprop ro.build.characteristics` returned `emulator,nosdcard,watch`.

## Cold-Start Recovery And Calibration Evidence

Commands run from this workspace:

```powershell
powershell.exe -NoProfile -Command '& {
  $ErrorActionPreference = "Stop"
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  $adb = Join-Path $env:ANDROID_HOME "platform-tools\adb.exe"
  & $adb -s emulator-5554 shell pm clear com.corelink.wear
  & $adb -s emulator-5554 shell am start -W -n com.corelink.wear/.MainActivity
  Start-Sleep -Seconds 8
  & $adb -s emulator-5554 shell uiautomator dump /sdcard/corelink-uix.xml | Out-Null
  & $adb -s emulator-5554 shell cat /sdcard/corelink-uix.xml
}'
```

Observed first-launch UI dump included:

- `CORE LINK OS`
- `BOOT`
- `Recovered watch node entering recovery mode.`
- `Initializing Core Link...`
- `[0001] OWNER PROFILE ........ UNKNOWN`
- `[0002] MEMORY LATTICE ...... TAMPERED`
- `[0003] AI CORE STATE ...... UNSTABLE`

After scrolling the watch-sized recovery surface, the same cleared session
showed:

- `[0004] NANOBOT CONTAINER ... FULL`
- `[0005] CONNECTED RESOURCE .. 1x AI Core`
- `[0006] CONNECTED RESOURCE .. 1x Nanobot Container (Full)`
- `[0007] RECOVERY CHANNEL .... READY`
- `Recover available items?`
- `Recover`
- `Defer`

After tapping `Recover` and scrolling again, the runtime UI dump showed:

- `[A-11] Recovering cached items into quarantine buffer...`
- `[A-12] AI core shell responding to low-band handshake...`
- `[A-13] Core Matrix calibration required before deployment.`
- `AI core ready for calibration.`
- `Begin Calibration`

After tapping `Begin Calibration`, the runtime UI dump showed:

- `CORE MATRIX`
- `1/4`
- `Failsafe Priority`
- `A lattice spike trips in the deadband. Which routine does Core Link pin first?`

## Acceptance Surface Mapping

- First-launch Core Link OS recovery boot: `RecoveryScreen()` in `MainActivity.kt`
- One-question-at-a-time deterministic calibration: `CalibrationScreen()` in `MainActivity.kt` plus `starterStateFromAnswers(...)` in `CoreLinkModel.kt`
- Persisted local watch state across restart: `CoreLinkPrefs` in `CoreLinkStorage.kt`
- Single visual scene, compact HUD, repair/roam/scan/charge loop, watch status,
  and reset access: `GameSceneScreen()`, `WatchStatusScreen()`,
  `SettingsScreen()`, and `PixelScene()` in `MainActivity.kt`

## Notes

- On the 480x480 Wear emulator, the recovery diagnostics fill the first fold, so
  revealing `Recover` and later `Begin Calibration` requires the expected
  vertical scroll on the watch-sized surface.
- No code changes were required for `WRK-199`; the issue closed as native
  runtime proof for the existing implementation.
