package com.metallic.chiaki.design

import org.junit.Assert.assertEquals
import org.junit.Test

class LanguagePolicyTest {
    @Test fun firstLaunchRemainsEnglishEvenOnRussianSystem() {
        assertEquals("en", LanguagePolicy.resolve(null, listOf("ru-RU")))
    }
    @Test fun manualChoiceWinsOverDeviceLanguage() {
        assertEquals("ja", LanguagePolicy.resolve("ja", listOf("de-DE", "en-US")))
    }
    @Test fun automaticSelectsFirstSupportedPreferredLanguage() {
        assertEquals("ru", LanguagePolicy.resolve("auto", listOf("fi-FI", "ru-RU", "en-US")))
    }
    @Test fun unknownAndEmptyLanguagesFallBackToEnglish() {
        assertEquals("en", LanguagePolicy.resolve("auto", listOf("fi-FI", "sv-SE")))
        assertEquals("en", LanguagePolicy.resolve("auto", emptyList()))
        assertEquals("en", LanguagePolicy.resolve("invalid", listOf("ru-RU")))
    }
    @Test fun regionalTagsAndLegacyIndonesianAreHandled() {
        assertEquals("pt", LanguagePolicy.resolve("auto", listOf("pt-BR")))
        assertEquals("zh", LanguagePolicy.resolve("auto", listOf("zh-Hans-CN")))
        assertEquals("id", LanguagePolicy.resolve("auto", listOf("in_ID")))
        assertEquals("ar", LanguagePolicy.resolve("auto", listOf("ar-EG")))
    }
}
