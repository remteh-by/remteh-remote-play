package com.metallic.chiaki.lan

import org.junit.Assert.*
import org.junit.Test

class FirmwareCatalogPolicyTest {
    @Test fun binarySelectorsAreRejected() {
        assertTrue(FirmwareCatalogPolicy.permits(null, null))
        for (query in listOf("", "family=0004&version=0x0458", "download=1")) {
            assertFalse(FirmwareCatalogPolicy.permits(query, null))
        }
        assertFalse(FirmwareCatalogPolicy.permits(null, "download"))
    }
    @Test fun catalogDoesNotExposeUnrecognisedFamiliesOrFileLocations() {
        assertEquals(mapOf("0004" to "0x0458"), FirmwareCatalogPolicy.versions(mapOf(
            "0004" to "0x0458", "000B" to "file.bin", "artifacts" to "/firmware.bin", "other" to "0x9999")))
    }
}
