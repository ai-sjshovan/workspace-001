# WRK-181 Native Android Validation Evidence

Date: 2026-05-21

## Outcome

The repo contains a native Android Derpy Owl scaffold, but this shell could not complete a build or play-test launch because the Windows Gradle client could not reconnect to its local single-use daemon and `adb` never reached a usable device list from the same shell path. This task is therefore blocked on Android tooling execution, not on a missing native scaffold.

## Native runtime proof in the current checkout

- Android entry point exists at `app/src/main/AndroidManifest.xml` and launches `com.codexfoundry.derpyowl.MainActivity`.
- The start/login screen and gameplay host are native Android UI in `app/src/main/res/layout/activity_main.xml`, including the custom `com.codexfoundry.derpyowl.DerpyOwlGameView`.
- The gameplay loop is native `Canvas` rendering in `app/src/main/java/com/codexfoundry/derpyowl/DerpyOwlGameView.kt`.
- The native game loop increments score by exactly `1` for each survived second in `DerpyOwlGameView.updateWorld()`.
- Death flow saves score state through `PlayerSessionStore.saveCompletedRun(...)` in `app/src/main/java/com/codexfoundry/derpyowl/MainActivity.kt`.
- Saved score and achievement state is persisted in `SharedPreferences` by `app/src/main/java/com/codexfoundry/derpyowl/PlayerSessionStore.kt`.
- Milestone achievements are defined at `10`, `25`, `50`, and `100` in `app/src/main/java/com/codexfoundry/derpyowl/ScoreAchievements.kt`.
- The checked-in web files under `app/src/main/assets/` remain archived reference material. Android source inspection found no `WebView` usage in the native app code.

## Commands run

WSL shell baseline:

```bash
java -version
printf 'ANDROID_HOME=%s\nANDROID_SDK_ROOT=%s\nJAVA_HOME=%s\n' "$ANDROID_HOME" "$ANDROID_SDK_ROOT" "$JAVA_HOME"
```

Observed result:

```text
/bin/bash: line 1: java: command not found
ANDROID_HOME=
ANDROID_SDK_ROOT=
JAVA_HOME=
```

Windows Android tooling probes from the same workspace:

```bash
powershell.exe -NoProfile -Command 'Set-Location "D:\AI\codex-foundry\workspace\tasks\WRK-181"; & "C:\Users\Sjsho\AppData\Local\Android\Sdk\emulator\emulator.exe" -list-avds'
powershell.exe -NoProfile -Command 'Set-Location "D:\AI\codex-foundry\workspace\tasks\WRK-181"; $env:JAVA_HOME="C:\Program Files\Android\Android Studio\jbr"; $env:ANDROID_HOME="C:\Users\Sjsho\AppData\Local\Android\Sdk"; $env:ANDROID_SDK_ROOT="C:\Users\Sjsho\AppData\Local\Android\Sdk"; $env:Path="$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:Path"; java -version; .\gradlew.bat --no-daemon help'
powershell.exe -NoProfile -Command 'Set-Location "D:\AI\codex-foundry\workspace\tasks\WRK-181"; & "C:\Users\Sjsho\AppData\Local\Android\Sdk\platform-tools\adb.exe" devices'
```

Observed result:

```text
Medium_Phone

openjdk version "21.0.10" 2026-01-20
OpenJDK Runtime Environment (build 21.0.10+-14961533-b1163.108)
OpenJDK 64-Bit Server VM (build 21.0.10+-14961533-b1163.108, mixed mode)
To honour the JVM settings for this build a single-use Daemon process will be forked.

FAILURE: Build failed with an exception.
* What went wrong:
Could not connect to the Gradle daemon.
Caused by: java.net.ConnectException: Connection timed out: getsockopt
```

`adb.exe devices` did not return a usable device list before the command timed out from this shell path, so there is no trustworthy emulator/device launch evidence to attach from the current environment.

## Acceptance status from this run

- Native Android project present: yes
- Native launcher/start surface present in source: yes
- Native gameplay surface present without `WebView`: yes
- Score increments `1` per survived second in source: yes
- Death flow plus saved score/achievement persistence present in source: yes
- Milestones `10`, `25`, `50`, `100` represented in source: yes
- Build/run evidence from this shell: blocked by Gradle daemon connection timeout and unusable `adb` response path

## Next step to unblock

Run the project directly from Android Studio on Windows, or fix the Windows-side Gradle/ADB accessibility so `gradlew.bat assembleDebug` and `adb devices` can complete from the task shell. Once that is repaired, repeat the same validation path on the available `Medium_Phone` AVD or a connected device and capture the launch/play evidence there.
