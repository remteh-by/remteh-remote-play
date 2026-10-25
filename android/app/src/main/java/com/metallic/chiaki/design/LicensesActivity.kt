package com.metallic.chiaki.design

import android.os.Bundle
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import com.metallic.chiaki.BuildConfig
import com.metallic.chiaki.R
import org.json.JSONArray

/** All notices remain readable offline; the source link names the exact release. */
class LicensesActivity : DeckivoActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = DeckivoUi.screen(this, getString(R.string.dv_licenses), getString(R.string.dv_attribution))
        val source = "https://github.com/remteh-by/remteh-remote-play/releases/tag/v${BuildConfig.VERSION_NAME}"
        DeckivoUi.button(root, getString(R.string.dv_source_exact, source)) { LinkUi.openLinkOrShowQr(this, source) }
        val rows = JSONArray(assets.open("licenses/index.json").bufferedReader().use { it.readText() })
        for (i in 0 until rows.length()) {
            val row = rows.getJSONObject(i)
            DeckivoUi.button(root, row.getString("title")) {
                val text = TextView(this).apply {
                    this.text = assets.open("licenses/" + row.getString("file")).bufferedReader().use { it.readText() }
                    textSize = 14f
                    setPadding(24, 16, 24, 16)
                    setTextIsSelectable(true)
                }
                val scroll = ScrollView(this).apply { addView(text) }
                AlertDialog.Builder(this).setTitle(row.getString("title")).setView(scroll)
                    .setPositiveButton(android.R.string.ok, null).show()
            }
        }
        val supporters = SupportActivity.configuration(this).getJSONArray("supporters")
        if (supporters.length() > 0) {
            val section = DeckivoUi.section(root, getString(R.string.dv_supporters))
            for (i in 0 until supporters.length()) {
                val row = supporters.getJSONObject(i)
                DeckivoUi.label(section, getString(R.string.dv_supporter_format, row.getString("name"), row.getString("since")))
            }
        }
    }
}
