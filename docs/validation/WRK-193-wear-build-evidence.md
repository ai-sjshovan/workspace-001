# WRK-193 CoreLink Wear OS Build And Launch Evidence

Date: 2026-05-29
Repo: `project/corelink`

## Result

CoreLink's native Wear OS project built successfully, installed to a connected
Wear OS device, and launched `MainActivity` through the native Android app path.
There is no remaining tooling blocker for the build-and-launch evidence required
by this issue.

## Build Evidence

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
- `adb devices` showed the connected target `adb-RFAX82BTZ9A-F20k5e._adb-tls-connect._tcp`.
- `emulator -list-avds` reported both `Medium_Phone` and `Wear_OS_XL_Round`.
- Debug APK produced at `app/build/outputs/apk/debug/app-debug.apk`.

Connected target proof:

- `adb shell getprop ro.build.characteristics` returned `nosdcard,watch`.
- `adb shell getprop ro.product.model` returned `SM-L705U`.

## Install And Launch Evidence

Command run from this workspace:

```powershell
powershell.exe -NoProfile -Command '& {
  $ErrorActionPreference = "Stop"
  $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  $env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
  $device = "adb-RFAX82BTZ9A-F20k5e._adb-tls-connect._tcp"
  .\gradlew.bat :app:installDebug
  & "$env:ANDROID_HOME\platform-tools\adb.exe" -s $device shell am start -W -n com.corelink.wear/.MainActivity
  & "$env:ANDROID_HOME\platform-tools\adb.exe" -s $device shell pidof com.corelink.wear
}'
```

Observed result:

- `:app:installDebug` succeeded with `Installed on 1 device.`
- `am start -W` returned `Status: ok`.
- Started activity: `com.corelink.wear/.MainActivity`
- `pidof com.corelink.wear` returned process id `18357`, confirming the app was running on the connected watch after launch.

## Acceptance Surface Coverage

- Native Wear OS app module: `app/`
- Recovery opening and onboarding: `Begin Recovery`
- Core Matrix calibration flow: `Calibration` and `Calibrate Starter Bot`
- Active bot dashboard: `Dashboard`
- Charge, Scrap, condition, and mood panels: dashboard telemetry plus `Watch Status Surface`
- Repair flow: `Repair -5 Charge / -3 Scrap`
- Roam flow: `Dispatch Roam -12 Charge` and `Recover Roam Haul`
- Settings/reset demo state: `Settings / Reset`

## Remaining Manual Smoke

The issue's required native build and launch path is now proven. The remaining
interactive product smoke still belongs on the Wear target itself:

- walk through recovery and calibration
- generate Charge through live activity or `Simulate Activity Burst`
- dispatch and recover a roam
- spend Charge and Scrap on repair
- relaunch once to confirm persisted state on-device
