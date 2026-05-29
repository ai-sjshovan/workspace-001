package com.corelink.wear

import androidx.wear.protolayout.TimelineBuilders
import androidx.wear.protolayout.ColorBuilders.argb
import androidx.wear.protolayout.DimensionBuilders.dp
import androidx.wear.protolayout.DimensionBuilders.expand
import androidx.wear.protolayout.DimensionBuilders.sp
import androidx.wear.protolayout.LayoutElementBuilders
import androidx.wear.protolayout.LayoutElementBuilders.FONT_WEIGHT_BOLD
import androidx.wear.protolayout.ModifiersBuilders
import androidx.wear.tiles.RequestBuilders
import androidx.wear.tiles.ResourceBuilders
import androidx.wear.tiles.TileBuilders
import androidx.wear.tiles.TileService
import com.google.common.util.concurrent.Futures
import com.google.common.util.concurrent.ListenableFuture

private const val StatusTileResourcesVersion = "core_link_status_tile_v1"

class CoreLinkStatusTileService : TileService() {
    override fun onTileRequest(
        requestParams: RequestBuilders.TileRequest,
    ): ListenableFuture<TileBuilders.Tile> {
        val state = CoreLinkPrefs.load(applicationContext)
        val timeline = TimelineBuilders.Timeline.Builder()
            .addTimelineEntry(
                TimelineBuilders.TimelineEntry.Builder()
                    .setLayout(
                        LayoutElementBuilders.Layout.Builder()
                            .setRoot(statusRoot(state))
                            .build(),
                    )
                    .build(),
            )
            .build()

        val tile = TileBuilders.Tile.Builder()
            .setResourcesVersion(StatusTileResourcesVersion)
            .setFreshnessIntervalMillis(60_000)
            .setTileTimeline(timeline)
            .build()

        return Futures.immediateFuture(tile)
    }

    override fun onResourcesRequest(
        requestParams: RequestBuilders.ResourcesRequest,
    ): ListenableFuture<ResourceBuilders.Resources> =
        Futures.immediateFuture(
            ResourceBuilders.Resources.Builder()
                .setVersion(StatusTileResourcesVersion)
                .build(),
        )

    private fun statusRoot(state: CoreLinkState): LayoutElementBuilders.LayoutElement {
        val summary = watchStatusSummary(state, System.currentTimeMillis()).replace('\n', ' ')
        return LayoutElementBuilders.Box.Builder()
            .setWidth(expand())
            .setHeight(expand())
            .setModifiers(
                ModifiersBuilders.Modifiers.Builder()
                    .setPadding(
                        ModifiersBuilders.Padding.Builder()
                            .setStart(dp(14f))
                            .setTop(dp(14f))
                            .setEnd(dp(14f))
                            .setBottom(dp(14f))
                            .build(),
                    )
                    .build(),
            )
            .addContent(
                LayoutElementBuilders.Column.Builder()
                    .setWidth(expand())
                    .addContent(tileText("CORE LINK", 15f, 0xFFB7F6FF.toInt(), bold = true))
                    .addContent(tileSpacer(6f))
                    .addContent(tileText(state.activeCore?.designation ?: "NO CORE", 13f, 0xFFFFFFFF.toInt(), bold = true))
                    .addContent(tileSpacer(4f))
                    .addContent(tileText(summary, 11f, 0xFF89D6FF.toInt()))
                    .build(),
            )
            .build()
    }

    private fun tileText(
        text: String,
        sizeSp: Float,
        color: Int,
        bold: Boolean = false,
    ): LayoutElementBuilders.Text =
        LayoutElementBuilders.Text.Builder()
            .setText(text)
            .setFontStyle(
                LayoutElementBuilders.FontStyle.Builder()
                    .setColor(argb(color))
                    .setSize(sp(sizeSp))
                    .setWeight(if (bold) FONT_WEIGHT_BOLD else LayoutElementBuilders.FONT_WEIGHT_NORMAL)
                    .build(),
            )
            .setMaxLines(3)
            .build()

    private fun tileSpacer(heightDp: Float): LayoutElementBuilders.Spacer =
        LayoutElementBuilders.Spacer.Builder()
            .setHeight(dp(heightDp))
            .build()
}
