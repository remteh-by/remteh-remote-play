package com.metallic.chiaki.design

import android.content.Context
import android.util.AtomicFile
import com.metallic.chiaki.BuildConfig
import com.metallic.chiaki.lib.ConnectVideoProfile
import org.json.JSONObject
import java.io.File

/** Allow-listed aggregate data only: no addresses, keys, accounts or raw logs. */
object StreamDiagnostics {
    fun save(context: Context, profile: ConnectVideoProfile, metrics: LongArray?, started: Long, ended: Long) {
        val safe = snapshot(profile.width, profile.height, profile.maxFPS, metrics, started, ended)
        val file = AtomicFile(File(context.filesDir,"last-stream-diagnostics.json"))
        runCatching {
            val stream = file.startWrite()
            try { stream.write(safe.toString(2).toByteArray()); file.finishWrite(stream) }
            catch (error: Exception) { file.failWrite(stream); throw error }
        }
    }
    fun snapshot(width: Int, height: Int, fps: Int, metrics: LongArray?, started: Long, ended: Long): JSONObject {
        val data = metrics?.takeIf { it.size == 5 && it.all { n -> n >= 0 } }
        val first = data?.get(4)?.takeIf { it in started..ended && it > 0 }
        return JSONObject().put("schema",1).put("appVersion",BuildConfig.VERSION_NAME)
            .put("requested",JSONObject().put("width",width).put("height",height).put("fps",fps))
            .put("decoderApi","MediaCodec").put("decoderName",JSONObject.NULL)
            .put("hardwareAcceleration",JSONObject.NULL).put("actualResolution",JSONObject.NULL)
            .put("inputBuffers",data?.get(0) ?: JSONObject.NULL)
            .put("decodedFrames",data?.get(1) ?: JSONObject.NULL)
            .put("surfaceSubmissions",data?.get(2) ?: JSONObject.NULL)
            .put("receiverLostFrames",data?.get(3) ?: JSONObject.NULL)
            .put("firstDecodedFrameMs",first?.let { (it-started)/1_000_000.0 } ?: JSONObject.NULL)
            .put("decodedFps",if (first!=null && ended>first) ((data!![1]-1).coerceAtLeast(0))*1_000_000_000.0/(ended-first) else JSONObject.NULL)
            .put("presentedFrames",JSONObject.NULL).put("displayDroppedFrames",JSONObject.NULL)
            .put("queueLatencyMs",JSONObject.NULL)
    }
}
