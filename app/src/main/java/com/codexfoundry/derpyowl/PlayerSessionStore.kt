package com.codexfoundry.derpyowl

import android.content.Context
import android.net.Uri

enum class AuthProvider {
    GOOGLE,
    DEV_FALLBACK,
}

data class PlayerIdentity(
    val id: String,
    val displayName: String,
    val provider: AuthProvider,
    val email: String? = null,
) {
    companion object {
        fun devFallback(): PlayerIdentity =
            PlayerIdentity(
                id = "dev-local-nest-tester",
                displayName = "Local Nest Tester",
                provider = AuthProvider.DEV_FALLBACK,
            )
    }
}

data class PlayerScoreSummary(
    val bestScore: Int = 0,
    val lastScore: Int = 0,
    val runCount: Int = 0,
    val unlockedMilestones: List<Int> = emptyList(),
)

class PlayerSessionStore(context: Context) {
    companion object {
        val SCORE_MILESTONES = ScoreAchievements.milestoneTargets
        private const val KEY_CURRENT_PLAYER_ID = "current_player_id"
        private const val KEY_CURRENT_PLAYER_NAME = "current_player_name"
        private const val KEY_CURRENT_PLAYER_PROVIDER = "current_player_provider"
        private const val KEY_CURRENT_PLAYER_EMAIL = "current_player_email"
    }

    private val prefs = context.getSharedPreferences("derpy_owl_player_state", Context.MODE_PRIVATE)

    fun loadCurrentPlayer(): PlayerIdentity? {
        val playerId = prefs.getString(KEY_CURRENT_PLAYER_ID, null) ?: return null
        val displayName = prefs.getString(KEY_CURRENT_PLAYER_NAME, null) ?: return null
        val providerName = prefs.getString(KEY_CURRENT_PLAYER_PROVIDER, null) ?: return null
        val provider = AuthProvider.entries.firstOrNull { it.name == providerName } ?: return null
        return PlayerIdentity(
            id = playerId,
            displayName = displayName,
            provider = provider,
            email = prefs.getString(KEY_CURRENT_PLAYER_EMAIL, null),
        )
    }

    fun saveCurrentPlayer(player: PlayerIdentity) {
        prefs.edit()
            .putString(KEY_CURRENT_PLAYER_ID, player.id)
            .putString(KEY_CURRENT_PLAYER_NAME, player.displayName)
            .putString(KEY_CURRENT_PLAYER_PROVIDER, player.provider.name)
            .putString(KEY_CURRENT_PLAYER_EMAIL, player.email)
            .apply()
    }

    fun getScoreSummary(playerId: String): PlayerScoreSummary {
        val prefix = playerPrefix(playerId)
        return PlayerScoreSummary(
            bestScore = prefs.getInt("${prefix}best_score", 0),
            lastScore = prefs.getInt("${prefix}last_score", 0),
            runCount = prefs.getInt("${prefix}run_count", 0),
            unlockedMilestones = SCORE_MILESTONES.filter { prefs.getBoolean("${prefix}milestone_$it", false) },
        )
    }

    fun saveCompletedRun(playerId: String, score: Int, newlyUnlockedMilestones: List<Int> = emptyList()): PlayerScoreSummary {
        val existing = getScoreSummary(playerId)
        val mergedMilestones = ScoreAchievements.mergedUnlocked(existing.unlockedMilestones, newlyUnlockedMilestones)
        val updated = PlayerScoreSummary(
            bestScore = maxOf(existing.bestScore, score),
            lastScore = score,
            runCount = existing.runCount + 1,
            unlockedMilestones = mergedMilestones,
        )
        val prefix = playerPrefix(playerId)
        val editor = prefs.edit()
            .putInt("${prefix}best_score", updated.bestScore)
            .putInt("${prefix}last_score", updated.lastScore)
            .putInt("${prefix}run_count", updated.runCount)
        SCORE_MILESTONES.forEach { milestone ->
            editor.putBoolean("${prefix}milestone_$milestone", milestone in mergedMilestones)
        }
        editor.apply()
        return updated
    }

    private fun playerPrefix(playerId: String): String = "player_${Uri.encode(playerId)}_"
}
