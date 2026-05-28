package com.corelink.wear

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.wear.compose.material3.Button
import androidx.wear.compose.material3.MaterialTheme
import androidx.wear.compose.material3.Text

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

    fun commit(nextState: CoreLinkState) {
        state = nextState
        CoreLinkPrefs.save(context, nextState)
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
            onSimulateActivity = {
                val nextCharge = (state.charge + 10).coerceAtMost(100)
                val nextMood = if (nextCharge >= 60) "Steady" else "Alert"
                commit(
                    state.copy(
                        activeCore = state.activeCore?.copy(mood = nextMood),
                        charge = nextCharge,
                        recoveryNotes = "Charge spike captured from simulated activity.",
                    ),
                )
            },
            onRepair = {
                if (state.charge >= 5 && state.scrap >= 3) {
                    commit(
                        state.copy(
                            activeCore = state.activeCore?.copy(mood = "Stabilized"),
                            charge = state.charge - 5,
                            scrap = state.scrap - 3,
                            condition = (state.condition + 12).coerceAtMost(100),
                            recoveryNotes = "${state.activeCore?.designation ?: "Starter bot"} repaired from scavenged scrap.",
                        ),
                    )
                }
            },
            onRoam = {
                if (state.charge >= 12) {
                    val haul = 2 + (state.condition / 25)
                    val updated = state.copy(
                        activeCore = state.activeCore?.copy(mood = "Curious"),
                        charge = state.charge - 12,
                        scrap = state.scrap + haul,
                        lastRoamReport = "${state.activeCore?.designation ?: "Starter bot"} returned with $haul Scrap after scanning the deadband.",
                        recoveryNotes = "Roam consumed 12 Charge and expanded local salvage stores.",
                    )
                    commit(updated)
                    screen = Screen.RoamReport
                }
            },
            onOpenSettings = { screen = Screen.Settings },
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
    onSimulateActivity: () -> Unit,
    onRepair: () -> Unit,
    onRoam: () -> Unit,
    onOpenSettings: () -> Unit,
) {
    val lowPower = state.charge < 15
    val core = state.activeCore

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
            lowPower = lowPower,
        )
        TelemetryGrid(
            metrics = listOf(
                TelemetryMetric("Charge", "${state.charge}%", metricAccent(state.charge)),
                TelemetryMetric("Scrap", state.scrap.toString(), metricAccent(state.scrap * 10)),
                TelemetryMetric("Condition", "${state.condition}%", metricAccent(state.condition)),
                TelemetryMetric("Power State", if (lowPower) "LOW" else "STABLE", if (lowPower) Color(0xFFFFB347) else Color(0xFF7EE787)),
            ),
        )
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
                accent = if (state.condition < 55 || lowPower) Color(0xFFFFB347) else Color(0xFF7EE787),
            )
        }
        DashboardReadout(
            title = "Ops Log",
            body = "${state.recoveryNotes}\n${state.lastRoamReport}",
        )
        Button(modifier = Modifier.fillMaxWidth(), onClick = onSimulateActivity) {
            Text("Simulate Activity +10 Charge")
        }
        Spacer(modifier = Modifier.height(8.dp))
        Button(modifier = Modifier.fillMaxWidth(), onClick = onRepair, enabled = state.charge >= 5 && state.scrap >= 3) {
            Text("Repair -5 Charge / -3 Scrap")
        }
        Spacer(modifier = Modifier.height(8.dp))
        Button(modifier = Modifier.fillMaxWidth(), onClick = onRoam, enabled = state.charge >= 12) {
            Text("Dispatch Roam -12 Charge")
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
        if (state.charge < 15) {
            append("Low power. Route activity before roam. ")
        } else {
            append("Charge reserves ready for field work. ")
        }
        if (state.condition < 55) {
            append("Condition degraded. Repair needs 5 Charge and 3 Scrap.")
        } else {
            append("Condition holding. Repair remains optional at 5 Charge and 3 Scrap.")
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
            body = "One active core, its 8 matrix metrics, starter stats, Charge, Scrap, condition, mood, and the last roam report are stored locally with SharedPreferences. Use Reset Demo State to clear them.",
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
