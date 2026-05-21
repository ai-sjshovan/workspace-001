package com.codexfoundry.derpyowl

import org.junit.Assert.assertEquals
import org.junit.Test

class ScoreAchievementsTest {
    @Test
    fun unlocksTenPointMilestoneOnce() {
        assertEquals(listOf(10), ScoreAchievements.newlyUnlocked(currentScore = 10, alreadyUnlocked = emptyList()))
        assertEquals(emptyList<Int>(), ScoreAchievements.newlyUnlocked(currentScore = 10, alreadyUnlocked = listOf(10)))
    }

    @Test
    fun unlocksTwentyFiveAfterTenAndMergesPersistedMilestones() {
        val newUnlocks = ScoreAchievements.newlyUnlocked(currentScore = 25, alreadyUnlocked = listOf(10))
        assertEquals(listOf(25), newUnlocks)
        assertEquals(listOf(10, 25), ScoreAchievements.mergedUnlocked(listOf(10), newUnlocks))
    }
}
