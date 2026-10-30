// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL

package com.metallic.chiaki.session

import android.graphics.SurfaceTexture
import android.util.Log
import android.view.*
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import com.metallic.chiaki.common.LogManager
import com.metallic.chiaki.lib.*

sealed class StreamState
object StreamStateIdle: StreamState()
object StreamStateConnecting: StreamState()
object StreamStateConnected: StreamState()
data class StreamStateCreateError(val error: CreateError): StreamState()
data class StreamStateQuit(val reason: QuitReason, val reasonString: String?): StreamState()
data class StreamStateLoginPinRequest(val pinIncorrect: Boolean): StreamState()

class StreamSession(val connectInfo: ConnectInfo, val logManager: LogManager, val logVerbose: Boolean, val input: StreamInput)
{
	var session: Session? = null
		private set

	private val _state = MutableLiveData<StreamState>(StreamStateIdle)
	val state: LiveData<StreamState> get() = _state
	private val _rumbleState = MutableLiveData<RumbleEvent>(RumbleEvent(0U, 0U))
	val rumbleState: LiveData<RumbleEvent> get() = _rumbleState

	private var surfaceTexture: SurfaceTexture? = null
	private var surface: Surface? = null
	var lastVideoMetrics: LongArray? = null
		private set
	var startedNanos = 0L
		private set

	init
	{
		input.controllerStateChangedCallback = {
			session?.setControllerState(it)
		}
	}

	fun shutdown()
	{
		val oldSession = session
		session = null
		oldSession?.eventCallback = null
		lastVideoMetrics = oldSession?.videoMetrics() ?: lastVideoMetrics
		try {
			oldSession?.stop()
		} finally {
			oldSession?.dispose()
		}
		// The view owns the Surface. Keep it for an in-place reconnect;
		// surfaceDestroyed/detachSurface clear it when the output actually ends.
		_state.value = StreamStateIdle
		//surfaceTexture?.release()
	}

	fun pause()
	{
		shutdown()
	}

	fun resume()
	{
		if(session != null)
			return
		try
		{
			_state.value = StreamStateConnecting
			startedNanos = System.nanoTime(); lastVideoMetrics = null
			val session = Session(connectInfo, logManager.createNewFile().file.absolutePath, logVerbose)
			this.session = session
			session.eventCallback = { event ->
				if (this.session === session) eventCallback(event)
			}
			val surface = surface?.takeIf { it.isValid }
			if(surface != null)
				session.setSurface(surface)
			// Initialize video output before incoming packets can reach the decoder.
			val startResult = session.start()
			if (!startResult.isSuccess) throw CreateError(startResult)
		}
		catch(e: CreateError)
		{
			shutdown()
			_state.value = StreamStateCreateError(e)
		}
	}

	private fun eventCallback(event: Event)
	{
		when(event)
		{
			is ConnectedEvent -> _state.postValue(StreamStateConnected)
			is QuitEvent -> _state.postValue(
				StreamStateQuit(
					event.reason,
					event.reasonString
				)
			)
			is LoginPinRequestEvent -> _state.postValue(
				StreamStateLoginPinRequest(
					event.pinIncorrect
				)
			)
			is RumbleEvent -> _rumbleState.postValue(event)
		}
	}

	fun attachToSurfaceView(surfaceView: SurfaceView)
	{
		surfaceView.holder.addCallback(object: SurfaceHolder.Callback {
			override fun surfaceCreated(holder: SurfaceHolder)
			{
				val surface = holder.surface
				this@StreamSession.surface = surface
				session?.setSurface(surface)
			}

			override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) { }

			override fun surfaceDestroyed(holder: SurfaceHolder)
			{
				this@StreamSession.surface = null
				session?.setSurface(null)
			}
		})
		
		val surface = surfaceView.holder.surface
		if (surface?.isValid == true) {
			this.surface = surface
			session?.setSurface(surface)
		}
	}

	/**
	 * Attach to a custom Surface (e.g., from GLSurfaceView with debanding)
	 */
	fun attachToSurface(surface: Surface)
	{
		this.surface = surface
		session?.setSurface(surface)
	}

	fun detachSurface()
	{
		this.surface = null
		session?.setSurface(null)
	}

	fun attachToTextureView(textureView: TextureView)
	{
		textureView.surfaceTextureListener = object: TextureView.SurfaceTextureListener {
			override fun onSurfaceTextureAvailable(surface: SurfaceTexture, width: Int, height: Int)
			{
				if(surfaceTexture != null)
					return
				surfaceTexture = surface
				this@StreamSession.surface = Surface(surfaceTexture)
				session?.setSurface(Surface(surface))
			}

			override fun onSurfaceTextureDestroyed(surface: SurfaceTexture): Boolean
			{
				// return false if we want to keep the surface texture
				return surfaceTexture == null
			}

			override fun onSurfaceTextureSizeChanged(surface: SurfaceTexture, width: Int, height: Int) { }
			override fun onSurfaceTextureUpdated(surface: SurfaceTexture) {}
		}

		val surfaceTexture = surfaceTexture
		if(surfaceTexture != null)
			textureView.setSurfaceTexture(surfaceTexture)
	}

	fun setLoginPin(pin: String)
	{
		session?.setLoginPin(pin)
	}
}
