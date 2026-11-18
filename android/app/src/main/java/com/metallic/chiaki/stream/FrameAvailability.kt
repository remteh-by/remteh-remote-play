// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.stream

import java.util.concurrent.atomic.AtomicBoolean

/** Coalesces notifications without losing one delivered while a texture is updated. */
internal class FrameAvailability {
    private val pending = AtomicBoolean(false)

    fun signal() { pending.set(true) }

    fun consume(updateTexture: () -> Unit) {
        // Clear before the update. A callback during updateTexImage belongs to
        // the next draw and must remain pending, rather than being overwritten.
        if (pending.getAndSet(false)) updateTexture()
    }
}
