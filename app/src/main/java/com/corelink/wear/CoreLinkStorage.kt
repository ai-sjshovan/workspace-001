package com.corelink.wear

import android.content.Context

object CoreLinkPrefs {
    private const val Name = "corelink_state"

    fun load(context: Context): CoreLinkState {
        val prefs = context.getSharedPreferences(Name, Context.MODE_PRIVATE)
        val values = prefs.all.mapValues { (_, value) -> value?.toString().orEmpty() }
        return CoreLinkStateCodec.decode(values)
    }

    fun save(context: Context, state: CoreLinkState) {
        val values = CoreLinkStateCodec.encode(state)
        context.getSharedPreferences(Name, Context.MODE_PRIVATE).edit().clear().apply {
            values.forEach { (key, value) -> putString(key, value) }
        }.apply()
    }
}
