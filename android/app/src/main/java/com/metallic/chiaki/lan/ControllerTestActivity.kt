// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.lan

import android.os.Bundle
import android.view.InputDevice
import android.view.KeyEvent
import android.view.MotionEvent
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.metallic.chiaki.common.Preferences

/** Calibrate by physical position instead of guessing the Switchroot key layout. */
class ControllerTestActivity : AppCompatActivity() {
    private lateinit var status: TextView
    private var step = -1
    private val captured = mutableListOf<Int>()
    private val positions = listOf("нижнюю кнопку (× на PS5)", "правую кнопку (○)", "левую кнопку (□)", "верхнюю кнопку (△)")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        title = "Joy-Con: проверка и раскладка"
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        val layout = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(32, 32, 32, 24) }
        val scroll = ScrollView(this).apply { addView(layout) }
        setContentView(scroll)
        SafeInsets.apply(scroll)
        val names = InputDevice.getDeviceIds().map { InputDevice.getDevice(it) }.filterNotNull()
            .filter { it.sources and InputDevice.SOURCE_GAMEPAD == InputDevice.SOURCE_GAMEPAD || it.sources and InputDevice.SOURCE_JOYSTICK == InputDevice.SOURCE_JOYSTICK }
            .joinToString { it.name }
        layout.addView(TextView(this).apply { text = "Контроллеры: ${names.ifEmpty { "пока не обнаружены" }}\nДвигай стики и нажимай кнопки. Plus = Options, Minus = Share; PS и нажатие тачпада доступны на экране игры."; textSize = 18f })
        layout.addView(Button(this).apply { text = "Настроить четыре кнопки по расположению"; setOnClickListener {
            captured.clear(); step = 0; status.text = "Нажми ${positions[step]}"
        } })
        layout.addView(Button(this).apply { text = "Отменить настройку"; setOnClickListener { step = -1; captured.clear(); status.text = "Изменения отменены" } })
        status = TextView(this).apply { textSize = 18f; text = "Ожидаю нажатия…"; layout.addView(this) }
        layout.addView(Button(this).apply { text = "Готово — вернуться"; setOnClickListener { finish() } })
    }
    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        val gamepad = event.source and InputDevice.SOURCE_GAMEPAD == InputDevice.SOURCE_GAMEPAD ||
            event.keyCode in KeyEvent.KEYCODE_BUTTON_A..KeyEvent.KEYCODE_BUTTON_MODE
        if (gamepad && ::status.isInitialized) {
            if (event.action == KeyEvent.ACTION_UP && step >= 0) {
                if (event.keyCode in captured) { status.text = "Эта кнопка уже выбрана. Нажми ${positions[step]}"; return true }
                captured.add(event.keyCode); step++
                if (step == positions.size) {
                    Preferences(this).apply { mappingCross = captured[0]; mappingCircle = captured[1]; mappingSquare = captured[2]; mappingTriangle = captured[3] }
                    step = -1; status.text = "Раскладка сохранена. Снизу — ×, справа — ○, слева — □, сверху — △."
                } else status.text = "Нажми ${positions[step]}"
            } else if (step < 0) status.text = "${event.device?.name}: ${KeyEvent.keyCodeToString(event.keyCode)} · ${if(event.action == KeyEvent.ACTION_DOWN) "нажато" else "отпущено"}"
            return true
        }
        return super.dispatchKeyEvent(event)
    }
    override fun onGenericMotionEvent(event: MotionEvent): Boolean {
        if (event.source and InputDevice.SOURCE_JOYSTICK == InputDevice.SOURCE_JOYSTICK) {
            if (step < 0) status.text = "Левый: %.2f / %.2f · Правый: %.2f / %.2f · ZL/ZR: %.2f / %.2f".format(
                event.getAxisValue(MotionEvent.AXIS_X), event.getAxisValue(MotionEvent.AXIS_Y),
                event.getAxisValue(MotionEvent.AXIS_Z), event.getAxisValue(MotionEvent.AXIS_RZ),
                event.getAxisValue(MotionEvent.AXIS_LTRIGGER), event.getAxisValue(MotionEvent.AXIS_RTRIGGER))
            return true
        }
        return super.onGenericMotionEvent(event)
    }
    override fun onSupportNavigateUp(): Boolean { finish(); return true }
}
