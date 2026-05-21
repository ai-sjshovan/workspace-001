package com.codexfoundry.derpyowl

object ScoreAchievements {
    val milestoneTargets = listOf(10, 25, 50, 100)

    fun newlyUnlocked(currentScore: Int, alreadyUnlocked: Collection<Int>): List<Int> =
        milestoneTargets.filter { milestone -> currentScore >= milestone && milestone !in alreadyUnlocked }

    fun mergedUnlocked(existing: Collection<Int>, newUnlocks: Collection<Int>): List<Int> =
        (existing + newUnlocks).distinct().sorted()
}
