// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.updates

import com.squareup.moshi.JsonClass
import java.net.URI
import java.security.MessageDigest

@JsonClass(generateAdapter = true)
data class UpdateManifest(
    val schema: Int, val packageName: String, val versionName: String,
    val versionCode: Long, val minSdk: Int, val abi: String,
    val apkFileName: String, val apkBytes: Long, val sha256: String
)

@JsonClass(generateAdapter = true)
data class ReleaseAsset(val name: String, val size: Long, val browser_download_url: String)

@JsonClass(generateAdapter = true)
data class GithubRelease(
    val tag_name: String, val draft: Boolean, val prerelease: Boolean,
    val assets: List<ReleaseAsset>
)

@JsonClass(generateAdapter = true)
data class UpdateCandidate(val manifest: UpdateManifest, val tag: String, val url: String, val preview: Boolean)

/** Pure validation shared by the feed, cached metadata and package installer. */
object UpdatePolicy {
    const val PACKAGE = "by.remteh.remoteplay"
    const val REPOSITORY = "remteh-by/remteh-remote-play"
    const val REPO_URL = "https://github.com/" + REPOSITORY
    const val API_URL = "https://api.github.com/repos/" + REPOSITORY + "/releases?per_page=30"
    const val MAX_APK_BYTES = 100L * 1024 * 1024
    private val versionPattern = Regex("[0-9]+[.][0-9]+[.][0-9]+")
    private val hashPattern = Regex("[a-f0-9]{64}")
    private val filePattern = Regex("[A-Za-z0-9][A-Za-z0-9._-]{0,120}[.]apk")

    fun versionAtLeast(candidate: String, installed: String): Boolean {
        require(versionPattern.matches(candidate) && versionPattern.matches(installed)) { "Invalid version" }
        for ((next, current) in candidate.split('.').map { it.toLong() }.zip(installed.split('.').map { it.toLong() })) {
            if (next != current) return next > current
        }
        return true
    }

    fun allowedTransport(url: String): Boolean = runCatching {
        if (PrivateChannel.allowed(url)) return true
        val uri = URI(url)
        uri.scheme == "https" && uri.rawUserInfo == null && uri.rawFragment == null &&
            (uri.port == -1 || uri.port == 443) && uri.host in setOf(
                "api.github.com", "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"
            )
    }.getOrDefault(false)

    fun acceptHeader(url: String): String = if (URI(url).host == "api.github.com") "application/vnd.github+json" else "application/octet-stream"

    fun assetUrl(tag: String, name: String): String {
        require(tag.startsWith("v") && versionPattern.matches(tag.drop(1))) { "Invalid version tag" }
        require(name == "update.json" || filePattern.matches(name)) { "Invalid file name" }
        return REPO_URL + "/releases/download/" + tag + "/" + name
    }

    fun validate(manifest: UpdateManifest, tag: String, url: String, installedCode: Long, sdk: Int) {
        require(manifest.schema == 1 && manifest.packageName == PACKAGE) { "Update is for a different app" }
        require(versionPattern.matches(manifest.versionName) && tag == "v" + manifest.versionName) { "Version and tag do not match" }
        require(manifest.versionCode > installedCode && manifest.versionCode <= 2100000000L) { "Build already installed or older" }
        require(manifest.minSdk in 26..sdk && manifest.abi == "arm64-v8a") { "Update is not compatible with this device" }
        require(manifest.apkBytes in 1..MAX_APK_BYTES && hashPattern.matches(manifest.sha256)) { "Invalid size or SHA-256" }
        require(url == assetUrl(tag, manifest.apkFileName) || PrivateChannel.allowed(url) && URI(url).path.endsWith("/" + manifest.apkFileName)) { "File is outside the trusted Deckivo channel" }
    }

    fun verifyDownload(manifest: UpdateManifest, bytes: Long, hash: String) {
        require(bytes == manifest.apkBytes) { "Download incomplete" }
        require(MessageDigest.isEqual(hash.toByteArray(), manifest.sha256.toByteArray())) { "Download SHA-256 mismatch" }
    }

    fun verifyIdentity(manifest: UpdateManifest, actualPackage: String, actualCode: Long, actualName: String?,
                       actualMinSdk: Int, currentSigners: Set<String>, archiveSigners: Set<String>) {
        require(actualPackage == PACKAGE && actualPackage == manifest.packageName) { "Different Android package" }
        require(actualCode == manifest.versionCode && actualName == manifest.versionName && actualMinSdk == manifest.minSdk) { "APK version does not match descriptor" }
        require(currentSigners.isNotEmpty() && archiveSigners == currentSigners) { "APK signed with a different key" }
    }
}
