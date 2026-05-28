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
}
