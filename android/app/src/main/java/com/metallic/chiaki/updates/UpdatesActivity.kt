// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.updates

import androidx.core.content.edit
import com.metallic.chiaki.R
import android.content.ActivityNotFoundException
import androidx.core.net.toUri
import android.content.Intent
import android.os.Bundle
import android.os.Build
import android.provider.Settings
import android.view.MenuItem
import android.view.View
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import java.util.Locale
import com.metallic.chiaki.design.DeckivoUi
import com.metallic.chiaki.design.DeckivoActivity
import androidx.core.content.FileProvider
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.google.android.material.button.MaterialButton
import com.google.android.material.switchmaterial.SwitchMaterial
import com.metallic.chiaki.BuildConfig
import com.metallic.chiaki.lan.SafeInsets
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

class UpdatesActivity : DeckivoActivity() {
    companion object { const val EXTRA_INSTALL_READY = "deckivo_install_ready" }
    private lateinit var panel: LinearLayout
    private lateinit var status: TextView
    private lateinit var progress: ProgressBar
    private lateinit var checkButton: MaterialButton
    private lateinit var downloadButton: MaterialButton
    private lateinit var installButton: MaterialButton
    private val settings by lazy { UpdateRepository.prefs(this) }
    private var work: Job? = null
    private var waitingForInstallPermission = false
    private var installWhenReady = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        title = getString(R.string.dv_about_updates)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        waitingForInstallPermission = savedInstanceState?.getBoolean("install_permission", false) ?: false
        installWhenReady = if (savedInstanceState == null) intent.getBooleanExtra(EXTRA_INSTALL_READY, false) else false
        val content = DeckivoUi.screen(this, getString(R.string.dv_about), getString(R.string.dv_tagline))
        panel = DeckivoUi.section(content, getString(R.string.dv_named_version, BuildConfig.VERSION_NAME))
        label(getString(R.string.dv_build_details, BuildConfig.VERSION_CODE, getString(R.string.dv_build_suffix)), 14f)
        button(getString(R.string.dv_developer_credit)) { openLink("https://remteh.by/") }
        label(getString(R.string.dv_attribution), 14f)
        button(getString(R.string.dv_source)) { openLink(UpdatePolicy.REPO_URL + "/blob/main/ATTRIBUTION.md") }
        button(getString(R.string.dv_licenses)) { startActivity(Intent(this, com.metallic.chiaki.design.LicensesActivity::class.java)) }
        val supporters = com.metallic.chiaki.design.SupportActivity.configuration(this).getJSONArray("supporters")
        if (supporters.length() > 0) {
            panel = DeckivoUi.section(content, getString(R.string.dv_supporters))
            for (i in 0 until supporters.length()) {
                val person = supporters.getJSONObject(i)
                label(getString(R.string.dv_supporter_since, person.getString("name"), person.getString("since")), 14f)
            }
        }
        panel = DeckivoUi.section(content, getString(R.string.dv_support))
        label(getString(R.string.dv_support_note), 14f)
        button(getString(R.string.dv_support)) { startActivity(Intent(this, com.metallic.chiaki.design.SupportActivity::class.java)) }
        panel = DeckivoUi.section(content, getString(R.string.dv_updates))
        label(getString(R.string.dv_updates_intro), 14f)
        toggle(getString(R.string.dv_auto_check), "automatic", true)
        toggle(getString(R.string.dv_auto_download), "download_wifi", true)
        toggle(getString(R.string.dv_preview), "preview", true)
        status = label("", 16f)
        status.accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_POLITE
        progress = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            max = 100
            visibility = View.GONE
        }
        panel.addView(progress, LinearLayout.LayoutParams(-1, dp(8)))
        checkButton = button(getString(R.string.dv_check_now)) { runCheck(manual = true) }
        downloadButton = button(getString(R.string.dv_download)) {
            work?.cancel()
            work = lifecycleScope.launch { UpdateRepository.download(applicationContext) }
        }
        installButton = button(getString(R.string.dv_install)) { install() }
        button(getString(R.string.dv_release_notes)) { openLink(UpdatePolicy.REPO_URL + "/releases") }


        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                UpdateRepository.state.collect { state ->
                    status.text = state.message.render(this@UpdatesActivity)
                    progress.visibility = if (state.busy) View.VISIBLE else View.GONE
                    progress.isIndeterminate = state.percent == null
                    progress.progress = state.percent ?: 0
                    checkButton.isEnabled = !state.busy
                    downloadButton.visibility = if (state.candidate != null && !state.ready) View.VISIBLE else View.GONE
                    downloadButton.isEnabled = !state.busy
                    state.candidate?.let {
                        downloadButton.text = getString(R.string.dv_up_download_size, it.manifest.versionName, it.manifest.apkBytes / 1048576.0)
                    }
                    installButton.visibility = if (state.ready) View.VISIBLE else View.GONE
                    installButton.isEnabled = !state.busy
                    if (state.ready && installWhenReady && lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) {
                        installWhenReady = false
                        install()
                    }
                }
            }
        }
        SelfUpdateInstaller.result(this, intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        SelfUpdateInstaller.result(this, intent)
    }

    override fun onStart() {
        super.onStart()
        runCheck(manual = false)
    }

    override fun onStop() {
        work?.cancel()
        super.onStop()
    }

    override fun onResume() {
        super.onResume()
        if (installWhenReady && UpdateRepository.state.value.ready) {
            installWhenReady = false
            install()
        }
        if (waitingForInstallPermission) {
            waitingForInstallPermission = false
            if (packageManager.canRequestPackageInstalls()) install()
            else status.text = getString(R.string.dv_permission_denied)
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        outState.putBoolean("install_permission", waitingForInstallPermission)
        super.onSaveInstanceState(outState)
    }

    private fun runCheck(manual: Boolean) {
        work?.cancel()
        work = lifecycleScope.launch { UpdateRepository.check(applicationContext, manual) }
    }

    private fun install() {
        if (!packageManager.canRequestPackageInstalls()) {
            waitingForInstallPermission = true
            try { startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, ("package:" + packageName).toUri())) }
            catch (failure: ActivityNotFoundException) {
                waitingForInstallPermission = false
                status.text = getString(R.string.dv_install_permission)
            }
            return
        }
        work?.cancel()
        work = lifecycleScope.launch {
            installButton.isEnabled = false
            try {
                val file = UpdateRepository.verifyForInstall(applicationContext)
                if (Build.VERSION.SDK_INT >= 31) {
                    SelfUpdateInstaller.install(this@UpdatesActivity, file)
                    return@launch
                }
                val uri = FileProvider.getUriForFile(this@UpdatesActivity, packageName + ".fileprovider", file)
                startActivity(Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, "application/vnd.android.package-archive")
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                })
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (failure: Exception) { status.text = updateFailure(failure).render(this@UpdatesActivity) }
            finally { installButton.isEnabled = true }
        }
    }

    private fun toggle(text: String, key: String, default: Boolean) {
        val control = SwitchMaterial(this).apply {
            this.text = text
            minHeight = dp(56)
            isChecked = settings.getBoolean(key, default)
            setOnCheckedChangeListener { _, checked ->
                settings.edit { putBoolean(key, checked) }
                if (key == "preview") UpdateRepository.channelChanged(this@UpdatesActivity)
                work?.cancel()
                // A manual check applies channel changes even when automatic checking is disabled.
                runCheck(manual = key == "preview")
            }
        }
        panel.addView(control, LinearLayout.LayoutParams(-1, -2))
    }

    private fun label(text: String, size: Float): TextView = DeckivoUi.label(panel, text, size)

    private fun button(text: String, action: () -> Unit): MaterialButton = DeckivoUi.button(panel, text, text == getString(R.string.dv_install), action)

    private fun openLink(url: String) = com.metallic.chiaki.design.LinkUi.openLinkOrShowQr(this, url)

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        if (item.itemId == android.R.id.home) { finish(); return true }
        return super.onOptionsItemSelected(item)
    }
}
