# WRK-192 Native Wear OS Build And Calibration Proof

Date: 2026-05-29
Repo: `project/corelink`

## Result

CoreLink's native Wear OS app builds successfully from this workspace, and the
remaining launch gap is a tooling inventory blocker rather than a web/runtime
substitution.

## Validation Command

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
- `adb devices` returned no connected devices.
- `emulator -list-avds` returned only `Medium_Phone`.

## Wear OS Proof Surface

- Native Android/Wear OS module: `app/`
- Wear app launch entrypoint: `app/src/main/java/com/corelink/wear/MainActivity.kt`
- Recovery opening and onboarding gate: `RecoveryScreen` with `Begin Recovery`
- Core Matrix calibration flow: `CalibrationScreen` with `Calibrate Starter Bot`
- Persistent local state: `CoreLinkPrefs` + `SharedPreferences`
- Active bot dashboard and watch-status surface: `DashboardScreen` and `WatchStatusScreen`

## Core Matrix Calibration Note

The deterministic starter-core proof is covered by the native unit-test surface.
Using answers `instinct=Relay`, `frame=Forge`, `doctrine=Ward`, and
`adaptation=Drift`, calibration creates exactly one active starter AI core:

- `calibrated = true`
- starter core designation: `RE-FOWD`
- starter core frame: `Relay Forge`
- recovery note confirms deterministic Core Matrix calibration

This is asserted in `CoreLinkModelTest.starterCalibrationCreatesOneActiveCore`
and uses the same native model path as the in-app calibration flow.

## Exact Launch Blocker

The remaining acceptance blocker is the lack of a valid Wear target from this
workspace today:

- `adb devices` showed no connected Wear OS device.
- `emulator -list-avds` showed only the phone AVD `Medium_Phone`.

Because the acceptance gate requires Android Studio with a Wear OS emulator or a
connected Wear OS device, runtime launch proof is blocked by tooling inventory,
not by app code.

## Next Required Tooling Step

Install or attach one of the following, then rerun the native launch smoke:

- a Wear OS emulator image/AVD in the Android SDK
- a connected Wear OS device visible through `adb devices`
