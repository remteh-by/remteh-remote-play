// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.main

import androidx.core.content.edit
import android.content.Intent
import android.content.res.Configuration
import android.net.Uri
import android.os.Bundle
import android.view.View
import com.metallic.chiaki.design.DeckivoActivity
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.Observer
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.GridLayoutManager
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.metallic.chiaki.R
import com.metallic.chiaki.common.*
import com.metallic.chiaki.common.ext.viewModelFactory
import com.metallic.chiaki.databinding.ActivityMainBinding
import com.metallic.chiaki.lib.ConnectInfo
import com.metallic.chiaki.lib.DiscoveryHost
import com.metallic.chiaki.lan.LanSetupActivity
import com.metallic.chiaki.lan.ControllerTestActivity
import com.metallic.chiaki.lan.SafeInsets
import com.metallic.chiaki.manualconsole.EditManualConsoleActivity
import com.metallic.chiaki.regist.RegistActivity
import com.metallic.chiaki.settings.SettingsActivity
import com.metallic.chiaki.stream.StreamActivity
import com.metallic.chiaki.updates.UpdateRepository
import com.metallic.chiaki.updates.UpdatesActivity
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive

class MainActivity : DeckivoActivity() {
    private lateinit var viewModel: MainViewModel
    private lateinit var binding: ActivityMainBinding
    private var updateJob: Job? = null
    private var updatePrompt: androidx.appcompat.app.AlertDialog? = null
    private var requestingInstall = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        SafeInsets.apply(binding.root)
        title = getString(R.string.app_name)
        binding.root.findViewById<android.widget.TextView>(R.id.buildVersion)?.text =
            getString(R.string.dv_version_build, com.metallic.chiaki.BuildConfig.VERSION_NAME, com.metallic.chiaki.BuildConfig.VERSION_CODE)
        binding.languageButton.text = com.metallic.chiaki.design.LanguagePicker.label(this)
        binding.languageButton.setOnClickListener { com.metallic.chiaki.design.LanguagePicker.show(this) }
        binding.navPlay.isEnabled = false
        binding.navPlay.alpha = 1f
        binding.navPlay.setTextColor(getColor(R.color.accent))
        binding.navSetup.setOnClickListener { open(ControllerTestActivity::class.java) }
        binding.navSettings.setOnClickListener { open(SettingsActivity::class.java) }
        binding.navUpdates.setOnClickListener { open(com.metallic.chiaki.design.SessionHistoryActivity::class.java) }
        binding.updatesButton.setOnClickListener { open(UpdatesActivity::class.java) }
        binding.controllerTestButton.setOnClickListener { open(ControllerTestActivity::class.java) }
        listOf(binding.qualityFast,binding.qualityBalanced,binding.qualitySafe).forEachIndexed { index, control ->
            control.isCheckable = true
            control.setOnClickListener {
                val p = Preferences(this)
                p.resolution = if(index == 2) Preferences.Resolution.RES_540P else Preferences.Resolution.RES_720P
                p.fps = if(index == 0) Preferences.FPS.FPS_60 else Preferences.FPS.FPS_30
                p.bitrate = listOf(10000,7000,5000)[index]
                listOf(binding.qualityFast,binding.qualityBalanced,binding.qualitySafe).forEachIndexed { i,b -> b.isChecked = i == index }
            }
        }
        binding.updateStatus.setOnClickListener { open(UpdatesActivity::class.java) }
        binding.developerCredit.setOnClickListener {
            com.metallic.chiaki.design.LinkUi.openLinkOrShowQr(this, "https://remteh.by/")
        }
        binding.supportButton.setOnClickListener { open(com.metallic.chiaki.design.SupportActivity::class.java) }
        binding.addConsoleButton.setOnClickListener {
            MaterialAlertDialogBuilder(this).setTitle(getString(R.string.dv_add_console))
                .setItems(arrayOf(getString(R.string.dv_guided), getString(R.string.dv_manual_ip), getString(R.string.dv_register_profile))) { _, choice ->
                    when (choice) {
                        0 -> open(LanSetupActivity::class.java)
                        1 -> open(EditManualConsoleActivity::class.java)
                        2 -> open(RegistActivity::class.java)
                    }
                }.show()
        }
        viewModel = ViewModelProvider(this, viewModelFactory { MainViewModel(getDatabase(this), Preferences(this)) }).get(MainViewModel::class.java)
        val adapter = DisplayHostRecyclerViewAdapter(this::hostTriggered, this::wakeupHost, this::editHost, this::deleteHost)
        binding.hostsRecyclerView.adapter = adapter
        binding.hostsRecyclerView.layoutManager = GridLayoutManager(this, if(resources.configuration.screenWidthDp >= 1400) 2 else 1)
        viewModel.displayHosts.observe(this, Observer {
            adapter.hosts = it
            binding.emptyInfoLayout.visibility = if(it.isEmpty()) View.VISIBLE else View.GONE
            binding.libraryStatus.text = if(it.isEmpty()) getString(R.string.dv_connect_yours) else getString(R.string.dv_your_consoles) + " " + it.size
        })
        binding.discoveryButton.setOnClickListener { viewModel.discoveryManager.active = !(viewModel.discoveryActive.value ?: false) }
        viewModel.discoveryActive.observe(this, Observer { active ->
            binding.discoveryButton.text = if(active) getString(R.string.dv_discovery_on) else getString(R.string.dv_discovery_find)
            binding.discoveryButton.setIconResource(if(active) R.drawable.ic_discover_on else R.drawable.ic_discover_off)
            binding.emptyInfoTextView.text = if(active) getString(R.string.dv_searching) else getString(R.string.dv_search_off)
        })
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.RESUMED) {
                UpdateRepository.state.collect { state ->
                    binding.updateStatus.visibility = if(state.ready) View.VISIBLE else View.GONE
                    if (state.ready) offerPreparedUpdate(state)
                }
            }
        }
        val setupPrefs = getSharedPreferences("remteh_lan", MODE_PRIVATE)
        if (!setupPrefs.getBoolean("initialized", false)) {
            com.metallic.chiaki.lan.SwitchProfile.apply(Preferences(this))
            setupPrefs.edit { putBoolean("initialized", true) }
            open(LanSetupActivity::class.java)
        }
    }
    private fun open(type: Class<*>) { startActivity(Intent(this, type)) }
    private fun offerPreparedUpdate(state: com.metallic.chiaki.updates.UpdateState) {
        val candidate = state.candidate ?: return
        val prefs = UpdateRepository.prefs(this)
        if (!prefs.getBoolean("automatic", true) || updatePrompt != null) return
        val code = candidate.manifest.versionCode
        if (prefs.getLong("prompted_build", 0) == code && System.currentTimeMillis() - prefs.getLong("prompted_at", 0) < 24*60*60*1000L) return
        fun remember() { prefs.edit { putLong("prompted_build", code); putLong("prompted_at", System.currentTimeMillis()) } }
        if (android.os.Build.VERSION.SDK_INT >= 31 && packageManager.canRequestPackageInstalls() &&
            !com.metallic.chiaki.updates.SelfUpdateInstaller.pending(this)) {
            remember();requestingInstall = true
            startActivity(Intent(this, UpdatesActivity::class.java).putExtra(UpdatesActivity.EXTRA_INSTALL_READY, true))
            return
        }
        updatePrompt = MaterialAlertDialogBuilder(this)
            .setTitle(getString(R.string.dv_updates) + " · " + candidate.manifest.versionName)
            .setMessage(getString(R.string.dv_update_ready))
            .setPositiveButton(R.string.dv_install) { _, _ ->
                remember();requestingInstall = true
                startActivity(Intent(this, UpdatesActivity::class.java).putExtra(UpdatesActivity.EXTRA_INSTALL_READY, true))
            }
            .setNegativeButton(android.R.string.cancel) { _, _ -> remember() }
            .setOnCancelListener { remember() }
            .create().also { dialog -> dialog.setOnDismissListener { updatePrompt = null }; dialog.show() }
    }
    override fun onStart() {
        super.onStart()
        viewModel.discoveryManager.resume()
        updateJob = lifecycleScope.launch {
            while(isActive) { UpdateRepository.check(applicationContext); delay(60_000) }
        }
    }
    override fun onResume() {
        super.onResume()
        requestingInstall = com.metallic.chiaki.updates.SelfUpdateInstaller.pending(this)
        binding.root.post { if (lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED) && !requestingInstall && !UpdateRepository.state.value.ready) com.metallic.chiaki.design.SupportNudges.showIfDue(this) }
    }
    override fun onStop() {
        updatePrompt?.dismiss()
        updateJob?.cancel()
        viewModel.discoveryManager.pause()
        super.onStop()
    }
    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        // Reinflate the compact or wide shell while retaining console data and preferences.
        recreate()
    }
    private fun hostTriggered(host: DisplayHost)
    {
        if (requestingInstall) return
        val registeredHost = host.registeredHost
        if(registeredHost != null)
        {
            fun connect() {
                val connectInfo = ConnectInfo(host.isPS5, host.host, registeredHost.rpRegistKey, registeredHost.rpKey, Preferences(this).videoProfile)
                Intent(this, StreamActivity::class.java).let {
                    it.putExtra(StreamActivity.EXTRA_CONNECT_INFO, connectInfo)
                    startActivity(it)
                }
            }

            if(host is DiscoveredDisplayHost && host.discoveredHost.state == DiscoveryHost.State.STANDBY)
            {
                MaterialAlertDialogBuilder(this)
                    .setMessage(R.string.alert_message_standby_wakeup)
                    .setPositiveButton(R.string.action_wakeup) { _, _ ->
                        wakeupHost(host)
                    }
                    .setNeutralButton(R.string.action_connect_immediately) { _, _ ->
                        connect()
                    }
                    .setNegativeButton(R.string.action_connect_cancel_connect) { _, _ -> }
                    .create()
                    .show()
            }
            else
                connect()
        }
        else
        {
            Intent(this, RegistActivity::class.java).let {
                it.putExtra(RegistActivity.EXTRA_HOST, host.host)
                it.putExtra(RegistActivity.EXTRA_BROADCAST, false)
                if(host is ManualDisplayHost)
                    it.putExtra(RegistActivity.EXTRA_ASSIGN_MANUAL_HOST_ID, host.manualHost.id)
                startActivity(it)
            }
        }
    }

    private fun wakeupHost(host: DisplayHost)
    {
        val registeredHost = host.registeredHost ?: return
        viewModel.discoveryManager.sendWakeup(host.host, registeredHost.rpRegistKey, registeredHost.target.isPS5)
    }

    private fun editHost(host: DisplayHost)
    {
        val manualHost = host.manualHost ?: return
        Intent(this, EditManualConsoleActivity::class.java).also {
            it.putExtra(EditManualConsoleActivity.EXTRA_MANUAL_HOST_ID, manualHost.id)
            startActivity(it)
        }
    }

    private fun deleteHost(host: DisplayHost)
    {
        val manualHost = host.manualHost ?: return
        MaterialAlertDialogBuilder(this)
            .setMessage(getString(R.string.alert_message_delete_manual_host, manualHost.host))
            .setPositiveButton(R.string.action_delete) { _, _ ->
                viewModel.deleteManualHost(manualHost)
            }
            .setNegativeButton(R.string.action_keep) { _, _ -> }
            .create()
            .show()
    }
}
