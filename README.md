# Derpy Owl Android MVP

This branch packages the existing Derpy Owl flap loop as an Android app shell instead of a standalone web page.

## MVP surfaces

- Android splash screen via the app theme and splashscreen API
- Android start/login screen loaded from local app assets
- Android gameplay screen with the existing owl flap loop
- Android death/score overlay that returns the player to the play screen

## Emulator and build commands

From the repo root:

```bash
./gradlew assembleDebug
./gradlew installDebug
adb shell am start -n com.codexfoundry.derpyowl/.MainActivity
```

If an emulator is already running, `installDebug` pushes the APK and the `adb` command launches the app directly into the Android shell.

## Local validation note

The Android project is checked in with a Gradle wrapper, but this Codex worker environment does not currently provide `java`, `ANDROID_HOME`, or `ANDROID_SDK_ROOT`, so the build command cannot be executed here without adding those dependencies first.
