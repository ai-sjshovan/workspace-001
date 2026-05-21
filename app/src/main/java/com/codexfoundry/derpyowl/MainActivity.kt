package com.codexfoundry.derpyowl

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.codexfoundry.derpyowl.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private var currentPlayerName = "Guest Pilot"

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.gameView.listener = object : DerpyOwlGameView.Listener {
            override fun onScoreChanged(score: Int) {
                binding.scoreText.text = getString(R.string.score_format, score)
            }

            override fun onMilestoneUnlocked(milestone: Int) {
                binding.achievementText.text = getString(R.string.achievement_unlocked_format, milestone)
            }

            override fun onGameOver(score: Int, bestScore: Int, unlockedMilestones: List<Int>) {
                val achievementLine = if (unlockedMilestones.isEmpty()) {
                    getString(R.string.achievement_progress_hint)
                } else {
                    getString(R.string.achievement_summary_format, unlockedMilestones.joinToString())
                }
                showOverlay(
                    title = getString(R.string.game_over_title),
                    message = getString(
                        R.string.game_over_message_format,
                        currentPlayerName,
                        score,
                        bestScore,
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

        binding.loginButton.setOnClickListener {
            currentPlayerName = "Local Nest Tester"
            binding.gameView.setPlayerName(currentPlayerName)
            binding.subtitleText.text = getString(R.string.subtitle_logged_in_format, currentPlayerName)
            Toast.makeText(
                this,
                getString(R.string.dev_login_toast),
                Toast.LENGTH_SHORT,
            ).show()
        }

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
        binding.hudPanel.visibility = android.view.View.VISIBLE
        binding.overlayCard.visibility = android.view.View.GONE
        binding.hintText.visibility = android.view.View.VISIBLE
        binding.loginButton.visibility = android.view.View.GONE
        binding.scoreText.text = getString(R.string.score_zero)
        binding.achievementText.text = getString(R.string.achievement_progress_hint)
        binding.gameView.setPlayerName(currentPlayerName)
        binding.gameView.startRun()
    }

    private fun showStartScreen() {
        binding.hudPanel.visibility = android.view.View.GONE
        binding.hintText.visibility = android.view.View.GONE
        binding.loginButton.visibility = android.view.View.VISIBLE
        binding.gameView.resetPreview()
        showOverlay(
            title = getString(R.string.title_derpy_owl),
            message = getString(R.string.start_message),
            primaryLabel = getString(R.string.action_start_flight),
            secondaryLabel = getString(R.string.action_practice_reset),
            onPrimary = { startRun() },
            onSecondary = {
                binding.gameView.resetPreview()
                Toast.makeText(this, getString(R.string.practice_reset_toast), Toast.LENGTH_SHORT).show()
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
}
