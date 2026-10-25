package com.metallic.chiaki.design

import androidx.core.content.edit
import android.content.Context
import android.content.Intent
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AlertDialog
import com.metallic.chiaki.R

object SupportNudges {
    private fun read(context: Context): SupportNudge {
        val p = context.getSharedPreferences("deckivo_support", Context.MODE_PRIVATE)
        return SupportNudge(p.getBoolean("eligible", false), p.getInt("shows", 0),
            p.getLong("next", 0), p.getBoolean("disabled", false))
    }
    private fun write(context: Context, state: SupportNudge) {
        context.getSharedPreferences("deckivo_support", Context.MODE_PRIVATE).edit { putBoolean("eligible", state.eligible); putInt("shows", state.shows); putLong("next", state.nextAt); putBoolean("disabled", state.disabled) }
    }
    fun complete(context: Context, seconds: Long, clean: Boolean) =
        write(context, SupportPolicy.complete(read(context), seconds, clean))

    fun showIfDue(activity: AppCompatActivity) {
        val state = read(activity)
        if (!SupportPolicy.due(state, System.currentTimeMillis()) || activity.isFinishing) return
        val methods = SupportActivity.configuration(activity).getJSONArray("methods")
        if (methods.length() == 0) return
        val method = methods.getJSONObject(0)
        val value = method.optString("url").ifBlank { method.optString("address") }
        write(activity, SupportPolicy.shown(state))
        AlertDialog.Builder(activity).setTitle(R.string.dv_thanks_title)
            .setMessage(R.string.dv_thanks_body).setView(LinkUi.qrView(activity, value))
            .setPositiveButton(R.string.dv_support_link) { _, _ ->
                write(activity, read(activity).copy(disabled = true))
                activity.startActivity(Intent(activity, SupportActivity::class.java))
            }
            .setNegativeButton(R.string.dv_thanks_later) { _, _ -> write(activity, SupportPolicy.later(read(activity), System.currentTimeMillis())) }
            .setNeutralButton(R.string.dv_thanks_never) { _, _ -> write(activity, read(activity).copy(disabled = true)) }
            .setOnCancelListener { write(activity, SupportPolicy.later(read(activity), System.currentTimeMillis())) }.show()
    }
}
