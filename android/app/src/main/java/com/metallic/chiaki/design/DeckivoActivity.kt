// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.design

import android.content.Context
import androidx.appcompat.app.AppCompatActivity

open class DeckivoActivity : AppCompatActivity() {
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(LanguagePicker.localizedContext(newBase))
    }
    override fun onResume() {
        super.onResume()
        // Re-evaluate Automatic after returning from Android's language settings.
        val rendered = LanguagePolicy.resolve("auto", listOf(resources.configuration.locales[0].toLanguageTag()))
        if (rendered != LanguagePicker.effective(this)) {
            LanguagePicker.apply(this)
            recreate()
        }
    }
}
