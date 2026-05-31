package com.corelink.wear

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class CoreLinkModelTest {
    @Test
    fun starterCalibrationCreatesOneActiveCore() {
        val state = starterStateFromAnswers(
            CalibrationAnswers(
                instinctIndex = 2,
                frameIndex = 1,
                doctrineIndex = 0,
                adaptationIndex = 2,
            ),
        )

        assertTrue(state.calibrated)
        assertEquals("RE-FOWD", state.activeCore?.designation)
        assertEquals("Relay Forge", state.activeCore?.frame)
        assertEquals(RecoveryStage.Complete, state.recoveryStage)
        assertEquals(
            CalibrationAnswers(
                instinctIndex = 2,
                frameIndex = 1,
                doctrineIndex = 0,
                adaptationIndex = 2,
            ),
            state.activeCore?.answers,
        )
        assertTrue(state.recoveryNotes.contains("deterministic Core Matrix calibration"))
    }

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
        assertEquals(first.pendingCalibrationAnswers, second.pendingCalibrationAnswers)
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
            recoveryStage = RecoveryStage.Complete,
            pendingCalibrationAnswers = CalibrationAnswers(1, 2, 1, 0),
            calibrationQuestionIndex = 3,
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
    fun resetDemoStateClearsRecoveredCoreAndProgress() {
        val populated = starterStateFromAnswers(CalibrationAnswers()).copy(
            charge = 52,
            scrap = 13,
            progress = 7,
            condition = 91,
            recoveryNotes = "Recovered state.",
            lastRoamReport = "Roam return ready.",
        )

        val reset = resetDemoState()

        assertEquals(CoreLinkState(), reset)
        assertNotNull(populated.activeCore)
        assertNull(reset.activeCore)
    }

    @Test
    fun onboardingProgressRoundTripsBeforeCalibrationCompletes() {
        val original = CoreLinkState(
            recoveryStage = RecoveryStage.Calibration,
            pendingCalibrationAnswers = CalibrationAnswers(
                instinctIndex = 1,
                frameIndex = 2,
                doctrineIndex = 0,
                adaptationIndex = 1,
            ),
            calibrationQuestionIndex = 2,
            recoveryNotes = "Core Matrix calibration required before deployment.",
        )

        val restored = CoreLinkStateCodec.decode(CoreLinkStateCodec.encode(original))

        assertEquals(RecoveryStage.Calibration, restored.recoveryStage)
        assertEquals(original.pendingCalibrationAnswers, restored.pendingCalibrationAnswers)
        assertEquals(2, restored.calibrationQuestionIndex)
        assertFalse(restored.calibrated)
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
    fun lowPowerGapReportsRemainingChargeNeeded() {
        val lowPower = starterStateFromAnswers(CalibrationAnswers()).copy(charge = 9)
        val recovered = starterStateFromAnswers(CalibrationAnswers()).copy(charge = 24)

        assertEquals(6, chargeNeededToExitLowPower(lowPower))
        assertEquals(0, chargeNeededToExitLowPower(recovered))
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
    fun scanUpdatesRecoveryNotesWithoutBreakingState() {
        val initial = starterStateFromAnswers(CalibrationAnswers())

        val scanned = scanCore(initial, nowEpochMillis = 2_000L)

        assertEquals(initial.charge, scanned.charge)
        assertEquals(initial.scrap, scanned.scrap)
        assertEquals("Curious", scanned.activeCore?.mood)
        assertTrue(scanned.recoveryNotes.contains("scan complete"))
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
