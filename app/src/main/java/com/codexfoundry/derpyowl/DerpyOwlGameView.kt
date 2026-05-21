package com.codexfoundry.derpyowl

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Shader
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
        fun onGameOver(score: Int, unlockedMilestones: List<Int>)
    }

    private data class Obstacle(
        var x: Float,
        val gapCenterY: Float,
        val gapHeight: Float,
    )

    var listener: Listener? = null

    private val random = Random(SystemClock.elapsedRealtime())
    private val unlockedMilestones = mutableSetOf<Int>()

    private val skyPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_sky)
    }
    private val mountainPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_mountain)
    }
    private val hillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_hill)
    }
    private val cloudPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
    }
    private val cloudShadePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_cloud_shadow)
    }
    private val treePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_tree)
    }
    private val treeShadowPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_tree_dark)
    }
    private val trunkPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_trunk)
    }
    private val owlPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_body)
    }
    private val owlBellyPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.owl_belly)
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

    fun startRun(existingUnlockedMilestones: Collection<Int>) {
        resetWorld()
        unlockedMilestones.clear()
        unlockedMilestones.addAll(existingUnlockedMilestones)
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
        if (w > 0 && h > 0) {
            skyPaint.shader = LinearGradient(
                0f,
                0f,
                0f,
                h.toFloat(),
                ContextCompat.getColor(context, R.color.owl_sky_top),
                ContextCompat.getColor(context, R.color.owl_sky_bottom),
                Shader.TileMode.CLAMP,
            )
        }
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
        val newlyUnlocked = ScoreAchievements.newlyUnlocked(currentScore, unlockedMilestones)
        newlyUnlocked.forEach { milestone ->
            unlockedMilestones += milestone
            listener?.onMilestoneUnlocked(milestone)
        }
        if (newlyUnlocked.isNotEmpty()) {
            latestRunUnlocked = newlyUnlocked
        }
    }

    private fun finishRun() {
        isRunning = false
        listener?.onGameOver(score, latestRunUnlocked)
    }

    private fun hitBounds(): Boolean {
        val radius = owlCollisionRadius()
        return owlY - radius < 0f || owlY + radius > height
    }

    private fun hitObstacle(): Boolean {
        val collisionRadius = owlCollisionRadius()
        val owlRect = RectF(
            owlX - collisionRadius,
            owlY - collisionRadius,
            owlX + collisionRadius,
            owlY + collisionRadius,
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
        drawMountains(canvas)
        drawRollingHills(canvas)
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
            width * 0.15f - (elapsed * 22f % (width + 180f)),
            width * 0.62f - (elapsed * 14f % (width + 220f)),
        )
        val cloudY = listOf(height * 0.18f, height * 0.3f)
        offsets.forEachIndexed { index, startX ->
            drawCloud(canvas, startX, cloudY[index], 1f + index * 0.12f)
            drawCloud(canvas, startX + width + 220f, cloudY[index], 1f + index * 0.12f)
        }
    }

    private fun drawMountains(canvas: Canvas) {
        val ridge = Path().apply {
            moveTo(0f, height * 0.62f)
            lineTo(width * 0.12f, height * 0.48f)
            lineTo(width * 0.26f, height * 0.62f)
            lineTo(width * 0.44f, height * 0.4f)
            lineTo(width * 0.63f, height * 0.62f)
            lineTo(width * 0.82f, height * 0.46f)
            lineTo(width.toFloat(), height * 0.62f)
            lineTo(width.toFloat(), height.toFloat())
            lineTo(0f, height.toFloat())
            close()
        }
        canvas.drawPath(ridge, mountainPaint)
    }

    private fun drawRollingHills(canvas: Canvas) {
        val hill = Path().apply {
            moveTo(0f, height * 0.78f)
            cubicTo(
                width * 0.12f,
                height * 0.68f,
                width * 0.3f,
                height * 0.74f,
                width * 0.42f,
                height * 0.7f,
            )
            cubicTo(
                width * 0.58f,
                height * 0.64f,
                width * 0.78f,
                height * 0.76f,
                width.toFloat(),
                height * 0.68f,
            )
            lineTo(width.toFloat(), height.toFloat())
            lineTo(0f, height.toFloat())
            close()
        }
        canvas.drawPath(hill, hillPaint)
    }

    private fun drawCloud(canvas: Canvas, x: Float, y: Float, scale: Float) {
        val radius = 34f * scale
        canvas.drawCircle(x, y, radius, cloudPaint)
        canvas.drawCircle(x + radius * 0.9f, y - radius * 0.18f, radius * 0.88f, cloudPaint)
        canvas.drawCircle(x + radius * 1.8f, y, radius * 0.72f, cloudPaint)
        canvas.drawRoundRect(
            x,
            y - radius * 0.12f,
            x + radius * 1.8f,
            y + radius * 0.7f,
            radius * 0.35f,
            radius * 0.35f,
            cloudShadePaint,
        )
    }

    private fun drawObstacles(canvas: Canvas) {
        val obstacleWidth = obstacleWidth()
        for (obstacle in obstacles) {
            val gapTop = obstacle.gapCenterY - obstacle.gapHeight / 2f
            val gapBottom = obstacle.gapCenterY + obstacle.gapHeight / 2f

            drawStormCloudObstacle(canvas, obstacle.x, obstacle.x + obstacleWidth, gapTop)
            drawForestObstacle(canvas, obstacle.x, obstacle.x + obstacleWidth, gapBottom, height.toFloat())
        }
    }

    private fun drawStormCloudObstacle(canvas: Canvas, left: Float, right: Float, bottom: Float) {
        if (bottom <= 0f) {
            return
        }
        canvas.drawRect(left, 0f, right, bottom, cloudShadePaint)
        val widthSpan = right - left
        val clusterRadius = widthSpan * 0.22f
        val clusterCenters = listOf(
            left + widthSpan * 0.12f,
            left + widthSpan * 0.4f,
            left + widthSpan * 0.68f,
            left + widthSpan * 0.9f,
        )
        clusterCenters.forEachIndexed { index, centerX ->
            val centerY = bottom - clusterRadius * (0.7f + (index % 2) * 0.18f)
            canvas.drawCircle(centerX, centerY, clusterRadius, cloudPaint)
            canvas.drawCircle(centerX - clusterRadius * 0.45f, centerY + clusterRadius * 0.15f, clusterRadius * 0.78f, cloudPaint)
            canvas.drawCircle(centerX + clusterRadius * 0.42f, centerY + clusterRadius * 0.1f, clusterRadius * 0.72f, cloudPaint)
        }
    }

    private fun drawForestObstacle(canvas: Canvas, left: Float, right: Float, top: Float, bottom: Float) {
        if (top >= bottom) {
            return
        }
        canvas.drawRect(left, top, right, bottom, treeShadowPaint)
        val widthSpan = right - left
        val pineCount = 3
        for (index in 0 until pineCount) {
            val centerX = left + widthSpan * (0.2f + index * 0.3f)
            val treeWidth = widthSpan * 0.28f
            val treeTop = top + (bottom - top) * (0.08f + (index % 2) * 0.1f)
            val canopy = Path().apply {
                moveTo(centerX, treeTop)
                lineTo(centerX - treeWidth * 0.55f, bottom - (bottom - top) * 0.18f)
                lineTo(centerX - treeWidth * 0.14f, bottom - (bottom - top) * 0.18f)
                lineTo(centerX - treeWidth * 0.62f, bottom - (bottom - top) * 0.04f)
                lineTo(centerX, bottom - (bottom - top) * 0.42f)
                lineTo(centerX + treeWidth * 0.62f, bottom - (bottom - top) * 0.04f)
                lineTo(centerX + treeWidth * 0.14f, bottom - (bottom - top) * 0.18f)
                lineTo(centerX + treeWidth * 0.55f, bottom - (bottom - top) * 0.18f)
                close()
            }
            canvas.drawPath(canopy, treePaint)
            canvas.drawRect(
                centerX - treeWidth * 0.08f,
                bottom - (bottom - top) * 0.22f,
                centerX + treeWidth * 0.08f,
                bottom,
                trunkPaint,
            )
        }
    }

    private fun drawOwl(canvas: Canvas) {
        val radius = owlRadius()
        val wingFlare = min(max(-owlVelocity / 720f, -0.4f), 1f)
        val bodyRect = RectF(
            owlX - radius * 0.72f,
            owlY - radius * 0.54f,
            owlX + radius * 0.72f,
            owlY + radius * 0.68f,
        )
        val bellyRect = RectF(
            owlX - radius * 0.38f,
            owlY - radius * 0.1f,
            owlX + radius * 0.42f,
            owlY + radius * 0.62f,
        )

        drawWing(canvas, owlX - radius * 0.25f, owlY - radius * 0.02f, radius, -(52f + wingFlare * 22f), true)
        drawWing(canvas, owlX + radius * 0.25f, owlY - radius * 0.02f, radius, 52f + wingFlare * 22f, false)

        canvas.drawOval(bodyRect, owlPaint)
        canvas.drawOval(bellyRect, owlBellyPaint)
        canvas.drawCircle(owlX, owlY - radius * 0.36f, radius * 0.52f, owlPaint)

        val leftEar = Path().apply {
            moveTo(owlX - radius * 0.38f, owlY - radius * 0.54f)
            lineTo(owlX - radius * 0.16f, owlY - radius * 1.02f)
            lineTo(owlX - radius * 0.02f, owlY - radius * 0.48f)
            close()
        }
        val rightEar = Path().apply {
            moveTo(owlX + radius * 0.02f, owlY - radius * 0.48f)
            lineTo(owlX + radius * 0.18f, owlY - radius * 1.02f)
            lineTo(owlX + radius * 0.4f, owlY - radius * 0.54f)
            close()
        }
        canvas.drawPath(leftEar, owlPaint)
        canvas.drawPath(rightEar, owlPaint)

        val tail = Path().apply {
            moveTo(owlX - radius * 0.18f, owlY + radius * 0.52f)
            lineTo(owlX - radius * 0.44f, owlY + radius * 0.98f)
            lineTo(owlX + radius * 0.12f, owlY + radius * 0.72f)
            close()
        }
        canvas.drawPath(tail, owlWingPaint)

        canvas.drawCircle(owlX - radius * 0.2f, owlY - radius * 0.38f, radius * 0.16f, owlEyePaint)
        canvas.drawCircle(owlX + radius * 0.2f, owlY - radius * 0.38f, radius * 0.16f, owlEyePaint)
        canvas.drawCircle(owlX - radius * 0.18f, owlY - radius * 0.36f, radius * 0.06f, owlPupilPaint)
        canvas.drawCircle(owlX + radius * 0.22f, owlY - radius * 0.36f, radius * 0.06f, owlPupilPaint)

        val beak = Path().apply {
            moveTo(owlX + radius * 0.02f, owlY - radius * 0.18f)
            lineTo(owlX + radius * 0.48f, owlY - radius * 0.02f)
            lineTo(owlX + radius * 0.04f, owlY + radius * 0.12f)
            close()
        }
        canvas.drawPath(beak, owlBeakPaint)
    }

    private fun owlRadius(): Float = max(width, height) * 0.04f

    private fun owlCollisionRadius(): Float = owlRadius() * 0.72f

    private fun obstacleWidth(): Float = max(width * 0.13f, 96f)

    private fun drawWing(
        canvas: Canvas,
        pivotX: Float,
        pivotY: Float,
        radius: Float,
        rotation: Float,
        leftSide: Boolean,
    ) {
        canvas.save()
        canvas.rotate(rotation, pivotX, pivotY)
        val wingRect = if (leftSide) {
            RectF(
                pivotX - radius * 1.02f,
                pivotY - radius * 0.24f,
                pivotX + radius * 0.14f,
                pivotY + radius * 0.72f,
            )
        } else {
            RectF(
                pivotX - radius * 0.14f,
                pivotY - radius * 0.24f,
                pivotX + radius * 1.02f,
                pivotY + radius * 0.72f,
            )
        }
        canvas.drawOval(wingRect, owlWingPaint)
        canvas.restore()
    }
}
