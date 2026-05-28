package com.corelink.wear

data class CalibrationAnswers(
    val instinctIndex: Int = 0,
    val frameIndex: Int = 0,
    val doctrineIndex: Int = 0,
    val adaptationIndex: Int = 0,
)

data class CoreMatrix(
    val aggression: Int,
    val caution: Int,
    val curiosity: Int,
    val discipline: Int,
    val loyalty: Int,
    val independence: Int,
    val imagination: Int,
    val efficiency: Int,
)

data class StarterBotStats(
    val speed: Int,
    val memory: Int,
    val power: Int,
    val trust: Int,
    val weight: Int,
    val attack: Int,
    val defense: Int,
    val control: Int,
    val stability: Int,
    val temperament: String,
)

data class StarterCore(
    val designation: String,
    val frame: String,
    val mood: String,
    val matrix: CoreMatrix,
    val stats: StarterBotStats,
    val answers: CalibrationAnswers,
)

data class CoreLinkState(
    val calibrated: Boolean = false,
    val activeCore: StarterCore? = null,
    val charge: Int = 8,
    val scrap: Int = 4,
    val condition: Int = 62,
    val recoveryNotes: String = "Signal acquisition pending.",
    val lastRoamReport: String = "No roam runs yet.",
    val activityCarryoverSteps: Int = 0,
    val lastStepCounterTotal: Int? = null,
    val lastActivitySource: String = "Simulation standby",
    val lastActivitySummary: String = "No activity routed into the CoreLink capacitor yet.",
)

const val StepsPerChargeUnit = 40
const val SimulatedActivitySteps = 400
private const val MaxCharge = 100

private val instinctNames = listOf("Aegis", "Pulse", "Relay")
private val frameNames = listOf("Scout", "Forge", "Bloom")
private val doctrineNames = listOf("Ward", "Drive", "Weave")
private val adaptationNames = listOf("Anchor", "Surge", "Drift")

fun calibrateStarterCore(answers: CalibrationAnswers): StarterCore {
    val instinct = answers.instinctIndex
    val frame = answers.frameIndex
    val doctrine = answers.doctrineIndex
    val adaptation = answers.adaptationIndex

    fun score(base: Int, vararg contributions: Int): Int =
        (base + contributions.sum()).coerceIn(0, 100)

    val matrix = CoreMatrix(
        aggression = score(24, instinct * 14, doctrine * 9, frame * 5, -adaptation * 4),
        caution = score(28, (2 - instinct) * 8, frame * 10, (2 - adaptation) * 6, doctrine * 2),
        curiosity = score(26, adaptation * 15, (2 - frame) * 8, doctrine * 4, instinct * 3),
        discipline = score(32, doctrine * 14, frame * 7, (2 - adaptation) * 5, instinct * 2),
        loyalty = score(30, instinct * 6, frame * 8, (2 - adaptation) * 7, (2 - doctrine) * 4),
        independence = score(22, adaptation * 12, instinct * 5, doctrine * 6, -frame * 3),
        imagination = score(24, adaptation * 14, (2 - frame) * 6, (2 - instinct) * 4, doctrine * 3),
        efficiency = score(30, frame * 12, doctrine * 10, (2 - adaptation) * 6, instinct * 2),
    )

    val speed = (matrix.curiosity + matrix.independence) / 2
    val memory = (matrix.discipline + matrix.imagination + matrix.efficiency) / 3
    val power = (matrix.aggression + matrix.efficiency) / 2
    val trust = (matrix.loyalty + matrix.caution) / 2
    val weight = 32 + (frame * 12) + (doctrine * 4)
    val attack = (matrix.aggression + matrix.curiosity) / 2
    val defense = (matrix.caution + matrix.loyalty + matrix.discipline) / 3
    val control = (matrix.discipline + matrix.caution + matrix.efficiency) / 3
    val stability = (matrix.loyalty + control + matrix.efficiency) / 3

    val temperament = when {
        matrix.aggression >= 55 && control >= 55 -> "Vanguard"
        matrix.curiosity >= 60 && matrix.imagination >= 55 -> "Seeker"
        matrix.loyalty >= 55 && defense >= 55 -> "Sentinel"
        matrix.efficiency >= 60 -> "Operator"
        else -> "Balancer"
    }

    val stats = StarterBotStats(
        speed = speed,
        memory = memory,
        power = power,
        trust = trust,
        weight = weight,
        attack = attack,
        defense = defense,
        control = control,
        stability = stability,
        temperament = temperament,
    )

    val mood = when {
        stats.temperament == "Seeker" -> "Curious"
        stats.temperament == "Sentinel" -> "Guarded"
        stats.temperament == "Operator" -> "Steady"
        stats.temperament == "Vanguard" -> "Alert"
        else -> "Ready"
    }

    val designation = buildString {
        append(instinctNames[instinct].take(2).uppercase())
        append("-")
        append(frameNames[frame].take(2).uppercase())
        append(doctrineNames[doctrine].first())
        append(adaptationNames[adaptation].first())
    }

    return StarterCore(
        designation = designation,
        frame = "${instinctNames[instinct]} ${frameNames[frame]}",
        mood = mood,
        matrix = matrix,
        stats = stats,
        answers = answers,
    )
}

fun starterStateFromAnswers(answers: CalibrationAnswers): CoreLinkState {
    val starterCore = calibrateStarterCore(answers)
    return CoreLinkState(
        calibrated = true,
        activeCore = starterCore,
        charge = 24 + (starterCore.stats.control / 8),
        scrap = 6 + (starterCore.matrix.efficiency / 20),
        condition = 68 + (starterCore.stats.stability / 8),
        recoveryNotes = "Recovered AI core synchronized through deterministic Core Matrix calibration.",
        lastRoamReport = "Starter bot ready for first roam dispatch.",
        lastActivitySummary = "CoreLink capacitor primed. Route steps or use simulation to generate Charge.",
    )
}

fun applySimulatedActivityBurst(
    state: CoreLinkState,
    simulatedSteps: Int = SimulatedActivitySteps,
): CoreLinkState =
    applyActivityDelta(
        state = state,
        deltaSteps = simulatedSteps,
        source = "Simulated activity",
        intro = "Simulation routed $simulatedSteps activity steps into the shared capacitor.",
    )

fun applyWearStepSample(state: CoreLinkState, totalSteps: Int): CoreLinkState {
    val normalizedTotal = totalSteps.coerceAtLeast(0)
    val previousTotal = state.lastStepCounterTotal

    if (previousTotal == null) {
        return state.copy(
            lastStepCounterTotal = normalizedTotal,
            lastActivitySource = "Wear OS step sensor",
            lastActivitySummary = "Step counter linked at $normalizedTotal total steps. Walk to route Charge into the shared capacitor.",
            recoveryNotes = "Wear OS step sensor linked. CoreLink converts every $StepsPerChargeUnit steps into 1 Charge.",
        )
    }

    if (normalizedTotal < previousTotal) {
        return state.copy(
            lastStepCounterTotal = normalizedTotal,
            activityCarryoverSteps = 0,
            lastActivitySource = "Wear OS step sensor",
            lastActivitySummary = "Step counter reset detected. CoreLink re-linked at $normalizedTotal total steps.",
            recoveryNotes = "Wear OS step counter reset detected. Charge conversion resumed from the new baseline.",
        )
    }

    val deltaSteps = normalizedTotal - previousTotal
    if (deltaSteps == 0) {
        return state
    }

    val updatedState = applyActivityDelta(
        state = state,
        deltaSteps = deltaSteps,
        source = "Wear OS step sensor",
        intro = "Detected $deltaSteps new step(s) from the watch sensor.",
    )

    return updatedState.copy(lastStepCounterTotal = normalizedTotal)
}

private fun applyActivityDelta(
    state: CoreLinkState,
    deltaSteps: Int,
    source: String,
    intro: String,
): CoreLinkState {
    val sanitizedSteps = deltaSteps.coerceAtLeast(0)
    if (sanitizedSteps == 0) {
        return state
    }

    val availableSteps = state.activityCarryoverSteps + sanitizedSteps
    val rawChargeGain = availableSteps / StepsPerChargeUnit
    val chargeHeadroom = MaxCharge - state.charge
    val appliedChargeGain = rawChargeGain.coerceAtMost(chargeHeadroom)
    val consumedSteps = appliedChargeGain * StepsPerChargeUnit
    val remainingSteps = if (chargeHeadroom == 0) {
        0
    } else {
        availableSteps - consumedSteps
    }
    val nextCharge = state.charge + appliedChargeGain
    val nextMood = if (nextCharge >= 60) "Steady" else "Alert"

    val summary = if (appliedChargeGain > 0) {
        "$intro Generated +$appliedChargeGain Charge. $remainingSteps/$StepsPerChargeUnit steps banked toward the next Charge."
    } else if (chargeHeadroom == 0) {
        "$intro Capacitor already full at $MaxCharge Charge."
    } else {
        "$intro No Charge generated yet. $remainingSteps/$StepsPerChargeUnit steps banked toward the next Charge."
    }

    val note = if (appliedChargeGain > 0) {
        "Activity routed through the shared CoreLink capacitor and increased Charge by $appliedChargeGain."
    } else if (chargeHeadroom == 0) {
        "Activity registered, but the shared CoreLink capacitor is already full."
    } else {
        "Activity registered. CoreLink needs $StepsPerChargeUnit steps for each Charge unit."
    }

    return state.copy(
        activeCore = state.activeCore?.copy(mood = nextMood),
        charge = nextCharge,
        activityCarryoverSteps = remainingSteps,
        lastActivitySource = source,
        lastActivitySummary = summary,
        recoveryNotes = note,
    )
}

object CoreLinkStateCodec {
    fun encode(state: CoreLinkState): Map<String, String> {
        val values = linkedMapOf(
            "calibrated" to state.calibrated.toString(),
            "charge" to state.charge.toString(),
            "scrap" to state.scrap.toString(),
            "condition" to state.condition.toString(),
            "recoveryNotes" to state.recoveryNotes,
            "lastRoamReport" to state.lastRoamReport,
            "activityCarryoverSteps" to state.activityCarryoverSteps.toString(),
            "lastStepCounterTotal" to (state.lastStepCounterTotal?.toString() ?: ""),
            "lastActivitySource" to state.lastActivitySource,
            "lastActivitySummary" to state.lastActivitySummary,
        )

        val core = state.activeCore
        if (core != null) {
            values["hasCore"] = true.toString()
            values["designation"] = core.designation
            values["frame"] = core.frame
            values["mood"] = core.mood
            values["aggression"] = core.matrix.aggression.toString()
            values["caution"] = core.matrix.caution.toString()
            values["curiosity"] = core.matrix.curiosity.toString()
            values["discipline"] = core.matrix.discipline.toString()
            values["loyalty"] = core.matrix.loyalty.toString()
            values["independence"] = core.matrix.independence.toString()
            values["imagination"] = core.matrix.imagination.toString()
            values["efficiency"] = core.matrix.efficiency.toString()
            values["speed"] = core.stats.speed.toString()
            values["memory"] = core.stats.memory.toString()
            values["power"] = core.stats.power.toString()
            values["trust"] = core.stats.trust.toString()
            values["weight"] = core.stats.weight.toString()
            values["attack"] = core.stats.attack.toString()
            values["defense"] = core.stats.defense.toString()
            values["control"] = core.stats.control.toString()
            values["stability"] = core.stats.stability.toString()
            values["temperament"] = core.stats.temperament
            values["instinctIndex"] = core.answers.instinctIndex.toString()
            values["frameIndex"] = core.answers.frameIndex.toString()
            values["doctrineIndex"] = core.answers.doctrineIndex.toString()
            values["adaptationIndex"] = core.answers.adaptationIndex.toString()
        } else {
            values["hasCore"] = false.toString()
        }

        return values
    }

    fun decode(values: Map<String, String>): CoreLinkState {
        val hasCore = values["hasCore"]?.toBoolean() ?: false
        return CoreLinkState(
            calibrated = values["calibrated"]?.toBoolean() ?: false,
            activeCore = if (hasCore) {
                StarterCore(
                    designation = values["designation"] ?: "",
                    frame = values["frame"] ?: "Dormant",
                    mood = values["mood"] ?: "Unlinked",
                    matrix = CoreMatrix(
                        aggression = values.intValue("aggression", 0),
                        caution = values.intValue("caution", 0),
                        curiosity = values.intValue("curiosity", 0),
                        discipline = values.intValue("discipline", 0),
                        loyalty = values.intValue("loyalty", 0),
                        independence = values.intValue("independence", 0),
                        imagination = values.intValue("imagination", 0),
                        efficiency = values.intValue("efficiency", 0),
                    ),
                    stats = StarterBotStats(
                        speed = values.intValue("speed", 0),
                        memory = values.intValue("memory", 0),
                        power = values.intValue("power", 0),
                        trust = values.intValue("trust", 0),
                        weight = values.intValue("weight", 32),
                        attack = values.intValue("attack", 0),
                        defense = values.intValue("defense", 0),
                        control = values.intValue("control", 0),
                        stability = values.intValue("stability", 0),
                        temperament = values["temperament"] ?: "Balancer",
                    ),
                    answers = CalibrationAnswers(
                        instinctIndex = values.intValue("instinctIndex", 0),
                        frameIndex = values.intValue("frameIndex", 0),
                        doctrineIndex = values.intValue("doctrineIndex", 0),
                        adaptationIndex = values.intValue("adaptationIndex", 0),
                    ),
                )
            } else {
                null
            },
            charge = values.intValue("charge", 8),
            scrap = values.intValue("scrap", 4),
            condition = values.intValue("condition", 62),
            recoveryNotes = values["recoveryNotes"] ?: "Signal acquisition pending.",
            lastRoamReport = values["lastRoamReport"] ?: "No roam runs yet.",
            activityCarryoverSteps = values.intValue("activityCarryoverSteps", 0),
            lastStepCounterTotal = values["lastStepCounterTotal"]?.toIntOrNull(),
            lastActivitySource = values["lastActivitySource"] ?: "Simulation standby",
            lastActivitySummary = values["lastActivitySummary"] ?: "No activity routed into the CoreLink capacitor yet.",
        )
    }

    private fun Map<String, String>.intValue(key: String, fallback: Int): Int =
        get(key)?.toIntOrNull() ?: fallback
}
