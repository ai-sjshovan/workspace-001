package com.codexfoundry.derpyowl

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.credentials.CredentialManager
import androidx.credentials.CredentialManagerCallback
import androidx.credentials.CustomCredential
import androidx.credentials.GetCredentialRequest
import androidx.credentials.GetCredentialResponse
import androidx.credentials.exceptions.GetCredentialException
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.codexfoundry.derpyowl.databinding.ActivityMainBinding
import com.google.android.gms.common.ConnectionResult
import com.google.android.gms.common.GoogleApiAvailability
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import com.google.android.libraries.identity.googleid.GoogleIdTokenParsingException

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private lateinit var sessionStore: PlayerSessionStore
    private lateinit var credentialManager: CredentialManager
    private var currentPlayer: PlayerIdentity? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        sessionStore = PlayerSessionStore(this)
        credentialManager = CredentialManager.create(this)
        currentPlayer = sessionStore.loadCurrentPlayer()

        binding.gameView.listener = object : DerpyOwlGameView.Listener {
            override fun onScoreChanged(score: Int) {
                binding.scoreText.text = getString(R.string.score_format, score)
            }

            override fun onMilestoneUnlocked(milestone: Int) {
                binding.achievementText.text = getString(R.string.achievement_unlocked_format, milestone)
            }

            override fun onGameOver(score: Int, unlockedMilestones: List<Int>) {
                val activePlayer = currentPlayer ?: PlayerIdentity.devFallback()
                val scoreSummary = sessionStore.saveCompletedRun(activePlayer.id, score, unlockedMilestones)
                val achievementLine = if (unlockedMilestones.isEmpty()) {
                    formatAchievementStatus(scoreSummary.unlockedMilestones)
                } else {
                    getString(
                        R.string.achievement_summary_format,
                        unlockedMilestones.joinToString(),
                        formatAchievementStatus(scoreSummary.unlockedMilestones),
                    )
                }
                showOverlay(
                    title = getString(R.string.game_over_title),
                    message = getString(
                        R.string.game_over_message_format,
                        activePlayer.displayName,
                        score,
                        scoreSummary.bestScore,
                        scoreSummary.lastScore,
                        scoreSummary.runCount,
                        achievementLine,
                    ),
                    primaryLabel = getString(R.string.action_restart_flight),
                    secondaryLabel = getString(R.string.action_back_to_roost),
                    onPrimary = { startRun() },
                    onSecondary = { showStartScreen() },
                )
                binding.hintText.visibility = android.view.View.GONE
            }
        }

        binding.googleLoginButton.setOnClickListener { launchGoogleLogin() }
        binding.devLoginButton.setOnClickListener { activateDevFallback() }

        updatePlayerChrome()
        showStartScreen()
    }

    override fun onPause() {
        super.onPause()
        binding.gameView.resetPreview()
        if (binding.hudPanel.visibility == android.view.View.VISIBLE) {
            showStartScreen()
        }
    }

    private fun startRun() {
        val activePlayer = currentPlayer
        if (activePlayer == null) {
            Toast.makeText(this, getString(R.string.login_required_toast), Toast.LENGTH_SHORT).show()
            showStartScreen()
            return
        }
        val scoreSummary = sessionStore.getScoreSummary(activePlayer.id)
        binding.hudPanel.visibility = android.view.View.VISIBLE
        binding.overlayCard.visibility = android.view.View.GONE
        binding.hintText.visibility = android.view.View.VISIBLE
        binding.googleLoginButton.visibility = android.view.View.GONE
        binding.devLoginButton.visibility = android.view.View.GONE
        binding.scoreText.text = getString(R.string.score_zero)
        binding.achievementText.text = formatAchievementStatus(scoreSummary.unlockedMilestones)
        binding.gameView.setPlayerName(activePlayer.displayName)
        binding.gameView.startRun(scoreSummary.unlockedMilestones)
    }

    private fun showStartScreen() {
        binding.hudPanel.visibility = android.view.View.GONE
        binding.hintText.visibility = android.view.View.GONE
        binding.googleLoginButton.visibility = android.view.View.VISIBLE
        binding.devLoginButton.visibility = android.view.View.VISIBLE
        binding.gameView.resetPreview()
        showOverlay(
            title = getString(R.string.title_derpy_owl),
            message = buildStartMessage(),
            primaryLabel = getString(R.string.action_start_flight),
            secondaryLabel = getString(R.string.action_login_help),
            onPrimary = { startRun() },
            onSecondary = {
                showGoogleSetupRequirements(getString(R.string.google_setup_help_reason))
            },
        )
    }

    private fun showOverlay(
        title: String,
        message: String,
        primaryLabel: String,
        secondaryLabel: String,
        onPrimary: () -> Unit,
        onSecondary: () -> Unit,
    ) {
        binding.overlayCard.visibility = android.view.View.VISIBLE
        binding.overlayTitle.text = title
        binding.overlayMessage.text = message
        binding.primaryButton.text = primaryLabel
        binding.secondaryButton.text = secondaryLabel
        binding.primaryButton.setOnClickListener { onPrimary() }
        binding.secondaryButton.setOnClickListener { onSecondary() }
    }

    private fun activateDevFallback() {
        val devPlayer = PlayerIdentity.devFallback()
        setActivePlayer(devPlayer)
        Toast.makeText(this, getString(R.string.dev_login_toast), Toast.LENGTH_SHORT).show()
    }

    private fun launchGoogleLogin() {
        if (!isGoogleConfigured()) {
            showGoogleSetupRequirements(getString(R.string.google_setup_missing_client_id))
            return
        }
        if (!hasPlayServices()) {
            showGoogleSetupRequirements(getString(R.string.google_setup_missing_play_services))
            return
        }

        val request = GetCredentialRequest.Builder()
            .addCredentialOption(
                GetSignInWithGoogleOption.Builder(getString(R.string.google_web_client_id).trim()).build(),
            )
            .build()

        credentialManager.getCredentialAsync(
            context = this,
            request = request,
            cancellationSignal = null,
            executor = mainExecutor,
            callback = object : CredentialManagerCallback<GetCredentialResponse, GetCredentialException> {
                override fun onResult(result: GetCredentialResponse) {
                    handleGoogleCredentialResult(result)
                }

                override fun onError(e: GetCredentialException) {
                    showGoogleSetupRequirements(
                        getString(R.string.google_login_error_format, e.localizedMessage ?: e.javaClass.simpleName),
                    )
                }
            },
        )
    }

    private fun handleGoogleCredentialResult(result: GetCredentialResponse) {
        val credential = result.credential
        if (credential is CustomCredential &&
            credential.type == GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL
        ) {
            try {
                val googleCredential = GoogleIdTokenCredential.createFrom(credential.data)
                val displayName = googleCredential.displayName ?: googleCredential.id
                setActivePlayer(
                    PlayerIdentity(
                        id = googleCredential.id,
                        displayName = displayName,
                        provider = AuthProvider.GOOGLE,
                    ),
                )
                Toast.makeText(this, getString(R.string.google_login_success_toast, displayName), Toast.LENGTH_SHORT).show()
                return
            } catch (_: GoogleIdTokenParsingException) {
                showGoogleSetupRequirements(getString(R.string.google_setup_invalid_token))
                return
            }
        }

        showGoogleSetupRequirements(getString(R.string.google_setup_unexpected_credential))
    }

    private fun setActivePlayer(player: PlayerIdentity) {
        currentPlayer = player
        sessionStore.saveCurrentPlayer(player)
        binding.gameView.setPlayerName(player.displayName)
        updatePlayerChrome()
        showStartScreen()
    }

    private fun updatePlayerChrome() {
        val player = currentPlayer
        binding.subtitleText.text = if (player == null) {
            getString(R.string.subtitle_login_required)
        } else {
            getString(R.string.subtitle_logged_in_format, player.displayName, providerLabel(player.provider))
        }
    }

    private fun buildStartMessage(): String {
        val player = currentPlayer
        if (player == null) {
            return getString(R.string.start_message_needs_login, googleStatusLine())
        }

        val summary = sessionStore.getScoreSummary(player.id)
        val scoreLine = if (summary.runCount == 0) {
            getString(R.string.player_score_empty)
        } else {
            getString(
                R.string.player_score_summary_format,
                summary.bestScore,
                summary.lastScore,
                summary.runCount,
            )
        }
        val achievementLine = formatAchievementStatus(summary.unlockedMilestones)
        return getString(
            R.string.start_message_ready_format,
            player.displayName,
            providerLabel(player.provider),
            scoreLine,
            achievementLine,
            googleStatusLine(),
        )
    }

    private fun showGoogleSetupRequirements(reason: String) {
        showOverlay(
            title = getString(R.string.google_setup_title),
            message = getString(R.string.google_setup_message_format, reason),
            primaryLabel = getString(R.string.action_use_dev_fallback),
            secondaryLabel = getString(R.string.action_back_to_roost),
            onPrimary = { activateDevFallback() },
            onSecondary = { showStartScreen() },
        )
    }

    private fun isGoogleConfigured(): Boolean = getString(R.string.google_web_client_id).trim().isNotEmpty()

    private fun hasPlayServices(): Boolean =
        GoogleApiAvailability.getInstance().isGooglePlayServicesAvailable(this) == ConnectionResult.SUCCESS

    private fun googleStatusLine(): String = if (isGoogleConfigured()) {
        getString(R.string.google_status_ready)
    } else {
        getString(R.string.google_status_needs_setup)
    }

    private fun providerLabel(provider: AuthProvider): String = when (provider) {
        AuthProvider.GOOGLE -> getString(R.string.provider_google)
        AuthProvider.DEV_FALLBACK -> getString(R.string.provider_dev_fallback)
    }

    private fun formatAchievementStatus(unlockedMilestones: List<Int>): String = if (unlockedMilestones.isEmpty()) {
        getString(R.string.achievement_progress_hint)
    } else {
        getString(R.string.achievement_persisted_format, unlockedMilestones.joinToString())
    }
}
