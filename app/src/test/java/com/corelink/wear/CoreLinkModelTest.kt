package com.corelink.wear

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class CoreLinkModelTest {
    @Test
    fun calibrationIsDeterministicForSameAnswers() {
        val answers = CalibrationAnswers(
            instinctIndex = 2,
            frameIndex = 1,
            doctrineIndex = 0,
            adaptationIndex = 2,
        )

        val first = starterStateFromAnswers(answers)
        val second = starterStateFromAnswers(answers)

        assertEquals(first, second)
        assertEquals("RE-FOWD", first.activeCore?.designation)
    }

    @Test
    fun stateCodecRoundTripsSingleActiveCore() {
        val original = starterStateFromAnswers(
            CalibrationAnswers(
                instinctIndex = 1,
                frameIndex = 2,
                doctrineIndex = 1,
                adaptationIndex = 0,
            ),
        ).copy(
            charge = 41,
            scrap = 11,
            condition = 89,
            recoveryNotes = "Manual verification note.",
            lastRoamReport = "Roam result persisted.",
            lastChargeChangeAtEpochMillis = 1_000L,
            lastConditionChangeAtEpochMillis = 2_000L,
            lastRoamStartedAtEpochMillis = 3_000L,
            lastRepairAtEpochMillis = 4_000L,
            lastStateSyncEpochMillis = 5_000L,
        )

        val restored = CoreLinkStateCodec.decode(CoreLinkStateCodec.encode(original))

        assertEquals(original, restored)
        assertNotNull(restored.activeCore)
    }

    @Test
    fun emptyStateCodecRoundTripsWithoutCore() {
        val restored = CoreLinkStateCodec.decode(CoreLinkStateCodec.encode(CoreLinkState()))

        assertEquals(CoreLinkState(), restored)
        assertNull(restored.activeCore)
    }

    @Test
    fun simulatedActivityUsesDeterministicChargeConversion() {
        val initial = starterStateFromAnswers(CalibrationAnswers())
        val updated = applySimulatedActivityBurst(initial)

        assertEquals(initial.charge + (SimulatedActivitySteps / StepsPerChargeUnit), updated.charge)
        assertEquals(0, updated.activityCarryoverSteps)
        assertEquals("Simulated activity", updated.lastActivitySource)
    }

    @Test
    fun wearStepSampleBanksRemainderAcrossUpdates() {
        val baseline = starterStateFromAnswers(CalibrationAnswers())
        val linked = applyWearStepSample(baseline, totalSteps = 1_000)
        val firstGain = applyWearStepSample(linked, totalSteps = 1_050)
        val secondGain = applyWearStepSample(firstGain, totalSteps = 1_070)

        assertEquals(baseline.charge, linked.charge)
        assertEquals(baseline.charge + 1, firstGain.charge)
        assertEquals(10, firstGain.activityCarryoverSteps)
        assertEquals(baseline.charge + 1, secondGain.charge)
        assertEquals(30, secondGain.activityCarryoverSteps)
    }

    @Test
    fun wearStepSampleResetsBaselineWhenCounterDrops() {
        val baseline = starterStateFromAnswers(CalibrationAnswers())
        val linked = applyWearStepSample(baseline, totalSteps = 250)
        val reset = applyWearStepSample(linked.copy(activityCarryoverSteps = 12), totalSteps = 10)

        assertEquals(10, reset.lastStepCounterTotal)
        assertEquals(0, reset.activityCarryoverSteps)
        assertEquals("Wear OS step sensor", reset.lastActivitySource)
    }

    @Test
    fun roamDispatchConsumesChargeAndPersistsTimerState() {
        val initial = starterStateFromAnswers(CalibrationAnswers()).copy(charge = 40, condition = 72)

        val dispatched = dispatchRoam(initial, nowEpochMillis = 10_000L)
        val restored = CoreLinkStateCodec.decode(CoreLinkStateCodec.encode(dispatched))

        assertEquals(40 - RoamChargeCost, dispatched.charge)
        assertEquals(10_000L + RoamDurationMillis, dispatched.roamEndsAtEpochMillis)
        assertEquals(RoamStatus.Roaming, roamStatus(restored, nowEpochMillis = 20_000L))
        assertEquals(RoamStatus.ReadyToReturn, roamStatus(restored, nowEpochMillis = 80_000L))
        assertEquals(dispatched, restored)
    }

    @Test
    fun lowPowerStateActivatesPersistsAndClearsAfterRecharge() {
        val baseline = starterStateFromAnswers(CalibrationAnswers()).copy(
            charge = 18,
            condition = 70,
            lowPowerWarningActive = false,
            lowPowerEnteredAtEpochMillis = null,
        )

        val enteredLowPower = repairBot(baseline, nowEpochMillis = 12_000L)
        val restoredLowPower = CoreLinkStateCodec.decode(CoreLinkStateCodec.encode(enteredLowPower))
        val recovered = applySimulatedActivityBurst(restoredLowPower, simulatedSteps = 80)

        assertTrue(enteredLowPower.lowPowerWarningActive)
        assertEquals(12_000L, enteredLowPower.lowPowerEnteredAtEpochMillis)
        assertEquals("Low Power", enteredLowPower.activeCore?.mood)
        assertTrue(roamDispatchGate(restoredLowPower, nowEpochMillis = 12_500L).message.contains("Low Power"))
        assertFalse(recovered.lowPowerWarningActive)
        assertNull(recovered.lowPowerEnteredAtEpochMillis)
    }

    @Test
    fun roamReturnGrantsDeterministicScrapAndProgress() {
        val initial = starterStateFromAnswers(CalibrationAnswers()).copy(charge = 40, scrap = 7, progress = 3, condition = 75)
        val dispatched = dispatchRoam(initial, nowEpochMillis = 0L)

        val returned = resolveRoamReturn(dispatched, nowEpochMillis = RoamDurationMillis + 1L)

        assertEquals(12, returned.scrap)
        assertEquals(10, returned.progress)
        assertEquals(67, returned.condition)
        assertNull(returned.roamEndsAtEpochMillis)
    }

    @Test
    fun repairConsumesResourcesAndImprovesCondition() {
        val initial = starterStateFromAnswers(CalibrationAnswers()).copy(charge = 22, scrap = 9, condition = 54)

        val repaired = repairBot(initial, nowEpochMillis = 0L)

        assertEquals(22 - RepairChargeCost, repaired.charge)
        assertEquals(9 - RepairScrapCost, repaired.scrap)
        assertEquals(54 + RepairConditionGain, repaired.condition)
    }

    @Test
    fun actionsWarnWhenChargeOrConditionIsInsufficient() {
        val lowCharge = starterStateFromAnswers(CalibrationAnswers()).copy(charge = 2, scrap = 0, condition = 28)
        val lowCondition = starterStateFromAnswers(CalibrationAnswers()).copy(charge = 40, condition = 24)

        val repairGate = repairGate(lowCharge, nowEpochMillis = 0L)
        val roamGate = roamDispatchGate(lowCondition, nowEpochMillis = 0L)

        assertFalse(repairGate.allowed)
        assertTrue(repairGate.message.contains("Charge"))
        assertFalse(roamGate.allowed)
        assertTrue(roamGate.message.contains("Condition"))
    }
}
