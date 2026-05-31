# WRK-198 Low-Power Warning And Scene Reset Controls

Date: June 1, 2026

## Scope

- Keep the single watch-sized Core Link scene intact while adding a clearer in-scene low-power warning
- Expose settings/reset access from the main scene instead of only through the status flow
- Preserve existing local-first persistence, reset semantics, and native Wear OS command loop

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

## Acceptance Coverage

- Main watch scene still keeps compact `Charge`, `Scrap`, and `Cond` HUD chips visible above the pixel bot scene.
- When Charge drops below the low-power threshold, the scene now shows an explicit warning strip with the remaining Charge needed to clear the condition and the roam lockout.
- The main scene now exposes `Scene Settings / Reset`, so local wipe controls are reachable without first leaving to the status surface.
- Reset behavior still uses the existing persisted local-state wipe path and returns the app to the Core Link recovery boot flow.
- Existing deterministic low-power and persistence helpers remain covered by unit tests, including the new low-power recovery-gap helper.

## Notes

- This validation pass did not rerun emulator launch or tap-through proof because the change was limited to Compose scene/UI wiring and unit-tested local state helpers.
- Prior Wear OS launch evidence remains in `docs/validation/WRK-193-wear-build-evidence.md` and `docs/validation/WRK-196-native-wear-mvp-delivery.md`.
