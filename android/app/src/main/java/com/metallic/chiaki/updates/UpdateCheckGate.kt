package com.metallic.chiaki.updates

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.CancellationException

internal data class CheckHistory(
    val started: Long = 0, val succeeded: Long = 0, val failures: Int = 0,
    val retryAt: Long = 0, val serverRetryAt: Long = 0
)

interface RetryDelay { val retryAfterMillis: Long? }

/** The caller serializes checks. Cancellation never counts as a completed check. */
internal class UpdateCheckGate(
    private val clock: () -> Long,
    private val read: () -> CheckHistory,
    private val write: (CheckHistory) -> Unit
) {
    suspend fun execute(manual: Boolean, interval: Long, request: suspend () -> Unit): Boolean {
        val now = clock()
        val previous = read().let { if (now < it.started) CheckHistory() else it }
        if (previous.serverRetryAt > 0 && previous.serverRetryAt > now) return false
        if (!manual && (previous.retryAt > 0 && previous.retryAt > now ||
                previous.started > 0 && now - previous.started < 5_000 ||
                previous.succeeded > 0 && now - previous.succeeded in 0 until interval)) return false
        write(previous.copy(started = now))
        try {
            request()
            currentCoroutineContext().ensureActive()
            write(CheckHistory(started = now, succeeded = clock()))
            return true
        } catch (cancelled: CancellationException) {
            // Retain only the short request-spacing guard, not the success interval.
            throw cancelled
        } catch (failure: Exception) {
            val failures = (previous.failures + 1).coerceIn(1, 6)
            val backoff = (60_000L * (1L shl (failures - 1))).coerceAtMost(30 * 60_000L)
            val serverDelay = (failure as? RetryDelay)?.retryAfterMillis?.coerceIn(0L, 24 * 60 * 60_000L) ?: 0
            write(previous.copy(started = now, failures = failures,
                retryAt = clock() + backoff, serverRetryAt = clock() + serverDelay))
            throw failure
        }
    }
}
