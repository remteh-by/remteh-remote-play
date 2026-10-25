// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.design

import android.app.Application
import android.app.LocaleManager
import android.os.Build
import android.os.LocaleList
import android.content.Context
import android.content.res.Configuration
import android.content.res.Resources
import android.view.MenuItem
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.metallic.chiaki.R

class DeckivoApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // English is intentional on first launch, independent of the system language.
        LanguagePicker.apply(this)
    }
    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        if (LanguagePicker.code(this) == "auto") LanguagePicker.apply(this)
    }
}

object LanguagePicker {
    val languages = linkedMapOf("en" to "English", "ru" to "Русский", "uk" to "Українська", "pl" to "Polski", "de" to "Deutsch", "fr" to "Français", "es" to "Español", "it" to "Italiano", "pt" to "Português", "tr" to "Türkçe", "zh" to "简体中文", "ja" to "日本語", "ko" to "한국어", "ar" to "العربية", "hi" to "हिन्दी", "id" to "Bahasa Indonesia")
    fun code(context: Context): String = context.getSharedPreferences("deckivo_locale", Context.MODE_PRIVATE).getString("language", "en")?.takeIf { it == "auto" || it in languages } ?: "en"
    private fun systemTags(context: Context): List<String> {
        val systemLocales = if (Build.VERSION.SDK_INT >= 33) context.getSystemService(LocaleManager::class.java).systemLocales else Resources.getSystem().configuration.locales
        return systemLocales.toLanguageTags().split(",")
    }
    fun effective(context: Context): String = LanguagePolicy.resolve(code(context), systemTags(context))
    fun localizedContext(context: Context): Context {
        // LocaleManager's first update can arrive after an Activity has attached.
        // Inflate the first frame in the chosen language, including restored screens.
        val config = Configuration(context.resources.configuration)
        config.setLocales(LocaleList.forLanguageTags(effective(context)))
        return context.createConfigurationContext(config)
    }
    fun apply(context: Context): Boolean {
        val language = effective(context)
        // API 33+ must use LocaleManager before any Activity delegate exists.
        if (Build.VERSION.SDK_INT >= 33) {
            val manager = context.getSystemService(LocaleManager::class.java)
            if (manager.applicationLocales.toLanguageTags() == language) return false
            manager.applicationLocales = LocaleList.forLanguageTags(language)
        } else {
            if (AppCompatDelegate.getApplicationLocales().toLanguageTags() == language) return false
            AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(language))
        }
        return true
    }
    fun label(context: Context): String = if(code(context) == "auto") context.getString(R.string.dv_automatic_language) + " ▾" else languages.getValue(code(context)) + " ▾"
    fun show(activity: AppCompatActivity) {
        val codes = listOf("auto") + languages.keys
        val automaticLanguage = LanguagePolicy.resolve("auto", systemTags(activity))
        val labels = arrayOf(activity.getString(R.string.dv_automatic_language) + " · " + languages.getValue(automaticLanguage)) + languages.values
        val picker = MaterialAlertDialogBuilder(activity)
            .setTitle(activity.getString(R.string.dv_language) + " / Language")
            .setSingleChoiceItems(labels, codes.indexOf(code(activity))) { dialog, index ->
                val tag = codes[index]
                activity.getSharedPreferences("deckivo_locale", Context.MODE_PRIVATE).edit().putString("language", tag).apply()
                dialog.dismiss()
                apply(activity)
                // Our localized base context must be reattached for a new choice.
                activity.recreate()
            }
            .setNegativeButton(android.R.string.cancel, null).create()
        // Keep Automatic visible even when a language farther down is selected.
        picker.setOnShowListener { picker.listView.setSelection(0) }
        picker.show()
    }
    fun addToToolbar(activity: AppCompatActivity, toolbar: MaterialToolbar) {
        toolbar.menu.add(label(activity)).apply {
            setShowAsAction(MenuItem.SHOW_AS_ACTION_ALWAYS)
            contentDescription = activity.getString(R.string.dv_language)
            setOnMenuItemClickListener { show(activity); true }
        }
    }
}
