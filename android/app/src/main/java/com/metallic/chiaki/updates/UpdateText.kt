package com.metallic.chiaki.updates

import android.content.Context
import androidx.annotation.StringRes
import com.metallic.chiaki.R

/** State carries resource identity and values, never a translated Context string. */
data class UpdateText(@StringRes val resource: Int, val arguments: List<Any> = emptyList()) {
    fun render(context: Context): String = context.getString(resource, *arguments.toTypedArray())
}

class UpdateFailure(val text: UpdateText, override val retryAfterMillis: Long? = null) : IllegalStateException(), RetryDelay

fun updateFailure(error: Exception): UpdateText = when (error) {
    is UpdateFailure -> error.text
    is java.net.UnknownHostException -> UpdateText(R.string.dv_up_no_server)
    is java.net.SocketTimeoutException -> UpdateText(R.string.dv_up_timeout)
    is IllegalArgumentException, is IllegalStateException -> UpdateText(R.string.dv_up_verify_failed)
    else -> UpdateText(R.string.dv_up_check_failed)
}
