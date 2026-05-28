package com.corelink.wear

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
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
import androidx.compose.runtime.mutableIntStateOf
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

private data class CoreLinkState(
    val calibrated: Boolean = false,
    val botName: String = "",
    val botFrame: String = "Dormant",
    val mood: String = "Unlinked",
    val charge: Int = 8,
    val scrap: Int = 4,
    val condition: Int = 62,
    val recoveryNotes: String = "Signal acquisition pending.",
    val lastRoamReport: String = "No roam runs yet.",
)

private object CoreLinkPrefs {
    private const val Name = "corelink_state"
    private const val KeyCalibrated = "calibrated"
    private const val KeyBotName = "bot_name"
    private const val KeyBotFrame = "bot_frame"
    private const val KeyMood = "mood"
    private const val KeyCharge = "charge"
    private const val KeyScrap = "scrap"
    private const val KeyCondition = "condition"
    private const val KeyRecoveryNotes = "recovery_notes"
    private const val KeyLastRoamReport = "last_roam_report"

    fun load(context: Context): CoreLinkState {
        val prefs = context.getSharedPreferences(Name, Context.MODE_PRIVATE)
        return CoreLinkState(
            calibrated = prefs.getBoolean(KeyCalibrated, false),
            botName = prefs.getString(KeyBotName, "") ?: "",
            botFrame = prefs.getString(KeyBotFrame, "Dormant") ?: "Dormant",
            mood = prefs.getString(KeyMood, "Unlinked") ?: "Unlinked",
            charge = prefs.getInt(KeyCharge, 8),
            scrap = prefs.getInt(KeyScrap, 4),
            condition = prefs.getInt(KeyCondition, 62),
            recoveryNotes = prefs.getString(KeyRecoveryNotes, "Signal acquisition pending.") ?: "Signal acquisition pending.",
            lastRoamReport = prefs.getString(KeyLastRoamReport, "No roam runs yet.") ?: "No roam runs yet.",
        )
    }

    fun save(context: Context, state: CoreLinkState) {
        context.getSharedPreferences(Name, Context.MODE_PRIVATE).edit()
            .putBoolean(KeyCalibrated, state.calibrated)
            .putString(KeyBotName, state.botName)
            .putString(KeyBotFrame, state.botFrame)
            .putString(KeyMood, state.mood)
            .putInt(KeyCharge, state.charge)
            .putInt(KeyScrap, state.scrap)
            .putInt(KeyCondition, state.condition)
            .putString(KeyRecoveryNotes, state.recoveryNotes)
            .putString(KeyLastRoamReport, state.lastRoamReport)
            .apply()
    }
}

@Composable
private fun CoreLinkApp(context: Context) {
    val initialState = remember(context) { CoreLinkPrefs.load(context) }
    var state by remember { mutableStateOf(initialState) }
    var screen by remember { mutableStateOf(if (initialState.calibrated) Screen.Dashboard else Screen.Recovery) }
    var temperamentIndex by remember { mutableIntStateOf(0) }
    var chassisIndex by remember { mutableIntStateOf(0) }

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
            temperamentIndex = temperamentIndex,
            chassisIndex = chassisIndex,
            onTemperamentChange = { temperamentIndex = it },
            onChassisChange = { chassisIndex = it },
            onCalibrate = {
                val calibratedState = starterStateFromAnswers(temperamentIndex, chassisIndex)
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
                        charge = nextCharge,
                        mood = nextMood,
                        recoveryNotes = "Charge spike captured from simulated activity.",
                    ),
                )
            },
            onRepair = {
                if (state.charge >= 5 && state.scrap >= 3) {
                    commit(
                        state.copy(
                            charge = state.charge - 5,
                            scrap = state.scrap - 3,
                            condition = (state.condition + 12).coerceAtMost(100),
                            mood = "Stabilized",
                            recoveryNotes = "${state.botName} repaired from scavenged scrap.",
                        ),
                    )
                }
            },
            onRoam = {
                if (state.charge >= 12) {
                    val haul = 2 + (state.condition / 25)
                    val updated = state.copy(
                        charge = state.charge - 12,
                        scrap = state.scrap + haul,
                        mood = "Curious",
                        lastRoamReport = "${state.botName} returned with $haul Scrap after scanning the deadband.",
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
                temperamentIndex = 0
                chassisIndex = 0
                screen = Screen.Recovery
            },
            onBack = { screen = Screen.Dashboard },
        )
    }
}

private fun starterStateFromAnswers(temperamentIndex: Int, chassisIndex: Int): CoreLinkState {
    val temperaments = listOf("Aegis", "Pulse", "Relay")
    val chassis = listOf("Scout", "Forge", "Bloom")
    val names = listOf(
        listOf("Aegis-S9", "Aegis-F3", "Aegis-L2"),
        listOf("Pulse-S7", "Pulse-F5", "Pulse-L4"),
        listOf("Relay-S4", "Relay-F8", "Relay-L6"),
    )
    val baseMood = listOf("Guarded", "Restless", "Curious")
    val frame = "${temperaments[temperamentIndex]} ${chassis[chassisIndex]}"
    return CoreLinkState(
        calibrated = true,
        botName = names[temperamentIndex][chassisIndex],
        botFrame = frame,
        mood = baseMood[temperamentIndex],
        charge = 26 + (temperamentIndex * 6),
        scrap = 7 + chassisIndex,
        condition = 70 + (chassisIndex * 4),
        recoveryNotes = "Recovered AI core synchronized through a deterministic Core Matrix calibration.",
        lastRoamReport = "Starter bot ready for first roam dispatch.",
    )
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
    temperamentIndex: Int,
    chassisIndex: Int,
    onTemperamentChange: (Int) -> Unit,
    onChassisChange: (Int) -> Unit,
    onCalibrate: () -> Unit,
) {
    val temperamentOptions = listOf("Aegis", "Pulse", "Relay")
    val chassisOptions = listOf("Scout", "Forge", "Bloom")

    ScreenContainer(title = "Calibration") {
        HeaderCopy(
            overline = "Core Matrix",
            headline = "Answer two prompts to generate a deterministic starter AI core.",
        )
        ChoiceGroup(
            label = "Recovery instinct",
            options = temperamentOptions,
            selectedIndex = temperamentIndex,
            onSelect = onTemperamentChange,
        )
        ChoiceGroup(
            label = "Frame bias",
            options = chassisOptions,
            selectedIndex = chassisIndex,
            onSelect = onChassisChange,
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

    ScreenContainer(title = state.botName.ifBlank { "CoreLink" }) {
        HeaderCopy(
            overline = state.botFrame,
            headline = "Mood ${state.mood}  Condition ${state.condition}%",
        )
        StatusPanel(
            title = "Watch Status",
            body = if (lowPower) {
                "Low-power warning. Route activity into Charge before the next roam."
            } else {
                "Core stable. Dashboard synced to the active watch rig."
            },
            accent = if (lowPower) Color(0xFFFFB347) else Color(0xFF7EE787),
        )
        MeterRow("Charge", state.charge)
        MeterRow("Scrap", state.scrap)
        MeterRow("Condition", state.condition)
        StatusPanel(
            title = "Recovery Log",
            body = state.recoveryNotes,
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
            headline = "Current bot ${state.botName.ifBlank { "none" }} stays local to this watch.",
        )
        StatusPanel(
            title = "Persistence",
            body = "Charge, Scrap, condition, mood, and the last roam report are stored locally with SharedPreferences.",
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
