// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.updates

import com.squareup.moshi.Moshi
import org.junit.Assert.*
import org.junit.Test

class UpdatePolicyTest {
    private val manifest = UpdateManifest(1, UpdatePolicy.PACKAGE, "0.2.0", 5, 26, "arm64-v8a", "Deckivo-0.2.0-arm64.apk", 6000000, "a".repeat(64))
    private val url = UpdatePolicy.assetUrl("v0.2.0", manifest.apkFileName)
    private fun validate(m: UpdateManifest = manifest, address: String = url, installed: Long = 4) =
        UpdatePolicy.validate(m, "v0.2.0", address, installed, 35)
    private fun rejected(action: () -> Unit) { assertThrows(IllegalArgumentException::class.java) { action() } }

    @Test fun usesJsonAcceptForApiAndBinaryForAssets() {
        assertEquals("application/vnd.github+json", UpdatePolicy.acceptHeader(UpdatePolicy.API_URL))
        assertEquals("application/octet-stream", UpdatePolicy.acceptHeader(url))
    }
    @Test fun validUpgradeAndJsonRoundTrip() {
        validate()
        val adapter = Moshi.Builder().build().adapter(UpdateCandidate::class.java)
        val candidate = UpdateCandidate(manifest, "v0.2.0", url, true)
        assertEquals(candidate, adapter.fromJson(adapter.toJson(candidate)))
    }
    @Test fun rejectsDowngradeAndSameBuild() {
        rejected { validate(installed = 5) }
        rejected { validate(installed = 6) }
        rejected { validate(manifest.copy(versionCode = 0)) }
    }
    @Test fun rejectsOtherPackageSchemaAndTag() {
        rejected { validate(manifest.copy(packageName = "com.example.other")) }
        rejected { validate(manifest.copy(schema = 2)) }
        rejected { validate(manifest.copy(versionName = "0.3.0")) }
    }
    @Test fun rejectsIncompatibleAndroidAndAbi() {
        rejected { validate(manifest.copy(minSdk = 36)) }
        rejected { validate(manifest.copy(abi = "x86_64")) }
    }
    @Test fun rejectsOversizedEmptyAndMalformedDigest() {
        rejected { validate(manifest.copy(apkBytes = UpdatePolicy.MAX_APK_BYTES + 1)) }
        rejected { validate(manifest.copy(apkBytes = 0)) }
        rejected { validate(manifest.copy(sha256 = "a")) }
    }
    @Test fun rejectsExternalAndTraversalAssets() {
        rejected { validate(address = url.replace("remteh-by", "attacker")) }
        rejected { validate(address = url + "?download=1") }
        rejected { validate(manifest.copy(apkFileName = "../game.apk")) }
        rejected { UpdatePolicy.assetUrl("v0.2.0/../other", "update.json") }
        rejected { UpdatePolicy.assetUrl("v0.2.0", "folder/evil.apk") }
    }
    @Test fun restrictsHttpsRedirects() {
        assertTrue(UpdatePolicy.allowedTransport(url))
        assertTrue(UpdatePolicy.allowedTransport("https://release-assets.githubusercontent.com/asset?sig=test"))
        listOf("http://github.com/asset", "https://github.com.evil.test/asset", "https://127.0.0.1/asset", "https://github.com:444/asset", "https://user@github.com/asset", "https://github.com/asset#fragment", "file:///asset").forEach {
            assertFalse(it, UpdatePolicy.allowedTransport(it))
        }
    }
    @Test fun rejectsTruncatedAndAlteredFile() {
        UpdatePolicy.verifyDownload(manifest, manifest.apkBytes, manifest.sha256)
        rejected { UpdatePolicy.verifyDownload(manifest, manifest.apkBytes - 1, manifest.sha256) }
        rejected { UpdatePolicy.verifyDownload(manifest, manifest.apkBytes, "b".repeat(64)) }
    }
    @Test fun requiresSameSigningIdentityAndManifestVersion() {
        fun identity(signers: Set<String> = setOf("original"), code: Long = 5, name: String = "0.2.0", pkg: String = UpdatePolicy.PACKAGE, minSdk: Int = 26) =
            UpdatePolicy.verifyIdentity(manifest, pkg, code, name, minSdk, setOf("original"), signers)
        identity()
        rejected { identity(setOf("attacker")) }
        rejected { identity(emptySet()) }
        rejected { identity(setOf("original", "attacker")) }
        rejected { identity(code = 6) }
        rejected { identity(name = "0.2.1") }
        rejected { identity(pkg = "com.example.other") }
        rejected { identity(minSdk = 35) }
    }
}
