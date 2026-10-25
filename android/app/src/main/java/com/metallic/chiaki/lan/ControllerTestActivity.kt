// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.lan

import com.metallic.chiaki.R
import android.os.Bundle
import com.metallic.chiaki.design.DeckivoUi
import android.view.InputDevice
import android.view.KeyEvent
import android.view.MotionEvent
import android.widget.*
import com.metallic.chiaki.design.DeckivoActivity
import com.metallic.chiaki.common.Preferences

/** Calibrate by physical position instead of guessing the Switchroot key layout. */
class ControllerTestActivity : DeckivoActivity() {
    private lateinit var status: TextView
    private var step = -1
    private val captured = mutableListOf<Int>()
    private val positions by lazy { listOf(getString(R.string.dv_bottom_button), getString(R.string.dv_right_button), getString(R.string.dv_left_button), getString(R.string.dv_top_button)) }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        title = getString(R.string.dv_controller)
        val root = DeckivoUi.screen(this, getString(R.string.dv_controller), getString(R.string.dv_controller_intro))
        val layout = DeckivoUi.section(root, getString(R.string.dv_connected_devices))
        val names = InputDevice.getDeviceIds().map { InputDevice.getDevice(it) }.filterNotNull()
            .filter { it.sources and InputDevice.SOURCE_GAMEPAD == InputDevice.SOURCE_GAMEPAD || it.sources and InputDevice.SOURCE_JOYSTICK == InputDevice.SOURCE_JOYSTICK }
            .joinToString { it.name }
        DeckivoUi.label(layout, names.ifEmpty { getString(R.string.dv_no_controller) }, 17f, true)
        DeckivoUi.label(layout, getString(R.string.dv_controller_help))
        status = DeckivoUi.label(DeckivoUi.section(root, getString(R.string.dv_input_test)), getString(R.string.dv_waiting_input), 18f, true)
        val setup = DeckivoUi.section(root, getString(R.string.dv_button_layout))
        DeckivoUi.button(setup, getString(R.string.dv_calibrate), true) {
            captured.clear(); step = 0; status.text = getString(R.string.dv_press) + positions[step]
        }
        DeckivoUi.button(setup, getString(R.string.dv_cancel_calibration)) { step = -1; captured.clear(); status.text = getString(R.string.dv_changes_cancelled) }

    }
    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        val gamepad = event.source and InputDevice.SOURCE_GAMEPAD == InputDevice.SOURCE_GAMEPAD ||
            event.keyCode in KeyEvent.KEYCODE_BUTTON_A..KeyEvent.KEYCODE_BUTTON_MODE
        if (gamepad && ::status.isInitialized) {
            if (event.action == KeyEvent.ACTION_UP && step >= 0) {
                if (event.keyCode in captured) { status.text = "Button already mapped. Press ${positions[step]}"; return true }
                captured.add(event.keyCode); step++
                if (step == positions.size) {
                    Preferences(this).apply { mappingCross = captured[0]; mappingCircle = captured[1]; mappingSquare = captured[2]; mappingTriangle = captured[3] }
                    step = -1; status.text = getString(R.string.dv_layout_saved)
                } else status.text = "Press ${positions[step]}"
            } else if (step < 0) status.text = "${event.device?.name}: ${KeyEvent.keyCodeToString(event.keyCode)} · ${if(event.action == KeyEvent.ACTION_DOWN) getString(R.string.dv_pressed) else getString(R.string.dv_released)}"
            return true
        }
        return super.dispatchKeyEvent(event)
    }
    override fun onGenericMotionEvent(event: MotionEvent): Boolean {
        if (event.source and InputDevice.SOURCE_JOYSTICK == InputDevice.SOURCE_JOYSTICK) {
            if (step < 0) status.text = "Left: %.2f / %.2f · Right: %.2f / %.2f · ZL/ZR: %.2f / %.2f".format(
                event.getAxisValue(MotionEvent.AXIS_X), event.getAxisValue(MotionEvent.AXIS_Y),
                event.getAxisValue(MotionEvent.AXIS_Z), event.getAxisValue(MotionEvent.AXIS_RZ),
                event.getAxisValue(MotionEvent.AXIS_LTRIGGER), event.getAxisValue(MotionEvent.AXIS_RTRIGGER))
            return true
        }
        return super.onGenericMotionEvent(event)
    }
    override fun onSupportNavigateUp(): Boolean { finish(); return true }
}
