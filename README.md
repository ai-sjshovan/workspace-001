# Derpy Owl Android MVP

This branch replaces the WebView prototype path with a native Android runtime foundation. The checked-in HTML, JS, and CSS files remain only as archived mechanic reference and are no longer launched by the app.

## Native scaffold surfaces

- Native Android splash and launcher activity
- Native start screen with Google login plus a native dev-login fallback
- Native `View`-driven flap loop with Canvas rendering
- Native score HUD, milestone tracking, player-aware score persistence, and death/restart overlay

## Native visual surfaces

- Flying owl canvas art: `app/src/main/java/com/codexfoundry/derpyowl/DerpyOwlGameView.kt`
- Native palette resources: `app/src/main/res/values/colors.xml`
- The owl remains collision-fair by keeping collision checks on a smaller body radius while the animated wings render outside that hitbox.
- Obstacles stay native-rendered:
  - Top obstacles are storm-cloud canopy shapes drawn on `Canvas`
  - Bottom obstacles are layered pine silhouettes and trunks drawn on `Canvas`
- Background stays native-rendered with a shader sky, mountain ridge, rolling hills, and parallax clouds.

## Gameplay tuning evidence

- Score advances in `DerpyOwlGameView.updateWorld()` by accumulating frame delta and adding exactly `1` point whenever another full second is survived.
- Difficulty ramps from the opening values toward a hard cap over `40` score seconds, then stops increasing.
- Opening loop constants are tuned for an MVP-friendly start:
  - `FLAP_IMPULSE = -460f`
  - `STARTING_GRAVITY = 780f`
  - `STARTING_OBSTACLE_SPEED = 235f`
  - `STARTING_SPAWN_INTERVAL = 2.05f`
  - `BASE_GAP_HEIGHT_RATIO = 0.35f`
- Difficulty cap values prevent unfair late spikes:
  - `MAX_GRAVITY = 920f`
  - `MAX_OBSTACLE_SPEED = 355f`
  - `MIN_SPAWN_INTERVAL = 1.5f`
  - `MIN_GAP_HEIGHT_RATIO = 0.28f`

## Build and run

From the repo root:

```bash
./gradlew assembleDebug
./gradlew installDebug
adb shell am start -n com.codexfoundry.derpyowl/.MainActivity
```

Windows/WSL fallback used in this workspace:

```bash
cmd.exe /c "set JAVA_HOME=C:\Program Files\Android\Android Studio\jbr&& set ANDROID_HOME=C:\Users\Sjsho\AppData\Local\Android\Sdk&& set ANDROID_SDK_ROOT=C:\Users\Sjsho\AppData\Local\Android\Sdk&& gradlew.bat assembleDebug"
"/mnt/c/Users/Sjsho/AppData/Local/Android/Sdk/platform-tools/adb.exe" install -r app/build/outputs/apk/debug/app-debug.apk
"/mnt/c/Users/Sjsho/AppData/Local/Android/Sdk/platform-tools/adb.exe" shell am start -n com.codexfoundry.derpyowl/.MainActivity
```

Android Studio path:

1. Open this repo as a Gradle project in Android Studio.
2. Let the IDE sync the `app` module.
3. Run the `app` configuration on an AVD or a connected device.

## Login and score persistence

- Player identity is stored natively in `SharedPreferences` through `PlayerSessionStore`.
- Completed runs are saved per player with `bestScore`, `lastScore`, and `runCount`.
- The active player's saved score summary is shown on the start overlay and refreshed after each completed run.

## Google login setup

This build uses Android Credential Manager plus Sign in with Google. Google login only succeeds after the Android OAuth credentials are configured for this app.

1. In Google Auth Platform or Google Cloud Console, create credentials for package `com.codexfoundry.derpyowl`.
2. Register the SHA-1 and SHA-256 for the signing key you will use from Android Studio or Gradle.
3. Create or confirm the OAuth web client ID used for Credential Manager Sign in with Google.
4. Set that client ID in `app/src/main/res/values/strings.xml` as `google_web_client_id`, or place the override in a local untracked Android resource file.
5. Run on hardware with Google Play services, or on an emulator image that includes Google APIs / Play Store support.

If those credentials are not available, the start screen still provides the native dev fallback path. That fallback is intentionally local-only and does not pretend to be production Google auth.

## Validation blocker path

If the shell environment cannot build, check these prerequisites first:

```bash
java -version
echo "$ANDROID_HOME"
echo "$ANDROID_SDK_ROOT"
adb devices
```

Missing Java, missing Android SDK environment variables, or no attached/emulated device are the expected blockers for CLI validation outside Android Studio.
