package com.metallic.chiaki.design

import org.junit.Assert.*
import org.junit.Test

class SupportPolicyTest {
    @Test fun onlyCleanTenMinuteSessionQualifies() {
        assertFalse(SupportPolicy.due(SupportPolicy.complete(SupportNudge(), 600, false), 0))
        assertFalse(SupportPolicy.due(SupportPolicy.complete(SupportNudge(), 599, true), 0))
        assertTrue(SupportPolicy.due(SupportPolicy.complete(SupportNudge(), 600, true), 0))
    }
    @Test fun laterWaitsFourteenDaysAndStopsAfterThree() {
        var state = SupportPolicy.complete(SupportNudge(), 600, true)
        repeat(3) {
            state = SupportPolicy.shown(state)
            state = SupportPolicy.later(state, it * SupportPolicy.LATER_MS)
            assertFalse(SupportPolicy.due(state, state.nextAt - 1))
        }
        assertFalse(SupportPolicy.due(state, Long.MAX_VALUE))
        assertFalse(SupportPolicy.due(SupportNudge(eligible = true, disabled = true), Long.MAX_VALUE))
    }
}

class SupportResultBoundaryTest {
    @org.junit.Test fun currentSessionOnlyAndOneShot() {
        val stale = SupportPolicy.complete(SupportNudge(), 900, true)
        for ((seconds, clean) in listOf(0L to false, 20L to false, 20L to true, 599L to true, 900L to false)) {
            org.junit.Assert.assertFalse(SupportPolicy.consume(SupportPolicy.complete(stale, seconds, clean), Long.MAX_VALUE).second)
        }
        val (consumed, show) = SupportPolicy.consume(SupportPolicy.complete(stale, 600, true), Long.MAX_VALUE)
        org.junit.Assert.assertTrue(show)
        org.junit.Assert.assertFalse(SupportPolicy.consume(consumed, Long.MAX_VALUE).second)
        val completion = SupportSessionCompletion()
        org.junit.Assert.assertTrue(completion.consume(600, true))
        org.junit.Assert.assertFalse(completion.consume(900, true))
    }
    @org.junit.Test fun suppressedOrCooldownResultCannotAppearOnNextResume() {
        val pending = SupportPolicy.complete(SupportNudge(), 600, true)
        val (consumed, show) = SupportPolicy.consume(pending, 0, false)
        org.junit.Assert.assertFalse(show)
        org.junit.Assert.assertFalse(SupportPolicy.due(consumed, Long.MAX_VALUE))
        val later = SupportPolicy.later(pending, 0)
        org.junit.Assert.assertFalse(SupportPolicy.due(SupportPolicy.complete(later, 600, true), SupportPolicy.LATER_MS - 1))
        org.junit.Assert.assertTrue(SupportPolicy.due(SupportPolicy.complete(later, 600, true), SupportPolicy.LATER_MS))
    }
}
