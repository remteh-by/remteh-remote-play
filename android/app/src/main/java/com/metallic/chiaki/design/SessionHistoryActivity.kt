package com.metallic.chiaki.design

import android.os.Bundle
import com.metallic.chiaki.R
import java.text.DateFormat
import java.util.Date
import java.util.Locale
import androidx.activity.result.contract.ActivityResultContracts
import java.io.File

class SessionHistoryActivity: DeckivoActivity() {
    private val export = registerForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri ->
        if (uri != null) runCatching {
            val output=contentResolver.openOutputStream(uri) ?: error("Could not open document")
            output.use { File(filesDir,"last-stream-diagnostics.json").inputStream().use { source -> source.copyTo(it) } }
        }.onFailure { android.widget.Toast.makeText(this,R.string.dv_diag_save_failed,android.widget.Toast.LENGTH_LONG).show() }
    }
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val content=DeckivoUi.screen(this,getString(R.string.dv_sessions),getString(R.string.dv_sessions_note))
        val rows=SessionHistory.read(this)
        if(File(filesDir,"last-stream-diagnostics.json").isFile) DeckivoUi.button(content,getString(R.string.dv_export_stream_diagnostics)) { export.launch("Deckivo-stream-diagnostics.json") }
        if(rows.length()==0) DeckivoUi.label(content,getString(R.string.dv_no_sessions),20f,true)
        for(i in 0 until rows.length()) {
            val row=rows.optJSONObject(i) ?: continue
            val panel=DeckivoUi.section(content,DateFormat.getDateTimeInstance(DateFormat.MEDIUM,DateFormat.SHORT).format(Date(row.optLong("started"))))
            val seconds=row.optLong("seconds")
            DeckivoUi.label(panel,String.format(Locale.ROOT,"%02d:%02d",seconds/60,seconds%60)+" · "+row.optString("profile"),18f,true)
        }
    }
}
