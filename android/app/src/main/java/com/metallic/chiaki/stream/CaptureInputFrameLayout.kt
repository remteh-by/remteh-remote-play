// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.stream
import android.content.Context
import android.util.AttributeSet
import android.widget.FrameLayout
class CaptureInputFrameLayout @JvmOverloads constructor(context: Context,attrs: AttributeSet?=null): FrameLayout(context,attrs) {
    var onCaptureLost: (() -> Unit)? = null
    override fun onPointerCaptureChange(hasCapture: Boolean) { super.onPointerCaptureChange(hasCapture);if(!hasCapture) onCaptureLost?.invoke() }
}
