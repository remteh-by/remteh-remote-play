// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.design

import java.util.Locale

object LanguagePolicy {
    val supported = setOf("en", "ru", "uk", "pl", "de", "fr", "es", "it", "pt", "tr", "zh", "ja", "ko", "ar", "hi", "id")
    fun resolve(choice: String?, systemTags: List<String>): String {
        if (choice != "auto") return choice?.takeIf { it in supported } ?: "en"
        return systemTags.asSequence().map {
            val language = it.replace('_', '-').substringBefore('-').lowercase(Locale.ROOT)
            if (language == "in") "id" else language
        }.firstOrNull { it in supported } ?: "en"
    }
}
