package com.metallic.chiaki.design

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.widget.LinearLayout
import android.widget.ProgressBar
import com.metallic.chiaki.R
import org.json.JSONObject

class SupportActivity : DeckivoActivity() {
    companion object {
        fun configuration(context: Context) = JSONObject(context.resources.openRawResource(R.raw.deckivo_support).bufferedReader().use { it.readText() })
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val config = configuration(this)
        val root = DeckivoUi.screen(this, getString(R.string.dv_support), getString(R.string.dv_support_body))
        val goals = DeckivoUi.section(root, getString(R.string.dv_support_goals))
        val goalStrings = mapOf("support_goal_mac" to R.string.dv_support_goal_mac,
            "support_goal_windows" to R.string.dv_support_goal_windows, "support_goal_hardware" to R.string.dv_support_goal_hardware)
        val rows = config.getJSONArray("goals")
        for (i in 0 until rows.length()) {
            val goal = rows.getJSONObject(i)
            goalStrings[goal.getString("title_key")]?.let { DeckivoUi.label(goals, getString(it)) }
            val target = goal.optDouble("target_usd", 0.0)
            if (target > 0 && !goal.isNull("target_usd") && !goal.isNull("raised_usd")) {
                val bar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
                    isIndeterminate = false
                    max = 100
                    progress = (goal.optDouble("raised_usd", 0.0) * 100 / target).toInt().coerceIn(0, 100)
                    contentDescription = getString(R.string.dv_support_goals)
                }
                goals.addView(bar, LinearLayout.LayoutParams(-1, DeckivoUi.dp(this, 12)))
                DeckivoUi.label(goals, getString(R.string.dv_goal_amount, goal.getDouble("raised_usd"), target), 14f)
            }
        }
        val methods = config.getJSONArray("methods")
        for (i in 0 until methods.length()) {
            val method = methods.getJSONObject(i)
            val panel = DeckivoUi.section(root, method.getString("title"))
            val value = method.optString("url").ifBlank { method.optString("address") }
            if (method.optBoolean("qr")) panel.addView(LinkUi.qrView(this, value), LinearLayout.LayoutParams(-1, DeckivoUi.dp(this, 280)))
            DeckivoUi.label(panel, value, 14f).setTextIsSelectable(true)
            if (method.optString("network").isNotBlank()) DeckivoUi.label(panel, method.getString("network"))
            DeckivoUi.button(panel, getString(R.string.dv_support_link), true) {
                if (method.optString("url").isNotBlank()) LinkUi.openLinkOrShowQr(this, value) else LinkUi.showQr(this, value)
            }
        }
        DeckivoUi.label(root, getString(R.string.dv_support_note))
        DeckivoUi.button(root, getString(R.string.dv_licenses)) { startActivity(Intent(this, LicensesActivity::class.java)) }
        DeckivoUi.button(root, getString(R.string.dv_github_link)) { LinkUi.openLinkOrShowQr(this, LinkUi.GITHUB_URL) }
        DeckivoUi.button(root, getString(R.string.dv_remteh_link)) { LinkUi.openLinkOrShowQr(this, LinkUi.REMTEH_URL) }
    }
}
