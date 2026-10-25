package com.metallic.chiaki.design

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

object SessionHistory {
    fun read(context: Context): JSONArray = runCatching {
        JSONArray(context.getSharedPreferences("deckivo_sessions",Context.MODE_PRIVATE).getString("rows","[]"))
    }.getOrElse { JSONArray() }

    fun append(context: Context, started: Long, seconds: Long, profile: String) {
        val old=read(context);val rows=JSONArray()
        rows.put(JSONObject().put("started",started).put("seconds",seconds.coerceAtLeast(0)).put("profile",profile))
        for(i in 0 until minOf(old.length(),39)) rows.put(old.getJSONObject(i))
        context.getSharedPreferences("deckivo_sessions",Context.MODE_PRIVATE).edit().putString("rows",rows.toString()).apply()
    }
}
