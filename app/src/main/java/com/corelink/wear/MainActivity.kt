package com.corelink.wear

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.wear.compose.material3.Button
import androidx.wear.compose.material3.MaterialTheme
import androidx.wear.compose.material3.Text
import kotlinx.coroutines.delay

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
    Dashboard,
    WatchStatus,
    RoamReport,
    Settings,
}

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
    var screen by remember { mutableStateOf(if (initialState.calibrated) Screen.Dashboard else Screen.Recovery) }
    var answers by remember { mutableStateOf(initialState.activeCore?.answers ?: CalibrationAnswers()) }
    var roamClockMillis by remember { mutableStateOf(System.currentTimeMillis()) }
    val sensorManager = remember(context) { context.getSystemService(Context.SENSOR_SERVICE) as SensorManager }
    val stepCounterSensor = remember(sensorManager) { sensorManager.getDefaultSensor(Sensor.TYPE_STEP_COUNTER) }
    var hasActivityPermission by remember(context) { mutableStateOf(hasActivityRecognitionPermission(context)) }
    val latestState by rememberUpdatedState(state)
    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        hasActivityPermission = granted
    }

    fun commit(nextState: CoreLinkState) {
        val syncedState = synchronizeDerivedState(nextState, nowEpochMillis = System.currentTimeMillis())
        state = syncedState
        CoreLinkPrefs.save(context, syncedState)
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
        if (screen != Screen.Dashboard || stepCounterSensor == null || !hasActivityPermission) {
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
            onBegin = { screen = Screen.Calibration },
            onSkipToDashboard = if (state.calibrated) ({ screen = Screen.Dashboard }) else null,
        )

        Screen.Calibration -> CalibrationScreen(
            answers = answers,
            onAnswersChange = { answers = it },
            onCalibrate = {
                val calibratedState = starterStateFromAnswers(answers)
                commit(calibratedState)
                screen = Screen.Dashboard
            },
        )

        Screen.Dashboard -> DashboardScreen(
            state = state,
            nowEpochMillis = roamClockMillis,
            stepSensorAvailable = stepCounterSensor != null,
            activityPermissionGranted = hasActivityPermission,
            onRequestActivityPermission = {
                permissionLauncher.launch(Manifest.permission.ACTIVITY_RECOGNITION)
            },
            onSimulateActivity = { commit(applySimulatedActivityBurst(state)) },
            onRepair = { commit(repairBot(state, System.currentTimeMillis())) },
            onDispatchRoam = { commit(dispatchRoam(state, System.currentTimeMillis())) },
            onCollectRoam = {
                val updated = resolveRoamReturn(state, System.currentTimeMillis())
                commit(updated)
                if (updated != state) {
                    screen = Screen.RoamReport
                }
            },
            onOpenWatchStatus = { screen = Screen.WatchStatus },
            onOpenSettings = { screen = Screen.Settings },
        )

        Screen.WatchStatus -> WatchStatusScreen(
            state = state,
            nowEpochMillis = roamClockMillis,
            onBack = { screen = Screen.Dashboard },
        )

        Screen.RoamReport -> RoamReportScreen(
            report = state.lastRoamReport,
            onReturn = { screen = Screen.Dashboard },
        )

        Screen.Settings -> SettingsScreen(
            state = state,
            onReset = {
                val resetState = CoreLinkState()
                commit(resetState)
                answers = CalibrationAnswers()
                screen = Screen.Recovery
            },
            onBack = { screen = Screen.Dashboard },
        )
    }
}

@Composable
private fun RecoveryScreen(onBegin: () -> Unit, onSkipToDashboard: (() -> Unit)?) {
    ScreenContainer(title = "CoreLink") {
        HeaderCopy(
            overline = "Recovered wrist rig",
            headline = "Link one AI core and bring it back online.",
        )
        StatusPanel(
            title = "Recovery Brief",
            body = "Charge comes from activity. Scrap funds repairs. One starter bot stays active on-watch.",
        )
        Button(modifier = Modifier.fillMaxWidth(), onClick = onBegin) {
            Text("Begin Recovery")
        }
        if (onSkipToDashboard != null) {
            Spacer(modifier = Modifier.height(8.dp))
            Button(modifier = Modifier.fillMaxWidth(), onClick = onSkipToDashboard) {
                Text("Resume Bot")
            }
        }
    }
}

@Composable
private fun CalibrationScreen(
    answers: CalibrationAnswers,
    onAnswersChange: (CalibrationAnswers) -> Unit,
    onCalibrate: () -> Unit,
) {
    val instinctOptions = listOf("Aegis", "Pulse", "Relay")
    val frameOptions = listOf("Scout", "Forge", "Bloom")
    val doctrineOptions = listOf("Ward", "Drive", "Weave")
    val adaptationOptions = listOf("Anchor", "Surge", "Drift")
    val previewCore = remember(answers) { calibrateStarterCore(answers) }

    ScreenContainer(title = "Calibration") {
        HeaderCopy(
            overline = "Core Matrix",
            headline = "Answer four prompts to generate one deterministic starter AI core.",
        )
        ChoiceGroup(
            label = "Recovery instinct",
            options = instinctOptions,
            selectedIndex = answers.instinctIndex,
            onSelect = { onAnswersChange(answers.copy(instinctIndex = it)) },
        )
        ChoiceGroup(
            label = "Frame bias",
            options = frameOptions,
            selectedIndex = answers.frameIndex,
            onSelect = { onAnswersChange(answers.copy(frameIndex = it)) },
        )
        ChoiceGroup(
            label = "Command doctrine",
            options = doctrineOptions,
            selectedIndex = answers.doctrineIndex,
            onSelect = { onAnswersChange(answers.copy(doctrineIndex = it)) },
        )
        ChoiceGroup(
            label = "Adaptation mode",
            options = adaptationOptions,
            selectedIndex = answers.adaptationIndex,
            onSelect = { onAnswersChange(answers.copy(adaptationIndex = it)) },
        )
        StatusPanel(
            title = "Starter Preview",
            body = "${previewCore.designation}  ${previewCore.frame}\nMood ${previewCore.mood}  Temperament ${previewCore.stats.temperament}",
        )
        MatrixPanel(previewCore.matrix)
        StatusPanel(
            title = "Initial Stats",
            body = buildString {
                append("Speed ${previewCore.stats.speed}  Memory ${previewCore.stats.memory}\n")
                append("Power ${previewCore.stats.power}  Trust ${previewCore.stats.trust}\n")
                append("Weight ${previewCore.stats.weight}  Attack ${previewCore.stats.attack}\n")
                append("Defense ${previewCore.stats.defense}  Control ${previewCore.stats.control}\n")
                append("Stability ${previewCore.stats.stability}  Temperament ${previewCore.stats.temperament}")
            },
        )
        Button(modifier = Modifier.fillMaxWidth(), onClick = onCalibrate) {
            Text("Calibrate Starter Bot")
        }
    }
}

@Composable
private fun DashboardScreen(
    state: CoreLinkState,
    nowEpochMillis: Long,
    stepSensorAvailable: Boolean,
    activityPermissionGranted: Boolean,
    onRequestActivityPermission: () -> Unit,
    onSimulateActivity: () -> Unit,
    onRepair: () -> Unit,
    onDispatchRoam: () -> Unit,
    onCollectRoam: () -> Unit,
    onOpenWatchStatus: () -> Unit,
    onOpenSettings: () -> Unit,
) {
    val lowPower = lowPowerStatus(state)
    val core = state.activeCore
    val repairGate = repairGate(state, nowEpochMillis)
    val roamGate = roamDispatchGate(state, nowEpochMillis)
    val currentRoamStatus = roamStatus(state, nowEpochMillis)
    val roamCountdown = formatCountdown(remainingRoamMillis(state, nowEpochMillis))

    ScreenContainer(title = core?.designation ?: "CoreLink") {
        HeaderCopy(
            overline = core?.frame ?: "Dormant",
            headline = if (core != null) {
                "Active bot linked to the wrist rig."
            } else {
                "No recovered AI core is online."
            },
        )
        CommandSurfacePanel(
            designation = core?.designation ?: "UNLINKED",
            mood = core?.mood ?: "Unlinked",
            condition = state.condition,
            charge = state.charge,
            lowPower = lowPower.active,
        )
        TelemetryGrid(
            metrics = listOf(
                TelemetryMetric("Charge", "${state.charge}%", metricAccent(state.charge)),
                TelemetryMetric("Scrap", state.scrap.toString(), metricAccent(state.scrap * 10)),
                TelemetryMetric("Progress", state.progress.toString(), metricAccent(state.progress)),
                TelemetryMetric("Condition", "${state.condition}%", metricAccent(state.condition)),
                TelemetryMetric("Power State", if (lowPower.active) "LOW" else "STABLE", if (lowPower.active) Color(0xFFFFB347) else Color(0xFF7EE787)),
            ),
        )
        if (lowPower.active) {
            DashboardReadout(
                title = "Low Power",
                body = buildString {
                    append("Charge is below $LowPowerChargeThreshold. Roam dispatch is suspended until the capacitor is recharged.")
                    lowPower.enteredAtEpochMillis?.let {
                        append("\nEntered low power at epoch $it for future passive-drain tuning.")
                    }
                },
                accent = Color(0xFFFF6B6B),
            )
        }
        if (core != null) {
            DashboardReadout(
                title = "Core Matrix Summary",
                body = buildString {
                    append(matrixSummary(core))
                    append("\n")
                    append("Top traits ")
                    append(core.matrix.topTraitsSummary())
                },
                accent = Color(0xFF7AA2F7),
            )
            DashboardReadout(
                title = "Repair Queue",
                body = repairSummary(state, core),
                accent = if (state.condition < 55 || lowPower.active) Color(0xFFFFB347) else Color(0xFF7EE787),
            )
            DashboardReadout(
                title = "Roam Loop",
                body = roamSummary(state, core, currentRoamStatus, roamCountdown),
                accent = when (currentRoamStatus) {
                    RoamStatus.Idle -> if (roamGate.allowed) Color(0xFF7EE787) else Color(0xFFFFB347)
                    RoamStatus.Roaming -> Color(0xFF7AA2F7)
                    RoamStatus.ReadyToReturn -> Color(0xFF8BE9FD)
                },
            )
            DashboardReadout(
                title = "Command Warnings",
                body = buildString {
                    append("Repair: ${repairGate.message}\n")
                    append(
                        when (currentRoamStatus) {
                            RoamStatus.ReadyToReturn -> "Roam: Recover the haul to grant Scrap and progress."
                            else -> "Roam: ${roamGate.message}"
                        },
                    )
                },
                accent = if (!repairGate.allowed || !roamGate.allowed || currentRoamStatus == RoamStatus.ReadyToReturn) {
                    Color(0xFFFFB347)
                } else {
                    Color(0xFF7EE787)
                },
            )
        }
        DashboardReadout(
            title = "Ops Log",
            body = "${state.recoveryNotes}\n${state.lastRoamReport}",
        )
        DashboardReadout(
            title = "Activity Feed",
            body = buildString {
                append("Source ${state.lastActivitySource}\n")
                append(state.lastActivitySummary)
                if (!stepSensorAvailable) {
                    append("\nWear OS step sensor unavailable on this device or emulator. Use the simulation fallback for MVP validation.")
                } else if (!activityPermissionGranted) {
                    append("\nGrant activity access to convert live Wear OS steps into shared Charge.")
                }
            },
            accent = if (stepSensorAvailable && activityPermissionGranted) Color(0xFF7EE787) else Color(0xFFFFB347),
        )
        if (stepSensorAvailable && !activityPermissionGranted) {
            Button(modifier = Modifier.fillMaxWidth(), onClick = onRequestActivityPermission) {
                Text("Enable Wear Step Access")
            }
            Spacer(modifier = Modifier.height(8.dp))
        }
        Button(modifier = Modifier.fillMaxWidth(), onClick = onSimulateActivity) {
            Text("Simulate Activity Burst")
        }
        Spacer(modifier = Modifier.height(8.dp))
        Button(modifier = Modifier.fillMaxWidth(), onClick = onRepair, enabled = repairGate.allowed) {
            Text("Repair -$RepairChargeCost Charge / -$RepairScrapCost Scrap")
        }
        Spacer(modifier = Modifier.height(8.dp))
        Button(
            modifier = Modifier.fillMaxWidth(),
            onClick = if (currentRoamStatus == RoamStatus.ReadyToReturn) onCollectRoam else onDispatchRoam,
            enabled = currentRoamStatus == RoamStatus.ReadyToReturn || roamGate.allowed,
        ) {
            Text(
                when (currentRoamStatus) {
                    RoamStatus.Idle -> "Dispatch Roam -$RoamChargeCost Charge"
                    RoamStatus.Roaming -> "Roaming $roamCountdown"
                    RoamStatus.ReadyToReturn -> "Recover Roam Haul"
                },
            )
        }
        Spacer(modifier = Modifier.height(8.dp))
        Button(modifier = Modifier.fillMaxWidth(), onClick = onOpenWatchStatus) {
            Text("Watch Status Surface")
        }
        Spacer(modifier = Modifier.height(8.dp))
        Button(modifier = Modifier.fillMaxWidth(), onClick = onOpenSettings) {
            Text("Settings / Reset")
        }
    }
}

private data class TelemetryMetric(
    val label: String,
    val value: String,
    val accent: Color,
)

private fun metricAccent(value: Int): Color =
    when {
        value < 15 -> Color(0xFFFF6B6B)
        value < 40 -> Color(0xFFFFB347)
        else -> Color(0xFF7EE787)
    }

private fun matrixSummary(core: StarterCore): String =
    "${core.designation} ${core.stats.temperament} frame ${core.frame}. " +
        "Control ${core.stats.control}, Stability ${core.stats.stability}, Trust ${core.stats.trust}."

private fun repairSummary(state: CoreLinkState, core: StarterCore): String =
    buildString {
        append("${core.designation} mood ${core.mood}. ")
        if (state.lowPowerWarningActive) {
            append("Low power. Repairs still work in MVP, but roaming is paused until recharge. ")
        } else {
            append("Charge reserves ready for field work. ")
        }
        if (state.condition < 55) {
            append("Condition degraded. Repair needs 5 Charge and 3 Scrap.")
        } else {
            append("Condition holding. Repair remains optional at 5 Charge and 3 Scrap.")
        }
    }

private fun roamSummary(
    state: CoreLinkState,
    core: StarterCore,
    roamStatus: RoamStatus,
    roamCountdown: String,
): String =
    when (roamStatus) {
        RoamStatus.Idle -> buildString {
            append("${core.designation} standing by. ")
            append("Dispatch costs $RoamChargeCost Charge. ")
            append("Return rewards follow deterministic Scrap and progress rules.")
        }

        RoamStatus.Roaming -> "${core.designation} is sweeping the deadband. Return window opens in $roamCountdown."
        RoamStatus.ReadyToReturn -> "${core.designation} has completed the sweep. Recover the haul for Scrap and progress."
    }

private fun formatCountdown(remainingMillis: Long): String {
    val totalSeconds = (remainingMillis.coerceAtLeast(0L) + 999L) / 1000L
    val minutes = totalSeconds / 60
    val seconds = totalSeconds % 60
    return "%02d:%02d".format(minutes, seconds)
}

@Composable
private fun WatchStatusScreen(
    state: CoreLinkState,
    nowEpochMillis: Long,
    onBack: () -> Unit,
) {
    val core = state.activeCore
    val repairReady = repairGate(state, nowEpochMillis).allowed
    val currentRoamStatus = roamStatus(state, nowEpochMillis)
    val roamLabel = when (currentRoamStatus) {
        RoamStatus.Idle -> "Ready"
        RoamStatus.Roaming -> "Roaming ${formatCountdown(remainingRoamMillis(state, nowEpochMillis))}"
        RoamStatus.ReadyToReturn -> "Recover Haul"
    }

    ScreenContainer(title = "Watch Status") {
        HeaderCopy(
            overline = "Glance Surface",
            headline = "A watch-face-style readout for the active CoreLink bot.",
        )
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xFF050A14), RoundedCornerShape(28.dp))
                .border(1.dp, Color(0xFF214B75), RoundedCornerShape(28.dp))
                .padding(horizontal = 16.dp, vertical = 20.dp),
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    text = core?.designation ?: "NO CORE",
                    color = Color.White,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                )
                Text(
                    text = if (state.lowPowerWarningActive) "LOW POWER" else "CORELINK STABLE",
                    color = if (state.lowPowerWarningActive) Color(0xFFFFB347) else Color(0xFF7EE787),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                )
                Text(
                    text = "Mood ${core?.mood ?: "Dormant"}",
                    color = Color(0xFFB8C5D6),
                    fontSize = 13.sp,
                )
                Text(
                    text = "Charge ${state.charge}%  Scrap ${state.scrap}",
                    color = Color(0xFF8BE9FD),
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Medium,
                )
                Text(
                    text = "Condition ${state.condition}%  Roam $roamLabel",
                    color = Color(0xFFB8C5D6),
                    fontSize = 13.sp,
                    textAlign = TextAlign.Center,
                )
                Spacer(modifier = Modifier.height(4.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Box(modifier = Modifier.weight(1f)) {
                        WatchStatusChip(
                            label = "Charge",
                            value = "${state.charge}%",
                            accent = metricAccent(state.charge),
                        )
                    }
                    Box(modifier = Modifier.weight(1f)) {
                        WatchStatusChip(
                            label = "Scrap",
                            value = state.scrap.toString(),
                            accent = metricAccent(state.scrap * 10),
                        )
                    }
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Box(modifier = Modifier.weight(1f)) {
                        WatchStatusChip(
                            label = "Condition",
                            value = "${state.condition}%",
                            accent = metricAccent(state.condition),
                        )
                    }
                    Box(modifier = Modifier.weight(1f)) {
                        WatchStatusChip(
                            label = "Mood",
                            value = core?.mood ?: "Dormant",
                            accent = when {
                                state.lowPowerWarningActive -> Color(0xFFFFB347)
                                state.condition < 45 -> Color(0xFFFF6B6B)
                                else -> Color(0xFF7EE787)
                            },
                        )
                    }
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Box(modifier = Modifier.weight(1f)) {
                        WatchStatusChip(
                            label = "Repair",
                            value = if (repairReady) "Ready" else "Hold",
                            accent = if (repairReady) Color(0xFF7EE787) else Color(0xFFFFB347),
                        )
                    }
                    Box(modifier = Modifier.weight(1f)) {
                        WatchStatusChip(
                            label = "Roam",
                            value = when (currentRoamStatus) {
                                RoamStatus.Idle -> "Ready"
                                RoamStatus.Roaming -> "Live"
                                RoamStatus.ReadyToReturn -> "Return"
                            },
                            accent = when (currentRoamStatus) {
                                RoamStatus.Idle -> Color(0xFF7EE787)
                                RoamStatus.Roaming -> Color(0xFF7AA2F7)
                                RoamStatus.ReadyToReturn -> Color(0xFF8BE9FD)
                            },
                        )
                    }
                }
            }
        }
        Spacer(modifier = Modifier.height(12.dp))
        StatusPanel(
            title = "Use",
            body = "This native on-watch screen is the MVP glanceable status surface for quick Charge, Scrap, condition, mood, and repair or roam readiness checks.",
        )
        Button(modifier = Modifier.fillMaxWidth(), onClick = onBack) {
            Text("Back To Dashboard")
        }
    }
}

@Composable
private fun WatchStatusChip(label: String, value: String, accent: Color) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF0D1624), RoundedCornerShape(16.dp))
            .border(1.dp, accent.copy(alpha = 0.35f), RoundedCornerShape(16.dp))
            .padding(horizontal = 10.dp, vertical = 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(2.dp),
    ) {
        Text(
            text = label,
            color = Color(0xFF90A3B8),
            fontSize = 10.sp,
        )
        Text(
            text = value,
            color = accent,
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.Center,
        )
    }
}

private fun CoreMatrix.topTraitsSummary(): String =
    listOf(
        "Aggression" to aggression,
        "Caution" to caution,
        "Curiosity" to curiosity,
        "Discipline" to discipline,
        "Loyalty" to loyalty,
        "Independence" to independence,
        "Imagination" to imagination,
        "Efficiency" to efficiency,
    ).sortedByDescending { it.second }
        .take(3)
        .joinToString("  ") { (label, value) -> "$label $value" }

@Composable
private fun RoamReportScreen(report: String, onReturn: () -> Unit) {
    ScreenContainer(title = "Roam Result") {
        HeaderCopy(
            overline = "Deadband sweep",
            headline = "The starter bot has returned.",
        )
        StatusPanel(
            title = "Report",
            body = report,
        )
        Button(modifier = Modifier.fillMaxWidth(), onClick = onReturn) {
            Text("Back To Dashboard")
        }
    }
}

@Composable
private fun SettingsScreen(state: CoreLinkState, onReset: () -> Unit, onBack: () -> Unit) {
    ScreenContainer(title = "Settings") {
        HeaderCopy(
            overline = "Demo state",
            headline = "Current bot ${state.activeCore?.designation ?: "none"} stays local to this watch.",
        )
        StatusPanel(
            title = "Persistence",
            body = "One active core, its 8 matrix metrics, starter stats, Charge, Scrap, progress, condition, mood, low-power warning state, roam timer, and tuning timestamps are stored locally with SharedPreferences. Use Reset Demo State to clear them.",
        )
        StatusPanel(
            title = "MVP Deferrals",
            body = "Deferred beyond MVP: dead-core permanence, battles, capture, store, and a multi-bot squad.",
        )
        Button(modifier = Modifier.fillMaxWidth(), onClick = onReset) {
            Text("Reset Demo State")
        }
        Spacer(modifier = Modifier.height(8.dp))
        Button(modifier = Modifier.fillMaxWidth(), onClick = onBack) {
            Text("Back")
        }
    }
}

@Composable
private fun MatrixPanel(matrix: CoreMatrix) {
    StatusPanel(
        title = "Core Matrix",
        body = buildString {
            append("Aggression ${matrix.aggression}  Caution ${matrix.caution}\n")
            append("Curiosity ${matrix.curiosity}  Discipline ${matrix.discipline}\n")
            append("Loyalty ${matrix.loyalty}  Independence ${matrix.independence}\n")
            append("Imagination ${matrix.imagination}  Efficiency ${matrix.efficiency}")
        },
    )
}

@Composable
private fun CommandSurfacePanel(
    designation: String,
    mood: String,
    condition: Int,
    charge: Int,
    lowPower: Boolean,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFF22415F), RoundedCornerShape(22.dp))
            .background(Color(0xFF08111E), RoundedCornerShape(22.dp))
            .padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(
            text = "WRIST COMMAND SURFACE",
            color = Color(0xFF8BE9FD),
            fontSize = 10.sp,
            fontWeight = FontWeight.SemiBold,
        )
        Text(
            text = designation,
            color = Color.White,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = "Mood $mood  Condition $condition%  Charge $charge%",
            color = Color(0xFFB8C5D6),
            fontSize = 11.sp,
        )
        Text(
            text = if (lowPower) "STATUS: LOW-POWER / REPAIR WATCH" else "STATUS: CORE MATRIX SYNCED",
            color = if (lowPower) Color(0xFFFFB347) else Color(0xFF7EE787),
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium,
        )
    }
    Spacer(modifier = Modifier.height(10.dp))
}

@Composable
private fun TelemetryGrid(metrics: List<TelemetryMetric>) {
    metrics.chunked(2).forEach { rowMetrics ->
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            rowMetrics.forEach { metric ->
                Box(modifier = Modifier.weight(1f)) {
                    TelemetryCell(metric = metric)
                }
            }
            if (rowMetrics.size == 1) {
                Spacer(modifier = Modifier.weight(1f))
            }
        }
        Spacer(modifier = Modifier.height(8.dp))
    }
}

@Composable
private fun TelemetryCell(metric: TelemetryMetric) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF101826), RoundedCornerShape(18.dp))
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Text(
            text = metric.label,
            color = Color(0xFF90A3B8),
            fontSize = 10.sp,
        )
        Text(
            text = metric.value,
            color = metric.accent,
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
private fun DashboardReadout(title: String, body: String, accent: Color = Color(0xFF3AAED8)) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF101826), RoundedCornerShape(20.dp))
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .width(8.dp)
                    .height(8.dp)
                    .background(accent, RoundedCornerShape(99.dp)),
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = title,
                color = Color(0xFFB8C5D6),
                fontSize = 11.sp,
            )
        }
        Text(
            text = body,
            color = Color.White,
            textAlign = TextAlign.Start,
            fontSize = 12.sp,
        )
    }
    Spacer(modifier = Modifier.height(10.dp))
}

@Composable
private fun ScreenContainer(title: String, content: @Composable () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF030711))
            .padding(horizontal = 14.dp, vertical = 10.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = title,
                color = Color(0xFF8BE9FD),
                fontSize = 16.sp,
                fontWeight = FontWeight.SemiBold,
            )
            Spacer(modifier = Modifier.height(10.dp))
            content()
            Spacer(modifier = Modifier.height(18.dp))
        }
    }
}

@Composable
private fun HeaderCopy(overline: String, headline: String) {
    Text(
        text = overline,
        color = Color(0xFF7AA2F7),
        fontSize = 11.sp,
        textAlign = TextAlign.Center,
    )
    Spacer(modifier = Modifier.height(6.dp))
    Text(
        text = headline,
        color = Color.White,
        textAlign = TextAlign.Center,
        fontWeight = FontWeight.Medium,
    )
    Spacer(modifier = Modifier.height(12.dp))
}

@Composable
private fun ChoiceGroup(
    label: String,
    options: List<String>,
    selectedIndex: Int,
    onSelect: (Int) -> Unit,
) {
    StatusPanel(title = label, body = options[selectedIndex])
    options.forEachIndexed { index, option ->
        Button(modifier = Modifier.fillMaxWidth(), onClick = { onSelect(index) }) {
            Text(if (index == selectedIndex) "$option Selected" else option)
        }
        Spacer(modifier = Modifier.height(8.dp))
    }
}

@Composable
private fun StatusPanel(title: String, body: String, accent: Color = Color(0xFF3AAED8)) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF101826), RoundedCornerShape(20.dp))
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .width(8.dp)
                    .height(8.dp)
                    .background(accent, RoundedCornerShape(99.dp)),
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = title,
                color = Color(0xFFB8C5D6),
                fontSize = 11.sp,
            )
        }
        Text(
            text = body,
            color = Color.White,
            textAlign = TextAlign.Start,
        )
    }
    Spacer(modifier = Modifier.height(10.dp))
}

@Composable
private fun MeterRow(label: String, value: Int) {
    StatusPanel(
        title = label,
        body = "$value",
        accent = when {
            value < 15 -> Color(0xFFFFB347)
            value < 40 -> Color(0xFF7AA2F7)
            else -> Color(0xFF7EE787)
        },
    )
}

@Composable
private fun CoreLinkTheme(content: @Composable () -> Unit) {
    MaterialTheme(content = content)
}

private fun hasActivityRecognitionPermission(context: Context): Boolean =
    ContextCompat.checkSelfPermission(context, Manifest.permission.ACTIVITY_RECOGNITION) == PackageManager.PERMISSION_GRANTED
