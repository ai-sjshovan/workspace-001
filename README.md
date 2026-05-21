# Derpy Owl Android MVP

This branch replaces the WebView prototype path with a native Android runtime foundation. The checked-in HTML, JS, and CSS files remain only as archived mechanic reference and are no longer launched by the app.

## Native scaffold surfaces

- Native Android splash and launcher activity
- Native start screen with a local dev-login fallback
- Native `View`-driven flap loop with Canvas rendering
- Native score HUD, milestone tracking, and death/restart overlay

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

Android Studio path:

1. Open this repo as a Gradle project in Android Studio.
2. Let the IDE sync the `app` module.
3. Run the `app` configuration on an AVD or a connected device.

## Validation blocker path

If the shell environment cannot build, check these prerequisites first:

```bash
java -version
echo "$ANDROID_HOME"
echo "$ANDROID_SDK_ROOT"
adb devices
```

Missing Java, missing Android SDK environment variables, or no attached/emulated device are the expected blockers for CLI validation outside Android Studio.
