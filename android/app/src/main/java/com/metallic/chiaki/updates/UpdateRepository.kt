// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.updates

import androidx.core.content.edit
import android.content.Context
import android.content.pm.PackageInfo
import android.content.pm.PackageManager
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Build
import android.util.AtomicFile
import com.metallic.chiaki.BuildConfig
import com.metallic.chiaki.R
import com.squareup.moshi.Moshi
import com.squareup.moshi.Types
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest

data class UpdateState(
    val message: UpdateText = UpdateText(R.string.dv_up_not_checked),
    val candidate: UpdateCandidate? = null, val ready: Boolean = false,
    val busy: Boolean = false, val percent: Int? = null
)

/** Foreground-only updates. Leaving the home/update screen cancels its lifecycle job. */
object UpdateRepository {
    private const val INTERVAL = 6 * 60 * 60 * 1000L
    private val mutex = Mutex()
    private val mutable = MutableStateFlow(UpdateState())
    val state = mutable.asStateFlow()
    private val moshi = Moshi.Builder().build()
    private val candidateAdapter = moshi.adapter(UpdateCandidate::class.java)
    private val manifestAdapter = moshi.adapter(UpdateManifest::class.java)
    private val releasesAdapter = moshi.adapter<List<GithubRelease>>(Types.newParameterizedType(List::class.java, GithubRelease::class.java))

    fun prefs(context: Context) = context.getSharedPreferences("deckivo_updates", Context.MODE_PRIVATE)
    fun apk(context: Context) = File(context.filesDir, "updates/update.apk")
    private fun metadata(context: Context) = AtomicFile(File(context.filesDir, "updates/candidate.json"))
    private fun previewAllowed(context: Context) = prefs(context).getBoolean("preview", true)

    suspend fun check(context: Context, manual: Boolean = false) = operation(context) {
        restore(context)
        val settings = prefs(context)
        if (!manual && !settings.getBoolean("automatic", true)) return@operation
        val now = System.currentTimeMillis()
        val elapsed = now - settings.getLong("last_attempt", 0)
        val interval = if(PrivateChannel.enabled) 5 * 60 * 1000L else INTERVAL
        if (manual || elapsed < 0 || elapsed >= interval) {
            settings.edit { putLong("last_attempt", now) }
            mutable.value = mutable.value.copy(message = UpdateText(R.string.dv_up_checking), busy = true)
            val feed = if(PrivateChannel.enabled) emptyList() else releasesAdapter.fromJson(UpdateHttp().text(UpdatePolicy.API_URL, 2 * 1024 * 1024L)) ?: error("Invalid release list")
            val candidates = mutableListOf<UpdateCandidate>()
            if(PrivateChannel.enabled && previewAllowed(context)) PrivateChannel.latest(context)?.let { candidates += it }
            for (release in feed.filter { !it.draft && (!it.prerelease || previewAllowed(context)) }) {
                currentCoroutineContext().ensureActive()
                val descriptor = release.assets.singleOrNull { it.name == "update.json" } ?: continue
                // Older releases intentionally have no updater descriptor.
                require(descriptor.size in 1..65536 && descriptor.browser_download_url == UpdatePolicy.assetUrl(release.tag_name, "update.json")) { "Invalid release descriptor" }
                val manifest = manifestAdapter.fromJson(UpdateHttp().text(descriptor.browser_download_url, 65536)) ?: error("Invalid update descriptor")
                if (manifest.versionCode <= BuildConfig.VERSION_CODE || manifest.minSdk > Build.VERSION.SDK_INT) continue
                val asset = release.assets.singleOrNull { it.name == manifest.apkFileName } ?: error("Release has no APK")
                UpdatePolicy.validate(manifest, release.tag_name, asset.browser_download_url, BuildConfig.VERSION_CODE.toLong(), Build.VERSION.SDK_INT)
                require(asset.size == manifest.apkBytes) { "APK size does not match descriptor" }
                candidates += UpdateCandidate(manifest, release.tag_name, asset.browser_download_url, release.prerelease)
            }
            val candidate = candidates.maxByOrNull { it.manifest.versionCode }
            if (candidate == null) {
                clear(context)
                mutable.value = UpdateState(UpdateText(R.string.dv_up_current, listOf(BuildConfig.VERSION_NAME, BuildConfig.VERSION_CODE)))
                return@operation
            }
            if (candidate != mutable.value.candidate) {
                apk(context).delete()
                save(context, candidate)
                mutable.value = UpdateState(candidate = candidate)
            }
            restore(context)
        }
        val candidate = mutable.value.candidate ?: return@operation
        if (!mutable.value.ready && settings.getBoolean("download_wifi", true) && unmeteredWifi(context)) {
            downloadInside(context, candidate)
        } else if (!mutable.value.ready) {
            mutable.value = mutable.value.copy(message = UpdateText(R.string.dv_up_available, listOf(candidate.manifest.versionName)))
        }
    }

    suspend fun download(context: Context) = operation(context) {
        restore(context)
        val candidate = mutable.value.candidate ?: error("Check for updates first")
        downloadInside(context, candidate)
    }

    suspend fun verifyForInstall(context: Context): File = withContext(Dispatchers.IO) {
        mutex.lock()
        try {
            val candidate = mutable.value.candidate ?: error("No prepared update")
            require(!candidate.preview || previewAllowed(context)) { "Enable preview releases for this build" }
            validateApk(context, candidate, apk(context))
            apk(context)
        } finally { mutex.unlock() }
    }

    fun channelChanged(context: Context) {
        prefs(context).edit { putLong("last_attempt", 0) }
    }

    private suspend fun operation(context: Context, block: suspend () -> Unit) = withContext(Dispatchers.IO) {
        if (!mutex.tryLock()) return@withContext
        try {
            block()
        } catch (cancelled: CancellationException) {
            mutable.value = mutable.value.copy(message = UpdateText(if (mutable.value.ready) R.string.dv_up_ready else R.string.dv_up_paused))
            throw cancelled
        } catch (failure: Exception) {
            val detail = updateFailure(failure)
            mutable.value = mutable.value.copy(message = detail)
            // Automatic checks back off even on failure. Manual retry remains available.
        } finally {
            File(context.filesDir, "updates/download.part").delete()
            mutable.value = mutable.value.copy(busy = false, percent = null)
            mutex.unlock()
        }
    }

    private fun clear(context: Context) {
        metadata(context).delete()
        apk(context).delete()
    }

    private fun save(context: Context, candidate: UpdateCandidate) {
        val file = metadata(context)
        val stream = file.startWrite()
        try {
            stream.write(candidateAdapter.toJson(candidate).toByteArray(Charsets.UTF_8))
            file.finishWrite(stream)
        } catch (failure: Throwable) { file.failWrite(stream); throw failure }
    }

    private suspend fun restore(context: Context) {
        val file = metadata(context)
        if (!file.baseFile.exists() && !File(file.baseFile.path + ".bak").exists()) return
        val candidate = try {
            require(file.baseFile.length() <= 65536)
            candidateAdapter.fromJson(file.readFully().toString(Charsets.UTF_8))!!.also {
                UpdatePolicy.validate(it.manifest, it.tag, it.url, BuildConfig.VERSION_CODE.toLong(), Build.VERSION.SDK_INT)
                require(!it.preview || previewAllowed(context))
            }
        } catch (failure: Exception) {
            clear(context)
            mutable.value = UpdateState()
            return
        }
        var ready = false
        if (apk(context).exists()) {
            try { validateApk(context, candidate, apk(context)); ready = true }
            catch (cancelled: CancellationException) { throw cancelled }
            catch (failure: Exception) { apk(context).delete() }
        }
        mutable.value = UpdateState(
            if (ready) UpdateText(R.string.dv_up_downloaded, listOf(candidate.manifest.versionName))
            else UpdateText(R.string.dv_up_available, listOf(candidate.manifest.versionName)), candidate, ready
        )
    }

    private suspend fun downloadInside(context: Context, candidate: UpdateCandidate) {
        if (mutable.value.ready) return
        val part = File(context.filesDir, "updates/download.part")
        check(part.parentFile!!.mkdirs() || part.parentFile!!.isDirectory)
        mutable.value = UpdateState(UpdateText(R.string.dv_up_downloading, listOf(candidate.manifest.versionName)), candidate, busy = true, percent = 0)
        UpdateHttp().download(candidate, part) { progress -> mutable.value = mutable.value.copy(percent = progress) }
        validateApk(context, candidate, part)
        currentCoroutineContext().ensureActive()
        check(part.renameTo(apk(context))) { "Could not save APK" }
        mutable.value = UpdateState(UpdateText(R.string.dv_up_verified), candidate, ready = true)
    }

    @Suppress("DEPRECATION")
    private suspend fun validateApk(context: Context, candidate: UpdateCandidate, file: File) {
        val m = candidate.manifest
        UpdatePolicy.validate(m, candidate.tag, candidate.url, BuildConfig.VERSION_CODE.toLong(), Build.VERSION.SDK_INT)
        require(file.isFile && file.length() == m.apkBytes) { "APK missing or damaged" }
        val hash = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buffer = ByteArray(32768)
            while (true) {
                currentCoroutineContext().ensureActive()
                val count = input.read(buffer)
                if (count < 0) break
                hash.update(buffer, 0, count)
            }
        }
        UpdatePolicy.verifyDownload(m, file.length(), hash.digest().hex())
        val flags = if (Build.VERSION.SDK_INT >= 28) PackageManager.GET_SIGNING_CERTIFICATES else PackageManager.GET_SIGNATURES
        val installed = context.packageManager.getPackageInfo(context.packageName, flags)
        val archive = context.packageManager.getPackageArchiveInfo(file.path, flags) ?: error("Android could not read the APK")
        val code = if (Build.VERSION.SDK_INT >= 28) archive.longVersionCode else archive.versionCode.toLong()
        UpdatePolicy.verifyIdentity(m, archive.packageName, code, archive.versionName, archive.applicationInfo!!.minSdkVersion,
            signers(installed), signers(archive))
    }

    @Suppress("DEPRECATION")
    private fun signers(info: PackageInfo): Set<String> {
        val signatures = if (Build.VERSION.SDK_INT >= 28) info.signingInfo?.apkContentsSigners else info.signatures
        return signatures.orEmpty().map { MessageDigest.getInstance("SHA-256").digest(it.toByteArray()).hex() }.toSet()
    }

    private fun unmeteredWifi(context: Context): Boolean {
        val manager = context.getSystemService(ConnectivityManager::class.java)
        val caps = manager.getNetworkCapabilities(manager.activeNetwork) ?: return false
        return caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) && !manager.isActiveNetworkMetered
    }
}
