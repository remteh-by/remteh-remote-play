package com.metallic.chiaki.updates

import androidx.core.content.edit
import android.app.Activity
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageInstaller
import android.os.Build
import androidx.appcompat.app.AlertDialog
import androidx.annotation.RequiresApi
import com.metallic.chiaki.R
import com.metallic.chiaki.main.MainActivity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.util.UUID

/** Uses Android's self-update API, and always honours requests for user consent. */
object SelfUpdateInstaller {
    private const val RESULT = "by.remteh.remoteplay.UPDATE_RESULT"
    private const val NONCE = "deckivo_install_nonce"

    fun pending(activity: Activity): Boolean {
        val id = UpdateRepository.prefs(activity).getInt("install_session", -1)
        return id >= 0 && activity.packageManager.packageInstaller.getSessionInfo(id) != null
    }

    @RequiresApi(31)
    suspend fun install(activity: Activity, file: File) = withContext(Dispatchers.IO) {
        require(activity.packageManager.canRequestPackageInstalls())
        if (pending(activity)) return@withContext
        val manager = activity.packageManager.packageInstaller
        val params = PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL).apply {
            setAppPackageName(UpdatePolicy.PACKAGE)
            setSize(file.length())
            setRequireUserAction(PackageInstaller.SessionParams.USER_ACTION_NOT_REQUIRED)
        }
        val id = manager.createSession(params)
        val nonce = UUID.randomUUID().toString()
        try {
            manager.openSession(id).use { session ->
                file.inputStream().use { input ->
                    session.openWrite("base.apk", 0, file.length()).use { output ->
                        input.copyTo(output);session.fsync(output)
                    }
                }
                UpdateRepository.prefs(activity).edit(commit = true) { putInt("install_session", id); putString(NONCE, nonce) }
                val result = Intent(activity, UpdatesActivity::class.java).apply {
                    action = RESULT
                    putExtra(NONCE, nonce)
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
                }
                val callback = PendingIntent.getActivity(activity, id, result,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE)
                session.commit(callback.intentSender)
            }
        } catch (failure: Throwable) {
            runCatching { manager.abandonSession(id) }
            UpdateRepository.prefs(activity).edit { remove("install_session"); remove(NONCE) }
            throw failure
        }
    }

    @Suppress("DEPRECATION")
    fun result(activity: Activity, intent: Intent): Boolean {
        if (intent.action != RESULT) return false
        val prefs = UpdateRepository.prefs(activity)
        val nonce = intent.getStringExtra(NONCE)
        if (nonce.isNullOrBlank() || nonce != prefs.getString(NONCE, null)) return true
        when (val status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE)) {
            PackageInstaller.STATUS_PENDING_USER_ACTION -> {
                val confirmation = if (Build.VERSION.SDK_INT >= 33) intent.getParcelableExtra(Intent.EXTRA_INTENT, Intent::class.java)
                    else intent.getParcelableExtra<Intent>(Intent.EXTRA_INTENT)
                if (confirmation != null) activity.startActivity(confirmation)
            }
            PackageInstaller.STATUS_SUCCESS -> {
                prefs.edit { remove("install_session"); remove(NONCE) }
                activity.startActivity(Intent(activity, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP))
                activity.finish()
            }
            else -> {
                prefs.edit { remove("install_session"); remove(NONCE) }
                AlertDialog.Builder(activity).setTitle(R.string.dv_updates)
                    .setMessage(activity.getString(R.string.dv_up_install_status, status))
                    .setPositiveButton(android.R.string.ok, null).show()
            }
        }
        return true
    }
}
