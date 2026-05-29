package com.corelink.wear

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.media.AudioManager
import android.media.ToneGenerator
import android.os.Bundle
import android.view.View
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.core.view.HapticFeedbackConstantsCompat
import androidx.core.view.ViewCompat
import androidx.wear.compose.material3.Button
import androidx.wear.compose.material3.MaterialTheme
import androidx.wear.compose.material3.Text
import kotlinx.coroutines.delay
import kotlin.math.PI
import kotlin.math.sin

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            CoreLinkTheme {
                CoreLinkApp(applicationContext)
            }
        }
    }
}

private enum class Screen {
    Recovery,
    Calibration,
    Scene,
    WatchStatus,
    RoamReport,
}

private enum class BotVisualState {
    Idle,
    Scan,
    LowPower,
    Repair,
    Roam,
    Recovered,
}

private enum class CommandTone {
    Tap,
    Warning,
    Success,
}

private enum class PixelIconKind {
    Charge,
    Repair,
    Roam,
    Scan,
    Status,
    Continue,
    Recover,
    Back,
}

private data class CalibrationPrompt(
    val title: String,
    val prompt: String,
    val options: List<String>,
)

private data class CommandSpec(
    val icon: PixelIconKind,
    val label: String,
    val sublabel: String,
    val onPress: () -> Unit,
)

private data class DiagnosticLine(
    val text: String,
    val accent: Color = Color(0xFF89D6FF),
)

private object CoreLinkPrefs {
    private const val Name = "corelink_state"

    fun load(context: Context): CoreLinkState {
        val prefs = context.getSharedPreferences(Name, Context.MODE_PRIVATE)
        val values = prefs.all.mapValues { (_, value) -> value?.toString().orEmpty() }
        return CoreLinkStateCodec.decode(values)
    }

    fun save(context: Context, state: CoreLinkState) {
        val values = CoreLinkStateCodec.encode(state)
        context.getSharedPreferences(Name, Context.MODE_PRIVATE).edit().clear().apply {
            values.forEach { (key, value) -> putString(key, value) }
        }.apply()
    }
}

@Composable
private fun CoreLinkApp(context: Context) {
    val initialState = remember(context) { CoreLinkPrefs.load(context) }
    var state by remember { mutableStateOf(initialState) }
    var screen by remember { mutableStateOf(if (initialState.calibrated) Screen.Scene else Screen.Recovery) }
    var answers by remember { mutableStateOf(initialState.activeCore?.answers ?: CalibrationAnswers()) }
    var roamClockMillis by remember { mutableStateOf(System.currentTimeMillis()) }
    var sceneVisualState by remember { mutableStateOf(if (initialState.calibrated) BotVisualState.Recovered else BotVisualState.Idle) }
    val sensorManager = remember(context) { context.getSystemService(Context.SENSOR_SERVICE) as SensorManager }
    val stepCounterSensor = remember(sensorManager) { sensorManager.getDefaultSensor(Sensor.TYPE_STEP_COUNTER) }
    var hasActivityPermission by remember(context) { mutableStateOf(hasActivityRecognitionPermission(context)) }
    val latestState by rememberUpdatedState(state)
    val feedback = rememberCommandFeedback()
    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        hasActivityPermission = granted
        if (granted) {
            feedback.play(CommandTone.Success)
        } else {
            feedback.play(CommandTone.Warning)
        }
    }

    fun commit(nextState: CoreLinkState) {
        val syncedState = synchronizeDerivedState(nextState, nowEpochMillis = System.currentTimeMillis())
        state = syncedState
        CoreLinkPrefs.save(context, syncedState)
    }

    fun pulseVisual(stateName: BotVisualState) {
        sceneVisualState = stateName
    }

    LaunchedEffect(sceneVisualState) {
        if (sceneVisualState != BotVisualState.Idle && sceneVisualState != BotVisualState.LowPower && sceneVisualState != BotVisualState.Roam) {
            delay(1_400)
            sceneVisualState = if (state.lowPowerWarningActive) {
                BotVisualState.LowPower
            } else if (roamStatus(state, System.currentTimeMillis()) == RoamStatus.Roaming) {
                BotVisualState.Roam
            } else {
                BotVisualState.Idle
            }
        }
    }

    LaunchedEffect(state.lowPowerWarningActive, state.roamEndsAtEpochMillis, state.condition) {
        sceneVisualState = when {
            roamStatus(state, System.currentTimeMillis()) == RoamStatus.Roaming -> BotVisualState.Roam
            state.lowPowerWarningActive || state.condition < 45 -> BotVisualState.LowPower
            else -> sceneVisualState
        }
    }

    LaunchedEffect(state.roamEndsAtEpochMillis) {
        roamClockMillis = System.currentTimeMillis()
        while (state.roamEndsAtEpochMillis != null && roamStatus(state, roamClockMillis) == RoamStatus.Roaming) {
            delay(1_000)
            roamClockMillis = System.currentTimeMillis()
        }
        roamClockMillis = System.currentTimeMillis()
    }

    DisposableEffect(screen, sensorManager, stepCounterSensor, hasActivityPermission) {
        if (screen != Screen.Scene || stepCounterSensor == null || !hasActivityPermission) {
            onDispose { }
        } else {
            val listener = object : SensorEventListener {
                override fun onSensorChanged(event: SensorEvent) {
                    val totalSteps = event.values.firstOrNull()?.toInt() ?: return
                    val nextState = applyWearStepSample(latestState, totalSteps)
                    if (nextState != latestState) {
                        commit(nextState)
                    }
                }

                override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit
            }

            sensorManager.registerListener(listener, stepCounterSensor, SensorManager.SENSOR_DELAY_NORMAL)
            onDispose {
                sensorManager.unregisterListener(listener)
            }
        }
    }

    when (screen) {
        Screen.Recovery -> RecoveryScreen(
            onRecover = {
                feedback.play(CommandTone.Success)
                screen = Screen.Calibration
            },
            onSkipToScene = if (state.calibrated) ({ screen = Screen.Scene }) else null,
            onBlocked = { feedback.play(CommandTone.Warning) },
        )

        Screen.Calibration -> CalibrationScreen(
            answers = answers,
            onAnswersChange = { answers = it },
            onRecovered = {
                val calibratedState = starterStateFromAnswers(answers).copy(
                    recoveryNotes = "Core Link OS recovered the AI core and mapped the starter lattice.",
                )
                commit(calibratedState)
                pulseVisual(BotVisualState.Recovered)
                feedback.play(CommandTone.Success)
                screen = Screen.Scene
            },
        )

        Screen.Scene -> GameSceneScreen(
            state = state,
            nowEpochMillis = roamClockMillis,
            visualState = sceneVisualState,
            stepSensorAvailable = stepCounterSensor != null,
            activityPermissionGranted = hasActivityPermission,
            onOpenWatchStatus = { screen = Screen.WatchStatus },
            onRequestActivityPermission = {
                permissionLauncher.launch(Manifest.permission.ACTIVITY_RECOGNITION)
            },
            onCharge = {
                commit(applySimulatedActivityBurst(state))
                pulseVisual(BotVisualState.Recovered)
                feedback.play(CommandTone.Tap)
            },
            onRepair = {
                val gate = repairGate(state, System.currentTimeMillis())
                if (gate.allowed) {
                    commit(repairBot(state, System.currentTimeMillis()))
                    pulseVisual(BotVisualState.Repair)
                    feedback.play(CommandTone.Success)
                } else {
                    commit(state.copy(recoveryNotes = gate.message))
                    feedback.play(CommandTone.Warning)
                }
            },
            onRoam = {
                val now = System.currentTimeMillis()
                when (roamStatus(state, now)) {
                    RoamStatus.ReadyToReturn -> {
                        val updated = resolveRoamReturn(state, now)
                        commit(updated)
                        pulseVisual(BotVisualState.Recovered)
                        feedback.play(CommandTone.Success)
                        if (updated != state) {
                            screen = Screen.RoamReport
                        }
                    }

                    RoamStatus.Roaming -> {
                        commit(state.copy(recoveryNotes = "Roam route still active. Wait for return window before recovery."))
                        feedback.play(CommandTone.Warning)
                    }

                    RoamStatus.Idle -> {
                        val gate = roamDispatchGate(state, now)
                        if (gate.allowed) {
                            commit(dispatchRoam(state, now))
                            pulseVisual(BotVisualState.Roam)
                            feedback.play(CommandTone.Tap)
                        } else {
                            commit(state.copy(recoveryNotes = gate.message))
                            feedback.play(CommandTone.Warning)
                        }
                    }
                }
            },
            onScan = {
                commit(scanCore(state, System.currentTimeMillis()))
                pulseVisual(BotVisualState.Scan)
                feedback.play(CommandTone.Tap)
            },
        )

        Screen.WatchStatus -> WatchStatusScreen(
            state = state,
            nowEpochMillis = roamClockMillis,
            onBack = { screen = Screen.Scene },
            onReset = {
                val resetState = CoreLinkState()
                commit(resetState)
                answers = CalibrationAnswers()
                feedback.play(CommandTone.Warning)
                screen = Screen.Recovery
            },
        )

        Screen.RoamReport -> RoamReportScreen(
            report = state.lastRoamReport,
            onReturn = { screen = Screen.Scene },
        )
    }
}

@Composable
private fun RecoveryScreen(
    onRecover: () -> Unit,
    onSkipToScene: (() -> Unit)?,
    onBlocked: () -> Unit,
) {
    val bootLines = remember {
        listOf(
            DiagnosticLine("Initializing Core Link...", Color(0xFFB7F6FF)),
            DiagnosticLine("[0001] OWNER PROFILE ........ UNKNOWN", Color(0xFFFFB36A)),
            DiagnosticLine("[0002] MEMORY LATTICE ...... TAMPERED", Color(0xFFFF7A7A)),
            DiagnosticLine("[0003] AI CORE STATE ...... UNSTABLE", Color(0xFFFF7A7A)),
            DiagnosticLine("[0004] NANOBOT CONTAINER ... FULL", Color(0xFF85FFB2)),
            DiagnosticLine("[0005] CONNECTED RESOURCE .. 1x AI Core", Color(0xFF85FFB2)),
            DiagnosticLine("[0006] CONNECTED RESOURCE .. 1x Nanobot Container (Full)", Color(0xFF85FFB2)),
            DiagnosticLine("[0007] RECOVERY CHANNEL .... READY", Color(0xFF89D6FF)),
        )
    }
    val analysisLines = remember {
        listOf(
            DiagnosticLine("[A-11] Recovering cached items into quarantine buffer...", Color(0xFF89D6FF)),
            DiagnosticLine("[A-12] AI core shell responding to low-band handshake...", Color(0xFF89D6FF)),
            DiagnosticLine("[A-13] Core Matrix calibration required before deployment.", Color(0xFFB7F6FF)),
        )
    }
    var visibleBootLines by remember { mutableIntStateOf(1) }
    var recoveryAccepted by remember { mutableStateOf(false) }
    var visibleAnalysisLines by remember { mutableIntStateOf(0) }

    LaunchedEffect(Unit) {
        while (visibleBootLines < bootLines.size) {
            delay(260)
            visibleBootLines += 1
        }
    }

    LaunchedEffect(recoveryAccepted) {
        if (recoveryAccepted) {
            visibleAnalysisLines = 0
            while (visibleAnalysisLines < analysisLines.size) {
                delay(280)
                visibleAnalysisLines += 1
            }
        }
    }

    ScrollScreenFrame {
        SceneHeader(
            title = "CORE LINK OS",
            badge = "BOOT",
            caption = "Recovered watch node entering recovery mode.",
        )
        ConsolePanel {
            bootLines.take(visibleBootLines).forEach { line ->
                ConsoleLine(line.text, line.accent)
            }
            if (recoveryAccepted) {
                analysisLines.take(visibleAnalysisLines).forEach { line ->
                    ConsoleLine(line.text, line.accent)
                }
            }
        }
        if (visibleBootLines == bootLines.size && !recoveryAccepted) {
            PromptPanel(
                title = "Recover available items?",
                body = "Core Link OS detected one unstable AI core and one full nanobot container.",
            )
            CommandRow(
                commands = listOf(
                    CommandSpec(PixelIconKind.Recover, "Recover", "ITEMS") { recoveryAccepted = true },
                    CommandSpec(PixelIconKind.Back, "Defer", "LOCK") { onBlocked() },
                ),
            )
        }
        if (recoveryAccepted && visibleAnalysisLines == analysisLines.size) {
            PromptPanel(
                title = "AI core ready for calibration.",
                body = "Proceed one question at a time to reconstruct the starter lattice.",
            )
            Button(modifier = Modifier.fillMaxWidth(), onClick = onRecover) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    PixelIcon(PixelIconKind.Continue, Color(0xFFB7F6FF))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Begin Calibration", fontFamily = FontFamily.Monospace)
                }
            }
        }
        if (onSkipToScene != null) {
            Spacer(modifier = Modifier.height(8.dp))
            SmallUtilityButton(
                modifier = Modifier.fillMaxWidth(),
                label = "Resume Active Core",
                icon = PixelIconKind.Status,
                onClick = onSkipToScene,
            )
        }
    }
}

@Composable
private fun CalibrationScreen(
    answers: CalibrationAnswers,
    onAnswersChange: (CalibrationAnswers) -> Unit,
    onRecovered: () -> Unit,
) {
    val prompts = remember {
        listOf(
            CalibrationPrompt(
                title = "Failsafe Priority",
                prompt = "A lattice spike trips in the deadband. Which routine does Core Link pin first?",
                options = listOf("Aegis shield mesh", "Pulse probe burst", "Relay signal reroute"),
            ),
            CalibrationPrompt(
                title = "Frame Bias",
                prompt = "Which chassis profile survives the recovery chamber best?",
                options = listOf("Scout micro-frame", "Forge reinforced frame", "Bloom adaptive shell"),
            ),
            CalibrationPrompt(
                title = "Command Doctrine",
                prompt = "When the recovered core meets resistance, which doctrine remains active?",
                options = listOf("Ward perimeter hold", "Drive pressure advance", "Weave route adaptation"),
            ),
            CalibrationPrompt(
                title = "Adaptive Mode",
                prompt = "Pick the stabilization mode for post-recovery drift correction.",
                options = listOf("Anchor hard-lock", "Surge overclock", "Drift elastic tuning"),
            ),
        )
    }
    var questionIndex by remember { mutableIntStateOf(0) }
    val previewCore = remember(answers) { calibrateStarterCore(answers) }
    val currentPrompt = prompts[questionIndex]

    fun selectedIndex(question: Int): Int =
        when (question) {
            0 -> answers.instinctIndex
            1 -> answers.frameIndex
            2 -> answers.doctrineIndex
            else -> answers.adaptationIndex
        }

    fun updateAnswer(question: Int, option: Int) {
        val nextAnswers = when (question) {
            0 -> answers.copy(instinctIndex = option)
            1 -> answers.copy(frameIndex = option)
            2 -> answers.copy(doctrineIndex = option)
            else -> answers.copy(adaptationIndex = option)
        }
        onAnswersChange(nextAnswers)
    }

    ScrollScreenFrame {
        SceneHeader(
            title = "CORE MATRIX",
            badge = "${questionIndex + 1}/${prompts.size}",
            caption = "Technical recovery prompts are shaping the restored starter AI core.",
        )
        PromptPanel(
            title = currentPrompt.title,
            body = currentPrompt.prompt,
        )
        currentPrompt.options.forEachIndexed { index, option ->
            val selected = selectedIndex(questionIndex) == index
            SelectionButton(
                label = option,
                selected = selected,
                onClick = { updateAnswer(questionIndex, index) },
            )
            Spacer(modifier = Modifier.height(8.dp))
        }
        PromptPanel(
            title = "Recovered profile",
            body = buildString {
                append("${previewCore.designation}  ${previewCore.frame}\n")
                append("Mood ${previewCore.mood}  Temperament ${previewCore.stats.temperament}\n")
                append("Control ${previewCore.stats.control}  Stability ${previewCore.stats.stability}  Curiosity ${previewCore.matrix.curiosity}")
            },
        )
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            if (questionIndex > 0) {
                Box(modifier = Modifier.weight(1f)) {
                    SmallUtilityButton(
                        modifier = Modifier.fillMaxWidth(),
                        label = "Previous",
                        icon = PixelIconKind.Back,
                        onClick = { questionIndex -= 1 },
                    )
                }
            }
            Box(modifier = Modifier.weight(1f)) {
                if (questionIndex < prompts.lastIndex) {
                    SmallUtilityButton(
                        modifier = Modifier.fillMaxWidth(),
                        label = "Next",
                        icon = PixelIconKind.Continue,
                        onClick = { questionIndex += 1 },
                    )
                } else {
                    SmallUtilityButton(
                        modifier = Modifier.fillMaxWidth(),
                        label = "Recover AI Core",
                        icon = PixelIconKind.Recover,
                        onClick = onRecovered,
                    )
                }
            }
        }
    }
}

@Composable
private fun GameSceneScreen(
    state: CoreLinkState,
    nowEpochMillis: Long,
    visualState: BotVisualState,
    stepSensorAvailable: Boolean,
    activityPermissionGranted: Boolean,
    onOpenWatchStatus: () -> Unit,
    onRequestActivityPermission: () -> Unit,
    onCharge: () -> Unit,
    onRepair: () -> Unit,
    onRoam: () -> Unit,
    onScan: () -> Unit,
) {
    val core = state.activeCore
    val currentRoamStatus = roamStatus(state, nowEpochMillis)
    val sceneState = when {
        visualState == BotVisualState.Scan -> BotVisualState.Scan
        visualState == BotVisualState.Repair -> BotVisualState.Repair
        visualState == BotVisualState.Recovered -> BotVisualState.Recovered
        currentRoamStatus == RoamStatus.Roaming -> BotVisualState.Roam
        state.lowPowerWarningActive || state.condition < 45 -> BotVisualState.LowPower
        else -> BotVisualState.Idle
    }
    val statusText = when {
        currentRoamStatus == RoamStatus.ReadyToReturn -> "ROAM HAUL READY"
        currentRoamStatus == RoamStatus.Roaming -> "ROAM ${formatCountdown(remainingRoamMillis(state, nowEpochMillis))}"
        state.lowPowerWarningActive -> "LOW POWER"
        else -> "CORE STABLE"
    }
    val statusAccent = when {
        currentRoamStatus == RoamStatus.ReadyToReturn -> Color(0xFF9AE7FF)
        currentRoamStatus == RoamStatus.Roaming -> Color(0xFF89AFFF)
        state.lowPowerWarningActive -> Color(0xFFFFB36A)
        else -> Color(0xFF85FFB2)
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF030811))
            .padding(horizontal = 12.dp, vertical = 10.dp),
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column {
                    Text(
                        text = "CORE LINK OS",
                        color = Color(0xFFB7F6FF),
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                    )
                    Text(
                        text = core?.designation ?: "UNLINKED",
                        color = Color.White,
                        fontFamily = FontFamily.Monospace,
                        fontSize = 12.sp,
                    )
                }
                SmallUtilityButton(
                    modifier = Modifier.width(88.dp),
                    label = "Status",
                    icon = PixelIconKind.Status,
                    onClick = onOpenWatchStatus,
                )
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                HudChip("Charge", "${state.charge}", metricAccent(state.charge))
                HudChip("Scrap", "${state.scrap}", metricAccent(state.scrap * 10))
                HudChip("Cond", "${state.condition}", metricAccent(state.condition))
            }

            PromptPanel(
                title = statusText,
                body = buildString {
                    append(core?.frame ?: "Recovered shell not yet linked")
                    append("  Mood ")
                    append(core?.mood ?: "Dormant")
                    append("\n")
                    append(
                        when {
                            stepSensorAvailable && activityPermissionGranted -> "Step link live. Walk to bank real Charge."
                            stepSensorAvailable -> "Step link locked. Enable activity access for live Charge."
                            else -> "No watch step sensor detected. Use Charge simulation fallback."
                        },
                    )
                },
                accent = statusAccent,
            )

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .background(Color(0xFF060E1B), RoundedCornerShape(28.dp))
                    .border(1.dp, Color(0xFF18324A), RoundedCornerShape(28.dp))
                    .padding(10.dp),
            ) {
                PixelScene(
                    visualState = sceneState,
                    designation = core?.designation ?: "UNLINKED",
                    condition = state.condition,
                    charge = state.charge,
                )
            }

            ConsolePanel(modifier = Modifier.wrapContentHeight()) {
                ConsoleLine(state.recoveryNotes, Color.White)
                ConsoleLine(
                    when (currentRoamStatus) {
                        RoamStatus.Idle -> state.lastActivitySummary
                        RoamStatus.Roaming -> state.lastRoamReport
                        RoamStatus.ReadyToReturn -> "Deadband sweep complete. Recover the haul from the Roam command."
                    },
                    Color(0xFF89D6FF),
                )
            }

            if (stepSensorAvailable && !activityPermissionGranted) {
                SmallUtilityButton(
                    modifier = Modifier.fillMaxWidth(),
                    label = "Enable Step Link",
                    icon = PixelIconKind.Charge,
                    onClick = onRequestActivityPermission,
                )
            }

            CommandRow(
                commands = listOf(
                    CommandSpec(PixelIconKind.Charge, "Charge", if (stepSensorAvailable) "PULSE" else "SIM") { onCharge() },
                    CommandSpec(PixelIconKind.Repair, "Repair", "PATCH") { onRepair() },
                    CommandSpec(
                        PixelIconKind.Roam,
                        "Roam",
                        when (currentRoamStatus) {
                            RoamStatus.Idle -> "SEND"
                            RoamStatus.Roaming -> "LIVE"
                            RoamStatus.ReadyToReturn -> "BACK"
                        },
                    ) { onRoam() },
                    CommandSpec(PixelIconKind.Scan, "Scan", "CORE") { onScan() },
                ),
            )
        }
    }
}

@Composable
private fun WatchStatusScreen(
    state: CoreLinkState,
    nowEpochMillis: Long,
    onBack: () -> Unit,
    onReset: () -> Unit,
) {
    val currentRoamStatus = roamStatus(state, nowEpochMillis)
    ScrollScreenFrame {
        SceneHeader(
            title = "WATCH STATUS",
            badge = "GLANCE",
            caption = "Compact status surface for the active companion state.",
        )
        PromptPanel(
            title = state.activeCore?.designation ?: "NO CORE",
            body = buildString {
                append("Charge ${state.charge}  Scrap ${state.scrap}  Condition ${state.condition}\n")
                append("Mood ${state.activeCore?.mood ?: "Dormant"}  ")
                append(
                    when (currentRoamStatus) {
                        RoamStatus.Idle -> "Roam ready"
                        RoamStatus.Roaming -> "Roam active"
                        RoamStatus.ReadyToReturn -> "Roam return ready"
                    },
                )
            },
        )
        ConsolePanel {
            ConsoleLine(state.lastActivitySummary, Color(0xFF89D6FF))
            ConsoleLine(state.lastRoamReport, Color.White)
        }
        SmallUtilityButton(
            modifier = Modifier.fillMaxWidth(),
            label = "Back To Core",
            icon = PixelIconKind.Back,
            onClick = onBack,
        )
        Spacer(modifier = Modifier.height(8.dp))
        SmallUtilityButton(
            modifier = Modifier.fillMaxWidth(),
            label = "Reset Demo State",
            icon = PixelIconKind.Back,
            onClick = onReset,
        )
    }
}

@Composable
private fun RoamReportScreen(report: String, onReturn: () -> Unit) {
    ScrollScreenFrame {
        SceneHeader(
            title = "ROAM RETURN",
            badge = "REPORT",
            caption = "Deadband sweep completed. Salvage and progress synchronized.",
        )
        ConsolePanel {
            ConsoleLine(report, Color.White)
        }
        SmallUtilityButton(
            modifier = Modifier.fillMaxWidth(),
            label = "Return To Core",
            icon = PixelIconKind.Continue,
            onClick = onReturn,
        )
    }
}

@Composable
private fun PixelScene(
    visualState: BotVisualState,
    designation: String,
    condition: Int,
    charge: Int,
) {
    val transition = rememberInfiniteTransition(label = "scene")
    val pulse by transition.animateFloat(
        initialValue = 0.92f,
        targetValue = 1.08f,
        animationSpec = infiniteRepeatable(
            animation = tween(850, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "pulse",
    )
    val orbit by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(2_400, easing = LinearEasing),
            repeatMode = RepeatMode.Restart,
        ),
        label = "orbit",
    )
    val flicker by transition.animateFloat(
        initialValue = 0.35f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(220, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "flicker",
    )
    val roamShift by transition.animateFloat(
        initialValue = -12f,
        targetValue = 12f,
        animationSpec = infiniteRepeatable(
            animation = tween(900, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "roam-shift",
    )
    val happyGlow by transition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(780, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "happy-glow",
    )

    Box(modifier = Modifier.fillMaxSize()) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val gridColor = Color(0xFF0E2132)
            val starColor = Color(0xFF18324A)
            val w = size.width
            val h = size.height
            val cell = w / 16f

            for (x in 0..16) {
                drawLine(
                    color = gridColor,
                    start = Offset(x * cell, 0f),
                    end = Offset(x * cell, h),
                    strokeWidth = 1f,
                )
            }
            for (y in 0..12) {
                drawLine(
                    color = gridColor,
                    start = Offset(0f, y * cell),
                    end = Offset(w, y * cell),
                    strokeWidth = 1f,
                )
            }

            listOf(
                Offset(cell * 2f, cell * 2f),
                Offset(cell * 13f, cell * 3f),
                Offset(cell * 11f, cell * 7f),
                Offset(cell * 4f, cell * 8f),
            ).forEach {
                drawRect(color = starColor, topLeft = it, size = Size(cell * 0.35f, cell * 0.35f))
            }

            val baseCenter = Offset(w / 2f + if (visualState == BotVisualState.Roam) roamShift else 0f, h * 0.52f)
            val pixel = (w / 28f).coerceAtMost(h / 28f)
            val botColor = when (visualState) {
                BotVisualState.Idle -> Color(0xFF8BE9FD)
                BotVisualState.Scan -> Color(0xFFB6A3FF)
                BotVisualState.LowPower -> Color(0xFFFF7A7A).copy(alpha = flicker)
                BotVisualState.Repair -> Color(0xFFFFD36A)
                BotVisualState.Roam -> Color(0xFF89AFFF)
                BotVisualState.Recovered -> Color(0xFF85FFB2).copy(alpha = happyGlow)
            }
            val coreGlow = when (visualState) {
                BotVisualState.LowPower -> Color(0x44FF7A7A)
                BotVisualState.Repair -> Color(0x55FFD36A)
                BotVisualState.Scan -> Color(0x44B6A3FF)
                BotVisualState.Roam -> Color(0x4489AFFF)
                BotVisualState.Recovered -> Color(0x5585FFB2)
                BotVisualState.Idle -> Color(0x448BE9FD)
            }
            val bodyScale = when (visualState) {
                BotVisualState.Idle -> pulse
                BotVisualState.Recovered -> 1.05f + (happyGlow * 0.08f)
                else -> 1f
            }

            drawCircle(
                color = coreGlow,
                radius = pixel * 9f * bodyScale,
                center = baseCenter,
                style = Fill,
            )

            val sprite = listOf(
                "000111000",
                "001111100",
                "011212110",
                "112222211",
                "111221111",
                "001111100",
                "011010110",
                "110000011",
            )

            sprite.forEachIndexed { rowIndex, row ->
                row.forEachIndexed { colIndex, char ->
                    val color = when (char) {
                        '1' -> botColor
                        '2' -> Color(0xFF05111D)
                        else -> Color.Transparent
                    }
                    if (color != Color.Transparent) {
                        val offsetX = baseCenter.x + ((colIndex - 4) * pixel * bodyScale)
                        val offsetY = baseCenter.y + ((rowIndex - 4) * pixel * bodyScale)
                        drawRect(
                            color = color,
                            topLeft = Offset(offsetX, offsetY),
                            size = Size(pixel * bodyScale, pixel * bodyScale),
                        )
                    }
                }
            }

            val eyeY = baseCenter.y - (pixel * 1.1f)
            val leftEyeX = baseCenter.x - (pixel * 1.8f)
            val rightEyeX = baseCenter.x + (pixel * 0.8f)
            val eyeColor = when (visualState) {
                BotVisualState.LowPower -> Color(0xFFFFD36A)
                BotVisualState.Scan -> Color(0xFFE6DEFF)
                BotVisualState.Repair -> Color(0xFFFFF3C4)
                BotVisualState.Recovered -> Color(0xFF031214)
                else -> Color(0xFF031214)
            }
            drawRect(eyeColor, Offset(leftEyeX, eyeY), Size(pixel, pixel))
            drawRect(eyeColor, Offset(rightEyeX, eyeY), Size(pixel, pixel))

            val smileColor = if (visualState == BotVisualState.Recovered) Color(0xFF031214) else botColor
            drawRect(
                smileColor,
                Offset(baseCenter.x - pixel, baseCenter.y + (pixel * 1.6f)),
                Size(pixel * if (visualState == BotVisualState.Recovered) 2f else 1.5f, pixel * 0.6f),
            )

            if (visualState == BotVisualState.Scan) {
                val beamHeight = (sin(orbit * PI * 2).toFloat() + 1f) * 10f
                drawRect(
                    color = Color(0x55B6A3FF),
                    topLeft = Offset(baseCenter.x - pixel * 0.5f, baseCenter.y - pixel * 9f - beamHeight),
                    size = Size(pixel, beamHeight),
                )
            }

            if (visualState == BotVisualState.Repair) {
                repeat(5) { index ->
                    val angle = (orbit + (index * 0.2f)) * (PI * 2f)
                    val x = baseCenter.x + (sin(angle).toFloat() * pixel * 6f)
                    val y = baseCenter.y + (sin(angle + 1.7f).toFloat() * pixel * 5f)
                    drawRect(
                        color = Color(0xFFFFD36A),
                        topLeft = Offset(x, y),
                        size = Size(pixel * 0.8f, pixel * 0.8f),
                    )
                }
            }

            if (visualState == BotVisualState.Roam) {
                repeat(4) { index ->
                    drawRect(
                        color = Color(0x6689AFFF),
                        topLeft = Offset(baseCenter.x + pixel * (4f + index * 1.8f), baseCenter.y + pixel * (index - 1)),
                        size = Size(pixel * 1.1f, pixel * 0.8f),
                    )
                }
            }

            if (visualState == BotVisualState.Recovered) {
                drawRect(
                    color = Color(0x7785FFB2),
                    topLeft = Offset(baseCenter.x - pixel * 5f, baseCenter.y - pixel * 8f),
                    size = Size(pixel * 10f, pixel * 0.9f),
                )
            }
        }

        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .background(Color(0xAA02060C), RoundedCornerShape(16.dp))
                .padding(horizontal = 10.dp, vertical = 8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = designation,
                color = Color.White,
                fontSize = 12.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = "Charge $charge  Condition $condition  ${visualState.name.uppercase()}",
                color = Color(0xFFB7F6FF),
                fontSize = 10.sp,
                fontFamily = FontFamily.Monospace,
            )
        }
    }
}

@Composable
private fun CommandRow(commands: List<CommandSpec>) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        commands.chunked(2).forEach { rowCommands ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                rowCommands.forEach { command ->
                    Box(modifier = Modifier.weight(1f)) {
                        Button(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(54.dp),
                            onClick = command.onPress,
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                PixelIcon(command.icon, Color(0xFF031116))
                                Text(
                                    text = command.label,
                                    color = Color(0xFF031116),
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace,
                                    fontSize = 11.sp,
                                )
                                Text(
                                    text = command.sublabel,
                                    color = Color(0xCC031116),
                                    fontFamily = FontFamily.Monospace,
                                    fontSize = 9.sp,
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ScrollScreenFrame(content: @Composable () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF030811))
            .padding(horizontal = 12.dp, vertical = 10.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            content()
            Spacer(modifier = Modifier.height(12.dp))
        }
    }
}

@Composable
private fun SceneHeader(title: String, badge: String, caption: String) {
    Text(
        text = title,
        color = Color(0xFFB7F6FF),
        fontFamily = FontFamily.Monospace,
        fontWeight = FontWeight.Bold,
        fontSize = 15.sp,
    )
    Text(
        text = badge,
        color = Color(0xFF89AFFF),
        fontFamily = FontFamily.Monospace,
        fontSize = 10.sp,
    )
    Text(
        text = caption,
        color = Color(0xFFDDE7F5),
        fontSize = 12.sp,
    )
}

@Composable
private fun PromptPanel(title: String, body: String, accent: Color = Color(0xFF89D6FF)) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF0A1421), RoundedCornerShape(18.dp))
            .border(1.dp, accent.copy(alpha = 0.35f), RoundedCornerShape(18.dp))
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Text(
            text = title,
            color = accent,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.SemiBold,
            fontSize = 11.sp,
        )
        Text(
            text = body,
            color = Color.White,
            fontSize = 12.sp,
        )
    }
}

@Composable
private fun ConsolePanel(modifier: Modifier = Modifier, lines: @Composable ColumnScope.() -> Unit) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(Color(0xFF050C14), RoundedCornerShape(18.dp))
            .border(1.dp, Color(0xFF18324A), RoundedCornerShape(18.dp))
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
        content = lines,
    )
}

@Composable
private fun ConsoleLine(text: String, color: Color) {
    Text(
        text = text,
        color = color,
        fontFamily = FontFamily.Monospace,
        fontSize = 11.sp,
    )
}

@Composable
private fun HudChip(label: String, value: String, accent: Color) {
    Box(
        modifier = Modifier
            .background(Color(0xFF0A1421), RoundedCornerShape(16.dp))
            .border(1.dp, accent.copy(alpha = 0.35f), RoundedCornerShape(16.dp))
            .padding(horizontal = 10.dp, vertical = 7.dp),
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = label,
                color = Color(0xFF8EA6BF),
                fontFamily = FontFamily.Monospace,
                fontSize = 9.sp,
            )
            Text(
                text = value,
                color = accent,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                fontSize = 12.sp,
            )
        }
    }
}

@Composable
private fun SelectionButton(label: String, selected: Boolean, onClick: () -> Unit) {
    val accent = if (selected) Color(0xFF85FFB2) else Color(0xFF89D6FF)
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF0A1421), RoundedCornerShape(18.dp))
            .border(1.dp, accent.copy(alpha = 0.35f), RoundedCornerShape(18.dp)),
    ) {
        Button(modifier = Modifier.fillMaxWidth(), onClick = onClick) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                PixelIcon(if (selected) PixelIconKind.Recover else PixelIconKind.Scan, Color(0xFF031116))
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = label,
                    color = Color(0xFF031116),
                    fontFamily = FontFamily.Monospace,
                    textAlign = TextAlign.Center,
                )
            }
        }
    }
}

@Composable
private fun SmallUtilityButton(
    label: String,
    icon: PixelIconKind,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Button(
        modifier = modifier,
        onClick = onClick,
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            PixelIcon(icon, Color(0xFF031116))
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = label,
                color = Color(0xFF031116),
                fontFamily = FontFamily.Monospace,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@Composable
private fun PixelIcon(kind: PixelIconKind, tint: Color) {
    val pattern = when (kind) {
        PixelIconKind.Charge -> listOf("0010", "0111", "0011", "0110")
        PixelIconKind.Repair -> listOf("1001", "0110", "0110", "1001")
        PixelIconKind.Roam -> listOf("1000", "1100", "0110", "0011")
        PixelIconKind.Scan -> listOf("1110", "1001", "1011", "0110")
        PixelIconKind.Status -> listOf("1010", "1111", "1111", "1010")
        PixelIconKind.Continue -> listOf("1000", "1100", "1110", "1100")
        PixelIconKind.Recover -> listOf("0110", "1111", "1111", "0110")
        PixelIconKind.Back -> listOf("0001", "0011", "0111", "0011")
    }
    Canvas(modifier = Modifier.size(14.dp)) {
        val pixel = size.width / 4f
        pattern.forEachIndexed { y, row ->
            row.forEachIndexed { x, value ->
                if (value == '1') {
                    drawRect(
                        color = tint,
                        topLeft = Offset(x * pixel, y * pixel),
                        size = Size(pixel, pixel),
                    )
                }
            }
        }
    }
}

@Composable
private fun rememberCommandFeedback(): CommandFeedback {
    val view = LocalView.current
    val toneGenerator = remember {
        runCatching { ToneGenerator(AudioManager.STREAM_NOTIFICATION, 60) }.getOrNull()
    }

    DisposableEffect(toneGenerator) {
        onDispose {
            runCatching { toneGenerator?.release() }
        }
    }

    return remember(view, toneGenerator) {
        CommandFeedback(view, toneGenerator)
    }
}

private class CommandFeedback(
    private val view: View,
    private val toneGenerator: ToneGenerator?,
) {
    fun play(tone: CommandTone) {
        val hapticConstant = when (tone) {
            CommandTone.Tap -> HapticFeedbackConstantsCompat.CLOCK_TICK
            CommandTone.Warning -> HapticFeedbackConstantsCompat.REJECT
            CommandTone.Success -> HapticFeedbackConstantsCompat.CONFIRM
        }
        runCatching { ViewCompat.performHapticFeedback(view, hapticConstant) }
        runCatching {
            when (tone) {
                CommandTone.Tap -> toneGenerator?.startTone(ToneGenerator.TONE_PROP_BEEP, 40)
                CommandTone.Warning -> toneGenerator?.startTone(ToneGenerator.TONE_PROP_NACK, 80)
                CommandTone.Success -> toneGenerator?.startTone(ToneGenerator.TONE_PROP_ACK, 80)
            }
        }
    }
}

private fun metricAccent(value: Int): Color =
    when {
        value < 15 -> Color(0xFFFF7A7A)
        value < 40 -> Color(0xFFFFB36A)
        else -> Color(0xFF85FFB2)
    }

private fun formatCountdown(remainingMillis: Long): String {
    val totalSeconds = ((remainingMillis.coerceAtLeast(0L) + 999L) / 1000L).toInt()
    val minutes = totalSeconds / 60
    val seconds = totalSeconds % 60
    return "%02d:%02d".format(minutes, seconds)
}

@Composable
private fun CoreLinkTheme(content: @Composable () -> Unit) {
    MaterialTheme(content = content)
}

private fun hasActivityRecognitionPermission(context: Context): Boolean =
    ContextCompat.checkSelfPermission(context, Manifest.permission.ACTIVITY_RECOGNITION) == PackageManager.PERMISSION_GRANTED
