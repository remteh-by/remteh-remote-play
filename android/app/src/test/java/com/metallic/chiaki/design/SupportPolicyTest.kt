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
