package com.metallic.chiaki.design

data class SupportNudge(val eligible: Boolean = false, val shows: Int = 0,
    val nextAt: Long = 0, val disabled: Boolean = false)

/** Pure policy: first clean 10-minute session, at most three idle reminders. */
object SupportPolicy {
    const val LATER_MS = 14L * 24 * 60 * 60 * 1000
    fun complete(state: SupportNudge, seconds: Long, clean: Boolean) =
        if (clean && seconds >= 600 && !state.eligible) state.copy(eligible = true) else state
    fun due(state: SupportNudge, now: Long) = state.eligible && !state.disabled && state.shows < 3 && now >= state.nextAt
    fun shown(state: SupportNudge) = state.copy(shows = (state.shows + 1).coerceAtMost(3))
    fun later(state: SupportNudge, now: Long) = state.copy(nextAt = now + LATER_MS)
}
