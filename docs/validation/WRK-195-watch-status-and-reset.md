# WRK-195 Watch Status Tile And Reset Flow Validation

Date: May 29, 2026

## Scope

- Native Wear OS status tile surface for Charge, Scrap, Condition, mood, and roam readiness
- In-app `WATCH STATUS` surface plus `Settings / Reset` confirmation flow
- Existing Charge, Scrap, Condition, repair, roam, and local persistence mechanics unchanged

## Build And Unit Test Proof

Validated from this workspace with the Windows Android Studio JBR and configured Windows SDK:

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
- Debug APK produced at `app/build/outputs/apk/debug/app-debug.apk`.

## Wear Target Inventory

Command:

```powershell
powershell.exe -NoProfile -Command '& {
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  & "$env:ANDROID_HOME\platform-tools\adb.exe" devices
  & "$env:ANDROID_HOME\emulator\emulator.exe" -list-avds
}'
```

Observed result:

- `adb.exe devices` printed only `List of devices attached` with no connected target.
- `emulator.exe -list-avds` reported `Medium_Phone` and `Wear_OS_XL_Round`.

## Launch Attempt And Blocker

Attempted launch path:

```powershell
powershell.exe -NoProfile -Command '& {
  $ErrorActionPreference = "Stop"
  $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
  $env:ANDROID_HOME = "C:\Users\Sjsho\AppData\Local\Android\Sdk"
  $env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
  $adb = Join-Path $env:ANDROID_HOME "platform-tools\adb.exe"
  $emulator = Join-Path $env:ANDROID_HOME "emulator\emulator.exe"
  $apk = Resolve-Path ".\app\build\outputs\apk\debug\app-debug.apk"
  Start-Process -FilePath $emulator -ArgumentList "-avd Wear_OS_XL_Round -no-snapshot-load -no-boot-anim" | Out-Null
  Start-Sleep -Seconds 30
  & $adb devices
}'
```

Observed result:

- Windows `emulator.exe` started as a process.
- After a 30-second wait, `adb.exe devices` still printed no attached device.

Blocker:

- A Wear OS AVD is installed, but it did not become an `adb`-attached watch target during this run, so on-device launch and tile interaction proof could not be completed from this workspace.

## Acceptance Coverage

- Glanceable watch-status surface: implemented as the native `Core Link Status` tile plus the mirrored in-app `WATCH STATUS` screen.
- Compact bot mood/state: exposed on the tile and the in-app status surface.
- Settings/reset demo state: implemented as `Settings / Reset` with explicit confirmation before wiping local state.
- Main scene and persistence mechanics: preserved; unit tests still pass after the new surface and reset-flow changes.
