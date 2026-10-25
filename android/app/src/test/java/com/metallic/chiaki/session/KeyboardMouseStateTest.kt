package com.metallic.chiaki.session
import com.metallic.chiaki.lib.ControllerState
import org.junit.Assert.*
import org.junit.Test
import kotlin.math.hypot
class KeyboardMouseStateTest {
    @Test fun diagonalMovementAndOpposites() {
        val s=KeyboardMouseState();s.key("W",true);s.key("D",true)
        val state=s.state(1);assertTrue(hypot(state.leftX.toDouble(),state.leftY.toDouble())<=32768)
        s.key("A",true);assertEquals(0,s.state(1).leftX.toInt())
    }
    @Test fun mouseIsBoundedAndExpires() {
        val s=KeyboardMouseState();s.move(1000f,-1000f,10)
        assertEquals(32767,s.state(20).rightX.toInt());assertEquals(-32767,s.state(20).rightY.toInt())
        assertEquals(0,s.state(91).rightX.toInt())
    }
    @Test fun releaseClearsEveryHeldInput() {
        val s=KeyboardMouseState();s.key("Space",true);s.leftMouse=true;s.rightMouse=true;s.middleMouse=true;s.move(1f,2f,1);s.reset()
        val state=s.state(2);assertEquals(0,state.buttons.toInt());assertEquals(0,state.r2State.toInt());assertEquals(0,state.l2State.toInt());assertEquals(0,state.rightY.toInt())
    }
    @Test fun nonFiniteMouseNeverReachesController() {
        val s=KeyboardMouseState();s.sensitivity=Float.NaN;s.move(Float.POSITIVE_INFINITY,0f,1)
        assertEquals(.025f,s.sensitivity);assertEquals(0,s.state(1).rightX.toInt())
    }
    @Test fun unknownKeysAreNotConsumed() { assertFalse(KeyboardMouseState().key("Escape",true)) }
    @Test fun gamepadButtonsAndMouseTriggersAreSeparate() {
        val s=KeyboardMouseState();s.key("Q",true);s.leftMouse=true
        assertTrue(s.state(1).buttons and ControllerState.BUTTON_L1 != 0U);assertEquals(255,s.state(1).r2State.toInt());assertEquals(0,s.state(1).l2State.toInt())
    }
}
