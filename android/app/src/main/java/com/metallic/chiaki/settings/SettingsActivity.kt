// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL

package com.metallic.chiaki.settings

import android.content.res.Resources
import android.os.Bundle
import android.view.Menu
import android.view.View
import com.google.android.material.tabs.TabLayout
import com.metallic.chiaki.lan.SafeInsets
import com.metallic.chiaki.design.LanguagePicker
import com.metallic.chiaki.design.DeckivoActivity
import androidx.fragment.app.Fragment
import androidx.preference.Preference
import androidx.preference.PreferenceFragmentCompat
import com.metallic.chiaki.R
import com.metallic.chiaki.databinding.ActivitySettingsBinding

interface TitleFragment
{
    fun getTitle(resources: Resources): String
}

class SettingsActivity: DeckivoActivity(), PreferenceFragmentCompat.OnPreferenceStartFragmentCallback
{
    private lateinit var binding: ActivitySettingsBinding

    override fun onCreate(savedInstanceState: Bundle?)
    {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)
        title = ""
        setSupportActionBar(binding.toolbar)
        SafeInsets.apply(binding.root)
        binding.toolbar.setNavigationOnClickListener { onBackPressedDispatcher.onBackPressed() }
        listOf(R.string.dv_settings, R.string.dv_video, R.string.dv_button_layout, R.string.dv_data).forEach { binding.settingsTabs.addTab(binding.settingsTabs.newTab().setText(it)) }
        binding.settingsTabs.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab) { (supportFragmentManager.findFragmentById(R.id.settingsFragment) as? SettingsFragment)?.showCategory(tab.position) }
            override fun onTabUnselected(tab: TabLayout.Tab) {}
            override fun onTabReselected(tab: TabLayout.Tab) {}
        })

        val rootFragment = SettingsFragment()
        if (savedInstanceState == null) replaceFragment(rootFragment, false)
        supportFragmentManager.addOnBackStackChangedListener {
            binding.settingsTabs.visibility = if(supportFragmentManager.backStackEntryCount == 0) View.VISIBLE else View.GONE
            val titleFragment = supportFragmentManager.findFragmentById(R.id.settingsFragment) as? TitleFragment ?: return@addOnBackStackChangedListener
            binding.titleTextView.text = titleFragment.getTitle(resources)
        }
        binding.titleTextView.text = rootFragment.getTitle(resources)
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        super.onCreateOptionsMenu(menu)
        // The ActionBar rebuilds this menu after onCreate, so add language here.
        LanguagePicker.addToToolbar(this, binding.toolbar)
        return true
    }

    override fun onPreferenceStartFragment(caller: PreferenceFragmentCompat, pref: Preference) = when(pref.fragment)
    {
        SettingsRegisteredHostsFragment::class.java.canonicalName -> {
            replaceFragment(SettingsRegisteredHostsFragment(), true)
            true
        }
        SettingsLogsFragment::class.java.canonicalName -> { replaceFragment(SettingsLogsFragment(), true); true }
        else -> false
    }

    private fun replaceFragment(fragment: Fragment, addToBackStack: Boolean)
    {
        supportFragmentManager.beginTransaction()
            .setCustomAnimations(android.R.anim.fade_in, android.R.anim.fade_out)
            .replace(R.id.settingsFragment, fragment)
            .also {
                if(addToBackStack)
                    it.addToBackStack(null)
            }
            .commit()
    }
}
