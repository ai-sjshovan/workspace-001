package com.corelink.wear

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
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
}
