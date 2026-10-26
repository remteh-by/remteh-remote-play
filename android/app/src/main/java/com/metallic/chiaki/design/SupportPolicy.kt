package com.metallic.chiaki.design

data class SupportNudge(val eligible: Boolean = false, val shows: Int = 0,
    val nextAt: Long = 0, val disabled: Boolean = false)

/** One-shot result of the current clean 10-minute session, at most three reminders. */
object SupportPolicy {
    const val LATER_MS = 14L * 24 * 60 * 60 * 1000
    fun complete(state: SupportNudge, seconds: Long, clean: Boolean) =
        state.copy(eligible = clean && seconds >= 600)
    fun due(state: SupportNudge, now: Long) = state.eligible && !state.disabled && state.shows < 3 && now >= state.nextAt
    fun shown(state: SupportNudge) = state.copy(eligible = false, shows = (state.shows + 1).coerceAtMost(3))
    fun later(state: SupportNudge, now: Long) = state.copy(eligible = false, nextAt = now + LATER_MS)
    fun consume(state: SupportNudge, now: Long, allowed: Boolean = true) =
        Pair(state.copy(eligible = false), allowed && due(state, now))
}

/** Activity recreation/duplicate finish cannot deliver the same result twice. */
class SupportSessionCompletion {
    private var consumed = false
    fun consume(seconds: Long, clean: Boolean): Boolean {
        if (consumed) return false
        consumed = true
        return clean && seconds >= 600
    }
}
