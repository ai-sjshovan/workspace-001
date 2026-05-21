package com.codexfoundry.derpyowl

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.os.SystemClock
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import androidx.core.content.ContextCompat
import kotlin.math.max
import kotlin.math.min
import kotlin.random.Random

class DerpyOwlGameView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    private companion object {
        const val FLAP_IMPULSE = -460f
        const val STARTING_GRAVITY = 780f
        const val MAX_GRAVITY = 920f
        const val STARTING_OBSTACLE_SPEED = 235f
        const val MAX_OBSTACLE_SPEED = 355f
        const val STARTING_SPAWN_INTERVAL = 2.05f
        const val MIN_SPAWN_INTERVAL = 1.5f
        const val BASE_GAP_HEIGHT_RATIO = 0.35f
        const val MIN_GAP_HEIGHT_RATIO = 0.28f
        const val DIFFICULTY_CAP_SECONDS = 40f
        const val MAX_FRAME_DELTA_SECONDS = 0.032f
        const val OFFSCREEN_OBSTACLE_THRESHOLD = -200f
        const val OBSTACLE_SPAWN_PADDING = 140f
        const val INITIAL_OWL_X_RATIO = 0.28f
        const val INITIAL_OWL_Y_RATIO = 0.45f
        const val MIN_INITIAL_OWL_Y = 180f
        const val INITIAL_OBSTACLE_SPACING_RATIO = 0.68f
    }

    interface Listener {
        fun onScoreChanged(score: Int)
        fun onMilestoneUnlocked(milestone: Int)
        fun onGameOver(score: Int, bestScore: Int, unlockedMilestones: List<Int>)
    }

    private data class Obstacle(
        var x: Float,
        val gapCenterY: Float,
        val gapHeight: Float,
    )

    var listener: Listener? = null

    private val random = Random(SystemClock.elapsedRealtime())
    private val prefs = context.getSharedPreferences("derpy_owl_state", Context.MODE_PRIVATE)
    private val milestoneTargets = listOf(10, 25, 50, 100)
    private val unlockedMilestones = milestoneTargets
        .filter { prefs.getBoolean("milestone_$it", false) }
        .toMutableSet()

    private val skyPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_sky)
    }
    private val cloudPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
    }
    private val cloudShadePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(110, 223, 236, 245)
    }
    private val treePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_tree)
    }
    private val trunkPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_trunk)
    }
    private val owlPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_body)
    }
    private val owlWingPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_wing)
    }
    private val owlEyePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
    }
    private val owlPupilPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_night)
    }
    private val owlBeakPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_beak)
    }
    private val sunPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_sun)
    }

    private val obstacles = mutableListOf<Obstacle>()
    private var isRunning = false
    private var score = 0
    private var owlX = 0f
    private var owlY = 0f
    private var owlVelocity = 0f
    private var lastFrameMillis = 0L
    private var obstacleSpawnAccumulator = 0f
    private var scoreAccumulator = 0f
    private var playerName = "Guest Pilot"
    private var latestRunUnlocked = emptyList<Int>()

    fun setPlayerName(name: String) {
        playerName = name
    }

    fun getPlayerName(): String = playerName

    fun startRun() {
        resetWorld()
        isRunning = true
        lastFrameMillis = SystemClock.elapsedRealtime()
        listener?.onScoreChanged(score)
        postInvalidateOnAnimation()
    }

    fun resetPreview() {
        isRunning = false
        resetWorld()
        invalidate()
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        resetWorld()
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (!isRunning) {
            return false
        }
        if (event.action == MotionEvent.ACTION_DOWN) {
            owlVelocity = FLAP_IMPULSE
            return true
        }
        return super.onTouchEvent(event)
    }

    override fun onDetachedFromWindow() {
        super.onDetachedFromWindow()
        isRunning = false
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        drawScene(canvas)
        if (!isRunning) {
            return
        }

        val frameMillis = SystemClock.elapsedRealtime()
        val deltaSeconds = min((frameMillis - lastFrameMillis) / 1000f, MAX_FRAME_DELTA_SECONDS)
        lastFrameMillis = frameMillis

        updateWorld(deltaSeconds)

        if (isRunning) {
            postInvalidateOnAnimation()
        }
    }

    private fun resetWorld() {
        score = 0
        latestRunUnlocked = emptyList()
        obstacleSpawnAccumulator = 0f
        scoreAccumulator = 0f
        obstacles.clear()
        owlX = width * INITIAL_OWL_X_RATIO
        owlY = max(height * INITIAL_OWL_Y_RATIO, MIN_INITIAL_OWL_Y)
        owlVelocity = 0f
        if (width > 0 && height > 0) {
            repeat(3) { index ->
                spawnObstacle(width + index * width * INITIAL_OBSTACLE_SPACING_RATIO)
            }
        }
    }

    private fun updateWorld(deltaSeconds: Float) {
        scoreAccumulator += deltaSeconds
        while (scoreAccumulator >= 1f) {
            scoreAccumulator -= 1f
            score += 1
            listener?.onScoreChanged(score)
            unlockMilestones(score)
        }

        val difficulty = min(score / DIFFICULTY_CAP_SECONDS, 1f)
        val gravity = STARTING_GRAVITY + (difficulty * (MAX_GRAVITY - STARTING_GRAVITY))
        val obstacleSpeed = STARTING_OBSTACLE_SPEED + (difficulty * (MAX_OBSTACLE_SPEED - STARTING_OBSTACLE_SPEED))
        val spawnEverySeconds =
            STARTING_SPAWN_INTERVAL - (difficulty * (STARTING_SPAWN_INTERVAL - MIN_SPAWN_INTERVAL))

        owlVelocity += gravity * deltaSeconds
        owlY += owlVelocity * deltaSeconds

        obstacleSpawnAccumulator += deltaSeconds
        while (obstacleSpawnAccumulator >= spawnEverySeconds) {
            obstacleSpawnAccumulator -= spawnEverySeconds
            spawnObstacle(width.toFloat() + OBSTACLE_SPAWN_PADDING, difficulty)
        }

        val iterator = obstacles.iterator()
        while (iterator.hasNext()) {
            val obstacle = iterator.next()
            obstacle.x -= obstacleSpeed * deltaSeconds
            if (obstacle.x < OFFSCREEN_OBSTACLE_THRESHOLD) {
                iterator.remove()
            }
        }

        if (hitBounds() || hitObstacle()) {
            finishRun()
        }
    }

    private fun unlockMilestones(currentScore: Int) {
        val newlyUnlocked = mutableListOf<Int>()
        for (milestone in milestoneTargets) {
            if (currentScore >= milestone && unlockedMilestones.add(milestone)) {
                prefs.edit().putBoolean("milestone_$milestone", true).apply()
                newlyUnlocked += milestone
                listener?.onMilestoneUnlocked(milestone)
            }
        }
        if (newlyUnlocked.isNotEmpty()) {
            latestRunUnlocked = newlyUnlocked
        }
    }

    private fun finishRun() {
        isRunning = false
        val bestScore = max(score, prefs.getInt("best_score", 0))
        prefs.edit().putInt("best_score", bestScore).apply()
        listener?.onGameOver(score, bestScore, latestRunUnlocked)
    }

    private fun hitBounds(): Boolean {
        val radius = owlRadius()
        return owlY - radius < 0f || owlY + radius > height
    }

    private fun hitObstacle(): Boolean {
        val owlRect = RectF(
            owlX - owlRadius(),
            owlY - owlRadius(),
            owlX + owlRadius(),
            owlY + owlRadius(),
        )
        val obstacleWidth = obstacleWidth()
        for (obstacle in obstacles) {
            val gapTop = obstacle.gapCenterY - obstacle.gapHeight / 2f
            val gapBottom = obstacle.gapCenterY + obstacle.gapHeight / 2f

            val topRect = RectF(obstacle.x, 0f, obstacle.x + obstacleWidth, gapTop)
            val bottomRect = RectF(obstacle.x, gapBottom, obstacle.x + obstacleWidth, height.toFloat())

            if (RectF.intersects(owlRect, topRect) || RectF.intersects(owlRect, bottomRect)) {
                return true
            }
        }
        return false
    }

    private fun spawnObstacle(initialX: Float, difficulty: Float = 0f) {
        if (width == 0 || height == 0) {
            return
        }
        val gapRatio = BASE_GAP_HEIGHT_RATIO - (difficulty * (BASE_GAP_HEIGHT_RATIO - MIN_GAP_HEIGHT_RATIO))
        val gapHeight = height * gapRatio
        val gapHalf = gapHeight / 2f
        val safeTop = height * 0.18f + gapHalf
        val safeBottom = height * 0.82f - gapHalf
        val center = random.nextFloat() * (safeBottom - safeTop) + safeTop
        obstacles += Obstacle(initialX, center, gapHeight)
    }

    private fun drawScene(canvas: Canvas) {
        canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), skyPaint)
        drawSun(canvas)
        drawParallaxClouds(canvas)
        drawObstacles(canvas)
        drawOwl(canvas)
    }

    private fun drawSun(canvas: Canvas) {
        canvas.drawCircle(width * 0.82f, height * 0.16f, width * 0.08f, sunPaint)
    }

    private fun drawParallaxClouds(canvas: Canvas) {
        val elapsed = if (isRunning) score.toFloat() else 0f
        val offsets = listOf(
            width * 0.15f - (elapsed * 18f % (width + 180f)),
            width * 0.62f - (elapsed * 11f % (width + 220f)),
        )
        val cloudY = listOf(height * 0.18f, height * 0.3f)
        offsets.forEachIndexed { index, startX ->
            drawCloud(canvas, startX, cloudY[index], 1f + index * 0.12f)
            drawCloud(canvas, startX + width + 220f, cloudY[index], 1f + index * 0.12f)
        }
    }

    private fun drawCloud(canvas: Canvas, x: Float, y: Float, scale: Float) {
        val radius = 34f * scale
        canvas.drawCircle(x, y, radius, cloudPaint)
        canvas.drawCircle(x + radius * 0.9f, y - radius * 0.18f, radius * 0.88f, cloudPaint)
        canvas.drawCircle(x + radius * 1.8f, y, radius * 0.72f, cloudPaint)
        canvas.drawRect(x, y, x + radius * 1.8f, y + radius * 0.7f, cloudShadePaint)
    }

    private fun drawObstacles(canvas: Canvas) {
        val obstacleWidth = obstacleWidth()
        for (obstacle in obstacles) {
            val gapTop = obstacle.gapCenterY - obstacle.gapHeight / 2f
            val gapBottom = obstacle.gapCenterY + obstacle.gapHeight / 2f

            canvas.drawRect(obstacle.x, 0f, obstacle.x + obstacleWidth, gapTop, cloudPaint)
            canvas.drawRect(obstacle.x, gapBottom, obstacle.x + obstacleWidth, height.toFloat(), treePaint)
            canvas.drawRect(
                obstacle.x + obstacleWidth * 0.3f,
                gapBottom,
                obstacle.x + obstacleWidth * 0.7f,
                min(height.toFloat(), gapBottom + height * 0.18f),
                trunkPaint,
            )
        }
    }

    private fun drawOwl(canvas: Canvas) {
        val radius = owlRadius()
        canvas.drawCircle(owlX, owlY, radius, owlPaint)
        canvas.drawCircle(owlX - radius * 0.24f, owlY - radius * 0.12f, radius * 0.2f, owlEyePaint)
        canvas.drawCircle(owlX + radius * 0.16f, owlY - radius * 0.12f, radius * 0.2f, owlEyePaint)
        canvas.drawCircle(owlX - radius * 0.22f, owlY - radius * 0.12f, radius * 0.08f, owlPupilPaint)
        canvas.drawCircle(owlX + radius * 0.18f, owlY - radius * 0.12f, radius * 0.08f, owlPupilPaint)

        val wingFlare = min(max(-owlVelocity / 700f, -0.5f), 1f)
        canvas.drawOval(
            owlX - radius * 1.08f,
            owlY - radius * 0.25f - (wingFlare * 16f),
            owlX - radius * 0.1f,
            owlY + radius * 0.65f,
            owlWingPaint,
        )
        canvas.drawOval(
            owlX + radius * 0.05f,
            owlY - radius * 0.15f + (wingFlare * 10f),
            owlX + radius * 1.05f,
            owlY + radius * 0.7f,
            owlWingPaint,
        )

        val beak = floatArrayOf(
            owlX + radius * 0.1f, owlY + radius * 0.05f,
            owlX + radius * 0.55f, owlY + radius * 0.18f,
            owlX + radius * 0.12f, owlY + radius * 0.38f,
        )
        canvas.drawVertices(
            Canvas.VertexMode.TRIANGLES,
            beak.size,
            beak,
            0,
            null,
            0,
            null,
            0,
            null,
            0,
            0,
            owlBeakPaint,
        )
    }

    private fun owlRadius(): Float = max(width, height) * 0.04f

    private fun obstacleWidth(): Float = max(width * 0.13f, 96f)
}
