// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.lan

import com.metallic.chiaki.common.Preferences

object SwitchProfile {
    fun apply(prefs: Preferences) {
        prefs.resolution = Preferences.Resolution.RES_720P
        prefs.fps = Preferences.FPS.FPS_60
        prefs.codec = Preferences.Codec.CODEC_H264
        prefs.bitrate = 8000
        prefs.debandingEnabled = false
        prefs.sharpnessIntensity = 0f
        prefs.onScreenControlsEnabled = false
        prefs.touchscreenTouchpadEnabled = true
        prefs.motionEnabled = false // Enable after checking the Switch sensor orientation.
        prefs.logVerbose = false
    }
}
