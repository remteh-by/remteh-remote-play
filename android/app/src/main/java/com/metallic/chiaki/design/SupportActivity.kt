package com.metallic.chiaki.design

import android.content.Context
import android.content.Intent
import android.content.ClipData
import android.content.ClipboardManager
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.Toast
import com.google.android.material.dialog.MaterialAlertDialogBuilder
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
        val language = LanguagePicker.effective(this)
        val catalog = config.getJSONObject("texts")
        val copy = catalog.optJSONObject(language) ?: catalog.getJSONObject("en")
        val methods = config.getJSONArray("methods").let { rows -> (0 until rows.length()).map { rows.getJSONObject(it) } }
        if (methods.isNotEmpty()) {
            val choices = getSharedPreferences("deckivo_support_choices", Context.MODE_PRIVATE)
            var selected = methods.indexOfFirst { it.getString("id") == choices.getString("method", "kofi") }.coerceAtLeast(0)
            val panel = DeckivoUi.section(root, copy.getString("support_choose"))
            val picker = DeckivoUi.button(panel, methods[selected].getString("title") + " ▾") { }
            val cadence = DeckivoUi.label(panel, "", 14f)
            val readiness = DeckivoUi.label(panel, "", 14f)
            val destination = DeckivoUi.label(panel, "", 14f).apply {
                setTextIsSelectable(true)
                textDirection = View.TEXT_DIRECTION_LTR
            }
            fun current() = methods[selected]
            fun value() = current().optString("url").ifBlank { current().optString("address") }
            fun renderSelection() {
                val method = current()
                picker.text = method.getString("title") + " ▾"
                picker.contentDescription = copy.getString("support_choose") + ": " + method.getString("title")
                cadence.text = copy.getString("method_cadence_" + method.optString("cadence", "profile"))
                readiness.text = copy.getString("method_status_" + method.optString("status", "unverified"))
                destination.text = value()
            }
            picker.setOnClickListener {
                MaterialAlertDialogBuilder(this)
                    .setTitle(copy.getString("support_choose"))
                    .setSingleChoiceItems(methods.map { it.getString("title") }.toTypedArray(), selected) { dialog, index ->
                        if (index in methods.indices) {
                            selected = index
                            choices.edit().putString("method", current().getString("id")).apply()
                            renderSelection()
                        }
                        dialog.dismiss()
                    }.setNegativeButton(android.R.string.cancel, null).show()
            }
            DeckivoUi.button(panel, copy.getString("support_open_provider"), true) {
                if (current().optString("url").isNotBlank()) LinkUi.openLinkOrShowQr(this, value()) else LinkUi.showQr(this, value())
            }
            DeckivoUi.button(panel, copy.getString("support_copy_link")) {
                val clipboard = getSystemService(ClipboardManager::class.java)
                if (clipboard != null) {
                    clipboard.setPrimaryClip(ClipData.newPlainText(current().getString("title"), value()))
                    if (Build.VERSION.SDK_INT < 33) Toast.makeText(this, copy.getString("support_copied"), Toast.LENGTH_SHORT).show()
                } else Toast.makeText(this, copy.getString("support_copy_failed"), Toast.LENGTH_LONG).show()
            }
            DeckivoUi.button(panel, getString(R.string.dv_scan_phone)) { LinkUi.showQr(this, value()) }
            renderSelection()
        }
        DeckivoUi.label(root, copy.getString("support_provider_note"), 14f)
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
        DeckivoUi.label(root, getString(R.string.dv_support_note))
        DeckivoUi.button(root, getString(R.string.dv_licenses)) { startActivity(Intent(this, LicensesActivity::class.java)) }
        DeckivoUi.button(root, getString(R.string.dv_github_link)) { LinkUi.openLinkOrShowQr(this, LinkUi.GITHUB_URL) }
        DeckivoUi.button(root, getString(R.string.dv_remteh_link)) { LinkUi.openLinkOrShowQr(this, LinkUi.REMTEH_URL) }
    }
}
