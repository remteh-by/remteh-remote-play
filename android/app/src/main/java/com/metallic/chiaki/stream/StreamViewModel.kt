// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL

package com.metallic.chiaki.stream

import android.app.Application
import android.content.Context
import androidx.lifecycle.*
import com.metallic.chiaki.common.LogManager
import com.metallic.chiaki.session.StreamSession
import com.metallic.chiaki.common.Preferences
import com.metallic.chiaki.lib.*
import com.metallic.chiaki.session.StreamInput

class StreamViewModel(val application: Application, val connectInfo: ConnectInfo): ViewModel()
{
    val preferences = Preferences(application)
    val logManager = LogManager(application)

    val input = StreamInput(application, preferences)
    val session = StreamSession(connectInfo, logManager, preferences.logVerbose, input)
    private var userExitRequested = false
    fun requestUserExit() { userExitRequested = session.state.value is com.metallic.chiaki.session.StreamStateConnected }
    private var historyStarted = 0L
    private var historyMonotonic = 0L
    private val supportCompletion = com.metallic.chiaki.design.SupportSessionCompletion()
    fun takeSupportResult(): Boolean = supportCompletion.consume(
        if (historyStarted == 0L) 0 else (android.os.SystemClock.elapsedRealtime()-historyMonotonic)/1000,
        userExitRequested && session.state.value is com.metallic.chiaki.session.StreamStateConnected)
    private fun finishHistory() {
        if(historyStarted == 0L) return
        com.metallic.chiaki.design.SessionHistory.append(application,historyStarted,
            (android.os.SystemClock.elapsedRealtime()-historyMonotonic)/1000,
            preferences.resolution.value + " · " + preferences.fps.value + " FPS")
        userExitRequested=false
        historyStarted=0L
    }
    private val historyObserver=Observer<com.metallic.chiaki.session.StreamState> { state ->
        if(state is com.metallic.chiaki.session.StreamStateConnected) {
            if(historyStarted==0L) { historyStarted=System.currentTimeMillis();historyMonotonic=android.os.SystemClock.elapsedRealtime() }
        } else if(state is com.metallic.chiaki.session.StreamStateIdle || state is com.metallic.chiaki.session.StreamStateQuit) finishHistory()
    }
    init { session.state.observeForever(historyObserver) }

    private var _onScreenControlsEnabled = MutableLiveData<Boolean>(preferences.onScreenControlsEnabled)
    val onScreenControlsEnabled: LiveData<Boolean> get() = _onScreenControlsEnabled


    override fun onCleared()
    {
        super.onCleared()
        finishHistory();session.state.removeObserver(historyObserver)
        session.shutdown()
    }

    fun setOnScreenControlsEnabled(enabled: Boolean)
    {
        preferences.onScreenControlsEnabled = enabled
        _onScreenControlsEnabled.value = enabled
    }

}
