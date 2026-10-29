package com.metallic.chiaki.updates

import kotlinx.coroutines.*
import org.junit.Assert.*
import org.junit.Test

class UpdateCheckGateTest {
    private var now = 1_000_000L
    private var history = CheckHistory()
    private val gate = UpdateCheckGate({ now }, { history }, { history = it })
    private val interval = 21_600_000L

    @Test fun leavingScreenBeforeReplyDoesNotSpendSuccessInterval() = runBlocking {
        val entered = CompletableDeferred<Unit>()
        val job = launch { gate.execute(false, interval) { entered.complete(Unit); awaitCancellation() } }
        entered.await(); job.cancelAndJoin()
        assertEquals(0L, history.succeeded); assertEquals(0, history.failures)
        now += 6_000
        var called = false
        assertTrue(gate.execute(false, interval) { called = true })
        assertTrue(called); assertEquals(now, history.succeeded)
    }

    @Test fun cancellationAfterSavingCandidateRetainsItAndAllowsRetry() = runBlocking {
        var candidate = ""
        val entered = CompletableDeferred<Unit>()
        val job = launch { gate.execute(false, interval) { candidate = "verified metadata"; entered.complete(Unit); awaitCancellation() } }
        entered.await(); job.cancelAndJoin(); now += 6_000
        assertTrue(gate.execute(false, interval) { assertEquals("verified metadata", candidate) })
    }

    @Test fun successfulEmptyCheckKeepsIntervalButManualCheckWorks() = runBlocking {
        assertTrue(gate.execute(false, interval) {})
        now += 60_000
        assertFalse(gate.execute(false, interval) { fail("must not request again") })
        assertTrue(gate.execute(true, interval) {})
    }

    @Test fun transientErrorsBackOffWithoutDelayingForSixHours() = runBlocking {
        repeat(2) { n ->
            try { gate.execute(false, interval) { throw java.io.IOException("offline") } } catch (_: java.io.IOException) {}
            assertEquals(n+1, history.failures)
            assertFalse(gate.execute(false, interval) { fail("backoff") })
            now = history.retryAt
        }
        assertTrue(gate.execute(false, interval) {})
        assertEquals(0, history.failures)
    }

    @Test fun serverLimitAlsoBoundsManualRetry() = runBlocking {
        class Limited : Exception(), RetryDelay { override val retryAfterMillis = 900_000L }
        try { gate.execute(false, interval) { throw Limited() } } catch (_: Limited) {}
        now += 60_000
        assertFalse(gate.execute(true, interval) { fail("server backoff") })
        now = history.serverRetryAt
        assertTrue(gate.execute(true, interval) {})
    }

    @Test fun clockRollbackCannotDisableChecksForDays() = runBlocking {
        gate.execute(false, interval) {}; now -= 86_400_000
        assertTrue(gate.execute(false, interval) {})
    }

    @Test fun retryHeadersUseLongestValidServerDeadline() {
        assertEquals(120_000L, retryDelay("120", null, now))
        assertEquals(0L, retryDelay("0", null, now))
        assertEquals(300_000L, retryDelay("120", ((now+300_000)/1000).toString(), now))
        assertEquals(900_000L, retryDelay("garbage", "garbage", now))
        assertEquals(86_400_000L, retryDelay(null, ((now+172_800_000L)/1000).toString(), now))
        assertEquals(900_000L, retryDelay(null, Long.MAX_VALUE.toString(), now))
    }
}
