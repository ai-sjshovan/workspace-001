# WRK-190 Wear OS Run Path Evidence

Date: 2026-05-29
Repo: `project/corelink`

## Result

CoreLink's native Wear OS project builds successfully, but the runnable launch path remains blocked by local Wear tooling inventory.

## Validated Today

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

## Smoke Check Coverage

- Calibration deterministic starter core: covered by `CoreLinkModelTest.calibrationIsDeterministicForSameAnswers`.
- Dashboard Charge/Scrap/condition state: present in the native app model and UI; unit-tested through state transitions.
- Activity-to-Charge: covered by simulated activity and step-sensor conversion tests.
- Roam consumes Charge and returns Scrap: covered by `roamDispatchConsumesChargeAndPersistsTimerState` and `roamReturnGrantsDeterministicScrapAndProgress`.
- Repair consumes Charge and Scrap: covered by `repairConsumesResourcesAndImprovesCondition`.
- Low-power behavior: covered by `lowPowerStateActivatesPersistsAndClearsAfterRecharge`.
- Local persistence: covered by state codec round-trip tests and native `SharedPreferences` persistence in `MainActivity.kt`.

## Exact Blocker

The app cannot be launched on a valid Wear OS target from this workspace today because no runnable Wear target is available:

- No connected Wear OS device is visible to `adb`.
- No Wear OS AVD is installed; the only emulator image listed is the phone AVD `Medium_Phone`.

Because the acceptance gate requires Android Studio, a Wear OS emulator, or a connected Wear OS device, the remaining blocked smoke checks are:

- native app launch on a Wear OS emulator or connected watch
- on-device walkthrough of calibration, dashboard, activity-to-Charge, roam, repair, low-power, and restart persistence

## Next Required Tooling Step

Install or attach one of the following, then rerun the native launch smoke:

- a Wear OS emulator image/AVD in the Android SDK
- a connected Wear OS device visible through `adb devices`
