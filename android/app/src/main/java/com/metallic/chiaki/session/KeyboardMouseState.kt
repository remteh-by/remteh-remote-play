// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.session

import com.metallic.chiaki.lib.ControllerState
import kotlin.math.hypot
import kotlin.math.max

/** Pure, bounded gamepad emulation. Only the focused stream supplies events. */
class KeyboardMouseState {
    val keys = mutableSetOf<String>()
    var sensitivity = .025f
        set(value) { field = if(value.isFinite()) value.coerceIn(.001f,.2f) else .025f }
    var invertY = false
    private var mouseX = 0f
    private var mouseY = 0f
    private var movedAt = Long.MIN_VALUE
    var leftMouse = false
    var rightMouse = false
    var middleMouse = false
    fun reset() { keys.clear();mouseX=0f;mouseY=0f;movedAt=Long.MIN_VALUE;leftMouse=false;rightMouse=false;middleMouse=false }
    fun move(dx: Float,dy: Float,now: Long) {
        if(!dx.isFinite()||!dy.isFinite()) return
        mouseX=(dx*sensitivity).coerceIn(-1f,1f);mouseY=(dy*sensitivity*(if(invertY)-1 else 1)).coerceIn(-1f,1f);movedAt=now
    }
    fun key(name: String,down: Boolean): Boolean {
        if(name !in MAPPING) return false
        if(down) keys.add(name) else keys.remove(name)
        return true
    }
    fun state(now: Long): ControllerState {
        val actions=keys.mapNotNull { MAPPING[it] }.toSet()
        val x=(if("lx+" in actions)1f else 0f)-(if("lx-" in actions)1f else 0f)
        val y=(if("ly+" in actions)1f else 0f)-(if("ly-" in actions)1f else 0f)
        val scale=max(1f,hypot(x,y))
        fun Float.axis()=(this*32767f).toInt().toShort()
        val fresh=movedAt!=Long.MIN_VALUE&&now>=movedAt&&now-movedAt<80
        var buttons=0U
        BUTTONS.forEach { (action,mask) -> if(action in actions) buttons=buttons or mask }
        if(middleMouse) buttons=buttons or ControllerState.BUTTON_R3
        return ControllerState(buttons=buttons,leftX=(x/scale).axis(),leftY=(y/scale).axis(),rightX=(if(fresh)mouseX else 0f).axis(),rightY=(if(fresh)mouseY else 0f).axis(),l2State=if(rightMouse)255U else 0U,r2State=if(leftMouse)255U else 0U)
    }
    companion object {
        val MAPPING=mapOf("W" to "ly-","S" to "ly+","A" to "lx-","D" to "lx+","Space" to "cross","C" to "circle","R" to "square","F" to "triangle","Q" to "l1","E" to "r1","Ctrl" to "l3","Alt" to "r3","Return" to "options","1" to "share","Tab" to "touchpad","F2" to "ps","Up" to "up","Down" to "down","Left" to "left","Right" to "right")
        private val BUTTONS=mapOf("cross" to ControllerState.BUTTON_CROSS,"circle" to ControllerState.BUTTON_MOON,"square" to ControllerState.BUTTON_BOX,"triangle" to ControllerState.BUTTON_PYRAMID,"l1" to ControllerState.BUTTON_L1,"r1" to ControllerState.BUTTON_R1,"l3" to ControllerState.BUTTON_L3,"r3" to ControllerState.BUTTON_R3,"options" to ControllerState.BUTTON_OPTIONS,"share" to ControllerState.BUTTON_SHARE,"touchpad" to ControllerState.BUTTON_TOUCHPAD,"ps" to ControllerState.BUTTON_PS,"up" to ControllerState.BUTTON_DPAD_UP,"down" to ControllerState.BUTTON_DPAD_DOWN,"left" to ControllerState.BUTTON_DPAD_LEFT,"right" to ControllerState.BUTTON_DPAD_RIGHT)
    }
}
