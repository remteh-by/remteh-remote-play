// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL

package com.metallic.chiaki.stream

import androidx.activity.addCallback
import android.animation.Animator
import android.animation.AnimatorListenerAdapter
import android.app.AlertDialog
import android.graphics.Matrix
import android.os.*
import android.view.*
import android.widget.EditText
import com.metallic.chiaki.design.DeckivoActivity
import androidx.core.content.edit
import androidx.core.view.isGone
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.*
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.metallic.chiaki.R
import com.metallic.chiaki.common.Preferences
import com.metallic.chiaki.common.ext.viewModelFactory
import com.metallic.chiaki.databinding.ActivityStreamBinding
import com.metallic.chiaki.lib.ConnectInfo
import com.metallic.chiaki.lib.ConnectVideoProfile
import com.metallic.chiaki.session.*
import com.metallic.chiaki.touchcontrols.DefaultTouchControlsFragment
import com.metallic.chiaki.touchcontrols.TouchControlsFragment
import io.reactivex.disposables.CompositeDisposable
import io.reactivex.rxkotlin.addTo
import kotlin.math.min

private sealed class DialogContents
private object StreamQuitDialog: DialogContents()
private object CreateErrorDialog: DialogContents()
private object PinRequestDialog: DialogContents()

class StreamActivity : DeckivoActivity(), View.OnSystemUiVisibilityChangeListener
{
    companion object
    {
        const val EXTRA_CONNECT_INFO = "connect_info"
        const val EXTRA_SUPPORT_COMPLETED = "deckivo_clean_long_session"
        private const val HIDE_UI_TIMEOUT_MS = 2000L
    }

    private lateinit var viewModel: StreamViewModel
    private lateinit var binding: ActivityStreamBinding

    private val uiVisibilityHandler = Handler()

    override fun onCreate(savedInstanceState: Bundle?)
    {
        super.onCreate(savedInstanceState)

        val connectInfo = intent.getParcelableExtra<ConnectInfo>(EXTRA_CONNECT_INFO)
        if(connectInfo == null)
        {
            finish()
            return
        }

        viewModel = ViewModelProvider(this, viewModelFactory {
            StreamViewModel(application, connectInfo)
        })[StreamViewModel::class.java]

        viewModel.input.observe(this)

        binding = ActivityStreamBinding.inflate(layoutInflater)
        setContentView(binding.root)
        window.decorView.setOnSystemUiVisibilityChangeListener(this)
        setupQuickButtons()
        setupKeyboardMouse()
        onBackPressedDispatcher.addCallback(this) { viewModel.requestUserExit(); finish() }

        viewModel.onScreenControlsEnabled.observe(this, Observer {
            if(binding.onScreenControlsSwitch.isChecked != it)
                binding.onScreenControlsSwitch.isChecked = it
        })
        binding.onScreenControlsSwitch.setOnCheckedChangeListener { _, isChecked ->
            viewModel.setOnScreenControlsEnabled(isChecked)
            showOverlay()
        }


        binding.displayModeToggle.addOnButtonCheckedListener { _, _, _ ->
            adjustStreamViewAspect()
            showOverlay()
        }

// Setup video output based on debanding preference
        setupVideoOutput()

        val prefs = Preferences(this)
        if (prefs.touchscreenTouchpadEnabled) {
            binding.streamTouchpadView.visibility = View.VISIBLE
            binding.streamTouchpadView.controllerState
                .subscribe {
                    lastStreamTouchpadControllerState = it
                    updateCombinedTouchState()
                }
                .addTo(controlsDisposable)
        }

        viewModel.session.state.observe(this, Observer { this.stateChanged(it) })
        adjustStreamViewAspect()

        if(Preferences(this).rumbleEnabled)
        {
            val vibrator = getSystemService(VIBRATOR_SERVICE) as Vibrator
            viewModel.session.rumbleState.observe(this, Observer {
                val amplitude = min(255, (it.left.toInt() + it.right.toInt()) / 2)
                vibrator.cancel()
                if(amplitude == 0)
                    return@Observer
                vibrator.vibrate(VibrationEffect.createOneShot(1000, amplitude))
            })
        }
    }

    private var debandRenderer: DebandRenderer? = null

    private fun setupVideoOutput() {
        val prefs = Preferences(this)
        viewModel.session.detachSurface()

        if (prefs.debandingEnabled) {
            // Use GLSurfaceView with debanding shader
            binding.surfaceView.visibility = View.GONE
            binding.debandSurfaceView.visibility = View.VISIBLE

            debandRenderer = DebandRenderer { surface ->
                viewModel.session.attachToSurface(surface)
            }

            binding.debandSurfaceView.setEGLContextClientVersion(3)
            binding.debandSurfaceView.setEGLConfigChooser(8, 8, 8, 8, 0, 0)
            binding.debandSurfaceView.holder.setFormat(android.graphics.PixelFormat.RGBA_8888)
            binding.debandSurfaceView.setRenderer(debandRenderer)
            debandRenderer!!.sharpness = prefs.sharpnessIntensity
            binding.debandSurfaceView.renderMode = android.opengl.GLSurfaceView.RENDERMODE_CONTINUOUSLY
        } else {
            // Use standard SurfaceView (no shader processing)
            binding.surfaceView.visibility = View.VISIBLE
            binding.debandSurfaceView.visibility = View.GONE
            viewModel.session.attachToSurfaceView(binding.surfaceView)
        }
    }

    private val quickControllerState = com.metallic.chiaki.lib.ControllerState()
    private fun setupQuickButtons() {
        listOf(binding.quickPsButton to com.metallic.chiaki.lib.ControllerState.BUTTON_PS,
               binding.quickTouchButton to com.metallic.chiaki.lib.ControllerState.BUTTON_TOUCHPAD).forEach { (button, mask) ->
            var touchInProgress = false
            button.setOnClickListener {
                // Accessibility clicks have no touch down/up events.
                if (!touchInProgress) {
                    quickControllerState.buttons = quickControllerState.buttons or mask
                    updateCombinedTouchState()
                    uiVisibilityHandler.postDelayed({
                        quickControllerState.buttons = quickControllerState.buttons and mask.inv()
                        updateCombinedTouchState()
                    }, 100L)
                    showOverlay()
                }
            }
            button.setOnTouchListener { v, event ->
                when (event.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        touchInProgress = true
                        v.isPressed = true
                        uiVisibilityHandler.removeCallbacks(hideSystemUIRunnable)
                        quickControllerState.buttons = quickControllerState.buttons or mask
                    }
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                        quickControllerState.buttons = quickControllerState.buttons and mask.inv()
                        v.isPressed = false
                        if (event.actionMasked == MotionEvent.ACTION_UP) v.performClick()
                        touchInProgress = false
                        showOverlay()
                    }
                }
                updateCombinedTouchState()
                true
            }
        }
    }

    private var lastFragmentControllerState = com.metallic.chiaki.lib.ControllerState()
    private var lastStreamTouchpadControllerState = com.metallic.chiaki.lib.ControllerState()

    private fun updateCombinedTouchState() {
        viewModel.input.touchControllerState = lastFragmentControllerState or lastStreamTouchpadControllerState or quickControllerState or keyboardMouse.state(SystemClock.uptimeMillis())
    }

    private val controlsDisposable = CompositeDisposable()

    override fun onAttachFragment(fragment: Fragment)
    {
        super.onAttachFragment(fragment)
        if(fragment is TouchControlsFragment)
        {
            fragment.controllerState
                .subscribe {
                    lastFragmentControllerState = it
                    updateCombinedTouchState()
                }
                .addTo(controlsDisposable)
            fragment.onScreenControlsEnabled = viewModel.onScreenControlsEnabled
        }
    }

    override fun onResume()
    {
        super.onResume()
        hideSystemUI()
        if (Preferences(this).debandingEnabled) {
            binding.debandSurfaceView.onResume()
        }
        viewModel.session.resume()
    }

    override fun onPause()
    {
        super.onPause()
        uiVisibilityHandler.removeCallbacksAndMessages(null)
        releaseKeyboardMouse()
        quickControllerState.buttons = 0U
        updateCombinedTouchState()
        if (Preferences(this).debandingEnabled) {
            binding.debandSurfaceView.onPause()
        }
        viewModel.session.pause()
    }

    override fun finish() {
        if (!isFinishing) {
            val completed = ::viewModel.isInitialized && viewModel.takeSupportResult()
            setResult(RESULT_OK, android.content.Intent().putExtra(EXTRA_SUPPORT_COMPLETED, completed))
        }
        super.finish()
    }

    override fun onDestroy()
    {
        super.onDestroy()
        debandRenderer?.release()
        controlsDisposable.dispose()
    }

    private fun reconnect()
    {
        viewModel.session.shutdown()
        viewModel.session.resume()
    }

    private val hideSystemUIRunnable = Runnable { hideSystemUI() }

    override fun onSystemUiVisibilityChange(visibility: Int)
    {
        if(visibility and View.SYSTEM_UI_FLAG_FULLSCREEN == 0)
            showOverlay()
        else
            hideOverlay()
    }

    private fun showOverlay()
    {
        binding.overlay.animate().setListener(null).cancel()
        binding.overlay.isVisible = true
        binding.overlay.animate()
            .alpha(1.0f)
            .setListener(object: AnimatorListenerAdapter()
            {
                override fun onAnimationEnd(animation: Animator)
                {
                    binding.overlay.alpha = 1.0f
                }
            })
        uiVisibilityHandler.removeCallbacks(hideSystemUIRunnable)
        uiVisibilityHandler.postDelayed(hideSystemUIRunnable, HIDE_UI_TIMEOUT_MS)
    }

    private fun hideOverlay()
    {
        uiVisibilityHandler.removeCallbacks(hideSystemUIRunnable)
        quickControllerState.buttons = 0U
        updateCombinedTouchState()
        binding.overlay.animate().setListener(null).cancel()
        binding.overlay.animate()
            .alpha(0.0f)
            .setListener(object: AnimatorListenerAdapter()
            {
                override fun onAnimationEnd(animation: Animator)
                {
                    binding.overlay.isGone = true
                }
            })
    }

    override fun onWindowFocusChanged(hasFocus: Boolean)
    {
        super.onWindowFocusChanged(hasFocus)
        if(hasFocus) hideSystemUI() else if(::binding.isInitialized) releaseKeyboardMouse()
    }

    private fun hideSystemUI()
    {
        window.decorView.systemUiVisibility = (View.SYSTEM_UI_FLAG_IMMERSIVE
                or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_FULLSCREEN)
    }

    private var dialogContents: DialogContents? = null
    private var dialog: AlertDialog? = null
        set(value)
        {
            field = value
            if(value == null)
                dialogContents = null
        }

    private fun stateChanged(state: StreamState)
    {
        binding.progressBar.visibility = if(state == StreamStateConnecting) View.VISIBLE else View.GONE

        when(state)
        {
            is StreamStateQuit ->
            {
                if(dialogContents != StreamQuitDialog)
                {
                    if(state.reason.isError)
                    {
                        dialog?.dismiss()
                        val reasonStr = state.reasonString
                        val dialog = MaterialAlertDialogBuilder(this)
                            .setMessage(getString(R.string.alert_message_session_quit, state.reason.toString())
                                    + (if(reasonStr != null) "\n$reasonStr" else ""))
                            .setPositiveButton(R.string.action_reconnect) { _, _ ->
                                dialog = null
                                reconnect()
                            }
                            .setOnCancelListener {
                                dialog = null
                                finish()
                            }
                            .setNegativeButton(R.string.action_quit_session) { _, _ ->
                                dialog = null
                                finish()
                            }
                            .create()
                        dialogContents = StreamQuitDialog
                        dialog.show()
                    }
                    else
                        finish()
                }
            }

            is StreamStateCreateError ->
            {
                if(dialogContents != CreateErrorDialog)
                {
                    dialog?.dismiss()
                    val dialog = MaterialAlertDialogBuilder(this)
                        .setMessage(getString(R.string.alert_message_session_create_error, state.error.errorCode.toString()))
                        .setOnDismissListener {
                            dialog = null
                            finish()
                        }
                        .setNegativeButton(R.string.action_quit_session) { _, _ -> }
                        .create()
                    dialogContents = CreateErrorDialog
                    dialog.show()
                }
            }

            is StreamStateLoginPinRequest ->
            {
                if(dialogContents != PinRequestDialog)
                {
                    dialog?.dismiss()

                    val view = layoutInflater.inflate(R.layout.dialog_login_pin, null)
                    val pinEditText = view.findViewById<EditText>(R.id.pinEditText)

                    val dialog = MaterialAlertDialogBuilder(this)
                        .setMessage(
                            if(state.pinIncorrect)
                                R.string.alert_message_login_pin_request_incorrect
                            else
                                R.string.alert_message_login_pin_request)
                        .setView(view)
                        .setPositiveButton(R.string.action_login_pin_connect) { _, _ ->
                            dialog = null
                            viewModel.session.setLoginPin(pinEditText.text.toString())
                        }
                        .setOnCancelListener {
                            dialog = null
                            finish()
                        }
                        .setNegativeButton(R.string.action_quit_session) { _, _ ->
                            dialog = null
                            finish()
                        }
                        .create()
                    dialogContents = PinRequestDialog
                    dialog.show()
                }
            }
            // These states don't need special handling
            StreamStateIdle, StreamStateConnecting, StreamStateConnected -> { }
        }
    }

    private fun adjustTextureViewAspect(textureView: TextureView)
    {
        val trans = TextureViewTransform(viewModel.session.connectInfo.videoProfile, textureView)
        val resolution = trans.resolutionFor(TransformMode.fromButton(binding.displayModeToggle.checkedButtonId))
        Matrix().also {
            textureView.getTransform(it)
            it.setScale(resolution.width / trans.viewWidth, resolution.height / trans.viewHeight)
            it.postTranslate((trans.viewWidth - resolution.width) * 0.5f, (trans.viewHeight - resolution.height) * 0.5f)
            textureView.setTransform(it)
        }
    }

    private fun adjustSurfaceViewAspect()
    {
        val videoProfile = viewModel.session.connectInfo.videoProfile
        binding.aspectRatioLayout.aspectRatio = videoProfile.width.toFloat() / videoProfile.height.toFloat()
        binding.aspectRatioLayout.mode = TransformMode.fromButton(binding.displayModeToggle.checkedButtonId)
    }

    private fun adjustStreamViewAspect() = adjustSurfaceViewAspect()

    private val keyboardMouse=KeyboardMouseState()
    private var keyboardCaptured=false
    private val keyboardTick=object: Runnable { override fun run() { if(keyboardCaptured) { updateCombinedTouchState();uiVisibilityHandler.postDelayed(this,16) } } }
    private fun setupKeyboardMouse() {
        binding.mainStreamLayout.isFocusableInTouchMode=true
        binding.mainStreamLayout.onCaptureLost={releaseKeyboardMouse()}
        binding.keyboardMouseButton.setOnClickListener { if(keyboardCaptured) releaseKeyboardMouse() else captureKeyboardMouse() }
        binding.keyboardMouseButton.setOnLongClickListener {
            releaseKeyboardMouse()
            val slider=com.google.android.material.slider.Slider(this).apply { valueFrom=.001f;valueTo=.2f;value=keyboardMouse.sensitivity }
            val invert=android.widget.CheckBox(this).apply { text=getString(R.string.dv_invert_mouse_y);isChecked=keyboardMouse.invertY }
            val column=android.widget.LinearLayout(this).apply { orientation=android.widget.LinearLayout.VERTICAL;setPadding(24,20,24,20);addView(slider);addView(invert) }
            MaterialAlertDialogBuilder(this).setTitle(R.string.dv_mouse_sensitivity).setView(column).setMessage(R.string.dv_keyboard_help).setPositiveButton(android.R.string.ok) { _,_ ->
                keyboardMouse.sensitivity=slider.value;keyboardMouse.invertY=invert.isChecked
                getSharedPreferences("deckivo_input",MODE_PRIVATE).edit { putFloat("sensitivity",slider.value);putBoolean("invert_y",invert.isChecked) }
            }.setNegativeButton(android.R.string.cancel,null).show()
            true
        }
        val input=getSharedPreferences("deckivo_input",MODE_PRIVATE)
        keyboardMouse.sensitivity=input.getFloat("sensitivity",.025f);keyboardMouse.invertY=input.getBoolean("invert_y",false)
        binding.mainStreamLayout.setOnCapturedPointerListener { _,event ->
            if(!keyboardCaptured) return@setOnCapturedPointerListener false
            if(event.actionMasked==MotionEvent.ACTION_MOVE) keyboardMouse.move(event.x,event.y,SystemClock.uptimeMillis())
            keyboardMouse.leftMouse=event.buttonState and MotionEvent.BUTTON_PRIMARY!=0
            keyboardMouse.rightMouse=event.buttonState and MotionEvent.BUTTON_SECONDARY!=0
            keyboardMouse.middleMouse=event.buttonState and MotionEvent.BUTTON_TERTIARY!=0
            updateCombinedTouchState();true
        }
    }
    private fun captureKeyboardMouse() {
        if(!hasWindowFocus()) return
        keyboardMouse.reset();keyboardCaptured=true
        binding.mainStreamLayout.requestFocus();binding.mainStreamLayout.requestPointerCapture()
        uiVisibilityHandler.removeCallbacks(keyboardTick);uiVisibilityHandler.post(keyboardTick)
        android.widget.Toast.makeText(this,R.string.dv_keyboard_help,android.widget.Toast.LENGTH_LONG).show()
    }
    private fun releaseKeyboardMouse() {
        keyboardCaptured=false;uiVisibilityHandler.removeCallbacks(keyboardTick);keyboardMouse.reset()
        if(::binding.isInitialized) { binding.mainStreamLayout.releasePointerCapture();updateCombinedTouchState() }
    }
    private fun keyboardName(key: Int): String = when(key) {
        KeyEvent.KEYCODE_SPACE -> "Space";KeyEvent.KEYCODE_CTRL_LEFT,KeyEvent.KEYCODE_CTRL_RIGHT -> "Ctrl"
        KeyEvent.KEYCODE_ALT_LEFT,KeyEvent.KEYCODE_ALT_RIGHT -> "Alt";KeyEvent.KEYCODE_ENTER -> "Return"
        KeyEvent.KEYCODE_TAB -> "Tab";KeyEvent.KEYCODE_F2 -> "F2";KeyEvent.KEYCODE_1 -> "1"
        KeyEvent.KEYCODE_DPAD_UP -> "Up";KeyEvent.KEYCODE_DPAD_DOWN -> "Down";KeyEvent.KEYCODE_DPAD_LEFT -> "Left";KeyEvent.KEYCODE_DPAD_RIGHT -> "Right"
        in KeyEvent.KEYCODE_A..KeyEvent.KEYCODE_Z -> ('A'.code+key-KeyEvent.KEYCODE_A).toChar().toString()
        else -> ""
    }
    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        val keyboard=event.source and InputDevice.SOURCE_KEYBOARD==InputDevice.SOURCE_KEYBOARD
        if(keyboard && event.keyCode==KeyEvent.KEYCODE_F8) {
            if(event.action==KeyEvent.ACTION_DOWN && event.repeatCount==0) { if(keyboardCaptured) releaseKeyboardMouse() else captureKeyboardMouse() };return true
        }
        if(keyboardCaptured && keyboard) {
            if(event.keyCode==KeyEvent.KEYCODE_ESCAPE) { releaseKeyboardMouse();return true }
            if(keyboardMouse.key(keyboardName(event.keyCode),event.action==KeyEvent.ACTION_DOWN)) { updateCombinedTouchState();return true }
        }
        return viewModel.input.dispatchKeyEvent(event) || super.dispatchKeyEvent(event)
    }
    override fun onGenericMotionEvent(event: MotionEvent) = viewModel.input.onGenericMotionEvent(event) || super.onGenericMotionEvent(event)

}

enum class TransformMode
{
    FIT,
    STRETCH,
    ZOOM;

    companion object
    {
        fun fromButton(displayModeButtonId: Int)
            = when (displayModeButtonId)
            {
                R.id.display_mode_stretch_button -> STRETCH
                R.id.display_mode_zoom_button -> ZOOM
                else -> FIT
            }
    }
}

class TextureViewTransform(private val videoProfile: ConnectVideoProfile, private val textureView: TextureView)
{
    private val contentWidth : Float get() = videoProfile.width.toFloat()
    private val contentHeight : Float get() = videoProfile.height.toFloat()
    val viewWidth : Float get() = textureView.width.toFloat()
    val viewHeight : Float get() = textureView.height.toFloat()
    private val contentAspect : Float get() =  contentHeight / contentWidth

    fun resolutionFor(mode: TransformMode): Resolution
        = when(mode)
        {
            TransformMode.STRETCH -> strechedResolution
            TransformMode.ZOOM -> zoomedResolution
            TransformMode.FIT -> normalResolution
        }

    private val strechedResolution get() = Resolution(viewWidth, viewHeight)

    private val zoomedResolution get() =
        if(viewHeight > viewWidth * contentAspect)
        {
            val zoomFactor = viewHeight / contentHeight
            Resolution(contentWidth * zoomFactor, viewHeight)
        }
        else
        {
            val zoomFactor = viewWidth / contentWidth
            Resolution(viewWidth, contentHeight * zoomFactor)
        }

    private val normalResolution get() =
        if(viewHeight > viewWidth * contentAspect)
            Resolution(viewWidth, viewWidth * contentAspect)
        else
            Resolution(viewHeight / contentAspect, viewHeight)
}


data class Resolution(val width: Float, val height: Float)
