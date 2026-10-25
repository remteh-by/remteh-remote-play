// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.updates

import android.content.Context
import android.os.Build
import com.metallic.chiaki.BuildConfig
import com.metallic.chiaki.R
import com.squareup.moshi.JsonClass
import com.squareup.moshi.Moshi
import java.net.URI
import java.security.KeyFactory
import java.security.Signature
import java.security.spec.X509EncodedKeySpec
import java.util.Base64

@JsonClass(generateAdapter = true)
data class PrivateIndex(val schema: Int, val packages: List<PrivatePackage>)

@JsonClass(generateAdapter = true)
data class PrivatePackage(val platform: String, val version: String, val build: Long,
    val filename: String, val bytes: Long, val sha256: String,
    val minSdk: Int = 26, val packageName: String = UpdatePolicy.PACKAGE, val abi: String = "arm64-v8a")

/** Private LAN previews are authenticated by a pinned signing key, never by HTTP alone. */
object PrivateChannel {
    val base: String get() = BuildConfig.PRIVATE_UPDATE_URL
    val enabled: Boolean get() = base.isNotBlank()

    fun allowed(url: String): Boolean = sameOriginAsset(base, url)

    fun sameOriginAsset(base: String, url: String): Boolean = runCatching {
        if (base.isBlank() || !base.endsWith('/')) return false
        val origin = URI(base); val target = URI(url)
        if (origin.rawUserInfo != null || origin.rawQuery != null || origin.rawFragment != null || origin.host == null) return false
        if (target.rawUserInfo != null || target.rawQuery != null || target.rawFragment != null) return false
        if (origin.scheme != target.scheme || origin.host != target.host || origin.port != target.port) return false
        if (origin.scheme != "https" && (origin.scheme != "http" || !privateV4(origin.host))) return false
        val filename = target.rawPath.removePrefix(origin.rawPath)
        target.rawPath.startsWith(origin.rawPath) && Regex("[A-Za-z0-9][A-Za-z0-9._-]{0,150}").matches(filename)
    }.getOrDefault(false)

    private fun privateV4(host: String?): Boolean {
        val bytes = host?.split('.')?.map { it.toIntOrNull() ?: return false } ?: return false
        if (bytes.size != 4 || bytes.any { it !in 0..255 }) return false
        return bytes[0] == 10 || bytes[0] == 127 || bytes[0] == 192 && bytes[1] == 168 || bytes[0] == 172 && bytes[1] in 16..31
    }

    fun verify(payload: ByteArray, signature: ByteArray, key: ByteArray) {
        require(payload.size <= 65536 && signature.size <= 1024) { "Invalid signed index size" }
        val publicKey = KeyFactory.getInstance("RSA").generatePublic(X509EncodedKeySpec(key))
        val verifier = Signature.getInstance("SHA256withRSA")
        verifier.initVerify(publicKey); verifier.update(payload)
        require(verifier.verify(Base64.getDecoder().decode(signature))) { "Update signature is invalid" }
    }

    fun choose(index: PrivateIndex, installedCode: Long, installedName: String, sdk: Int): PrivatePackage? {
        require(index.schema == 1) { "Unsupported update index" }
        return index.packages.filter { it.platform == "android-arm64" && it.build > installedCode && it.minSdk <= sdk &&
            UpdatePolicy.versionAtLeast(it.version, installedName) }.maxByOrNull { it.build }
    }

    suspend fun latest(context: Context): UpdateCandidate? {
        val http = UpdateHttp()
        val payload = http.text(base + "index.json", 65536).toByteArray(Charsets.UTF_8)
        val signature = http.text(base + "index.sig", 1024).toByteArray(Charsets.US_ASCII)
        val key = context.resources.openRawResource(R.raw.deckivo_update_public).use { it.readBytes() }
        verify(payload, signature, key)
        val index = Moshi.Builder().build().adapter(PrivateIndex::class.java).fromJson(payload.toString(Charsets.UTF_8)) ?: error("Invalid update index")
        return choose(index, BuildConfig.VERSION_CODE.toLong(), BuildConfig.VERSION_NAME, Build.VERSION.SDK_INT)?.let { entry ->
            val manifest = UpdateManifest(1,entry.packageName,entry.version,entry.build,entry.minSdk,entry.abi,entry.filename,entry.bytes,entry.sha256)
            val candidate = UpdateCandidate(manifest,"v" + entry.version,base + entry.filename,true)
            UpdatePolicy.validate(manifest,candidate.tag,candidate.url,BuildConfig.VERSION_CODE.toLong(),Build.VERSION.SDK_INT)
            candidate
        }
    }
}
