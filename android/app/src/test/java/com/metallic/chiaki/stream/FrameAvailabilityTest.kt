package com.metallic.chiaki.stream

import org.junit.Assert.assertEquals
import org.junit.Test

class FrameAvailabilityTest {
    @Test fun notificationDuringTextureUpdateIsConsumedByNextDraw() {
        val frames = FrameAvailability()
        var updates = 0
        frames.signal()
        frames.consume {
            updates++
            // SurfaceTexture may notify on another thread before updateTexImage returns.
            val producer = Thread { frames.signal() }
            producer.start()
            producer.join()
        }
        assertEquals(1, updates)
        frames.consume { updates++ }
        assertEquals(2, updates)
        frames.consume { updates++ }
        assertEquals(2, updates)
    }

    @Test fun idleDrawsDoNotUpdateAndPendingFramesMayCoalesce() {
        val frames = FrameAvailability()
        var updates = 0
        frames.consume { updates++ }
        assertEquals(0, updates)
        frames.signal()
        frames.signal()
        frames.consume { updates++ }
        assertEquals(1, updates)
    }
}
