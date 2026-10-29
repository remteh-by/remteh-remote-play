// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.updates

import com.metallic.chiaki.R
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.Locale
import javax.net.ssl.HttpsURLConnection

/** HTTPS only, bounded redirects/size/time; never sends console credentials or account identifiers. */
internal class UpdateHttp {
    suspend fun text(url: String, maxBytes: Long): String {
        val output = ByteArrayOutputStream()
        read(url, maxBytes) { bytes, count -> output.write(bytes, 0, count) }
        return output.toString("UTF-8")
    }

    suspend fun download(candidate: UpdateCandidate, file: File, onProgress: (Int) -> Unit) {
        val digest = MessageDigest.getInstance("SHA-256")
        var total = 0L
        try {
            FileOutputStream(file).use { output ->
                read(candidate.url, candidate.manifest.apkBytes) { bytes, count ->
                    output.write(bytes, 0, count)
                    digest.update(bytes, 0, count)
                    total += count
                    onProgress((total * 100 / candidate.manifest.apkBytes).toInt())
                }
                output.fd.sync()
            }
            UpdatePolicy.verifyDownload(candidate.manifest, total, digest.digest().hex())
        } catch (failure: Throwable) {
            file.delete()
            throw failure
        }
    }

    private suspend fun read(initialUrl: String, maxBytes: Long, consume: (ByteArray, Int) -> Unit) {
        var url = initialUrl
        val started = System.nanoTime()
        repeat(6) { redirect ->
            currentCoroutineContext().ensureActive()
            require(UpdatePolicy.allowedTransport(url)) { "Untrusted update URL" }
            val connection = URL(url).openConnection() as HttpURLConnection
            connection.instanceFollowRedirects = false
            connection.connectTimeout = 12000
            connection.readTimeout = 15000
            connection.setRequestProperty("Accept", UpdatePolicy.acceptHeader(url))
            connection.setRequestProperty("User-Agent", "Deckivo-Updater")
            connection.setRequestProperty("Accept-Encoding", "identity")
            try {
                val status = connection.responseCode
                if (status in setOf(301, 302, 303, 307, 308)) {
                    require(redirect < 5) { "Too many redirects" }
                    val location = connection.getHeaderField("Location") ?: error("Missing redirect location")
                    url = URL(URL(url), location).toString()
                } else {
                    if (status != HttpURLConnection.HTTP_OK) {
                        val limited = status == 429 || status == 403 &&
                            (connection.getHeaderField("X-RateLimit-Remaining") == "0" || connection.getHeaderField("Retry-After") != null)
                        val retry = if (limited) retryDelay(connection.getHeaderField("Retry-After"),
                            connection.getHeaderField("X-RateLimit-Reset"), System.currentTimeMillis()) else null
                        throw UpdateFailure(if (limited) UpdateText(R.string.dv_up_rate_limit)
                            else UpdateText(R.string.dv_up_http_error, listOf(status)), retry)
                    }
                    val length = connection.contentLengthLong
                    require(length <= maxBytes) { "File exceeds size limit" }
                    var total = 0L
                    connection.inputStream.use { input ->
                        val buffer = ByteArray(32768)
                        while (true) {
                            currentCoroutineContext().ensureActive()
                            check(System.nanoTime() - started < 180_000_000_000L) { "Download timed out" }
                            val count = input.read(buffer)
                            if (count < 0) break
                            total += count
                            require(total <= maxBytes) { "File exceeds size limit" }
                            consume(buffer, count)
                        }
                    }
                    if (length >= 0) require(total == length) { "Connection ended before download completed" }
                    return
                }
            } finally {
                connection.disconnect()
            }
        }
        error("Could not retrieve update")
    }
}

internal fun ByteArray.hex(): String = joinToString("") { String.format(Locale.ROOT, "%02x", it) }

internal fun retryDelay(after: String?, reset: String?, now: Long): Long {
    val seconds = after?.toLongOrNull()?.takeIf { it in 0..86400 }?.times(1000)
    val date = if (seconds == null && after != null) runCatching {
        java.time.ZonedDateTime.parse(after, java.time.format.DateTimeFormatter.RFC_1123_DATE_TIME).toInstant().toEpochMilli() - now
    }.getOrNull() else null
    val resetDelay = reset?.toLongOrNull()?.takeIf { it in 0..Long.MAX_VALUE / 1000 }?.let { it * 1000 - now }
    return listOfNotNull(seconds, date?.coerceAtLeast(0), resetDelay?.coerceAtLeast(0)).maxOrNull()?.coerceAtMost(86_400_000) ?: 900_000
}
