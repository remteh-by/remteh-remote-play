// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.lan

import android.annotation.SuppressLint
import android.app.PendingIntent
import android.content.*
import android.content.pm.PackageManager
import android.hardware.usb.*
import android.os.*
import android.util.Base64
import android.view.*
import android.webkit.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.addCallback
import androidx.core.content.ContextCompat
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.metallic.chiaki.R
import com.metallic.chiaki.design.DeckivoActivity
import com.metallic.chiaki.design.LinkUi
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayInputStream
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

/** Only app-bundled assets may call this bridge; no remote page is loaded. */
class ControllerLabActivity : DeckivoActivity() {
    private lateinit var web: WebView
    private val usb by lazy { getSystemService(USB_SERVICE) as UsbManager }
    private val executor = Executors.newSingleThreadExecutor()
    private val handler = Handler(Looper.getMainLooper())
    private val closed = AtomicBoolean(false)
    private var connection: UsbDeviceConnection? = null
    private var current: UsbDevice? = null
    private var hidInterface: UsbInterface? = null
    private var readThread: Thread? = null
    private var pendingChoice: String? = null
    private var mediaPermission: PermissionRequest? = null
    private var fileCallback: ValueCallback<Array<android.net.Uri>>? = null
    private var exportData: ByteArray? = null
    private var exportId: String? = null
    private val fileRequest=registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        fileCallback?.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result.resultCode,result.data));fileCallback=null
    }
    private val saveRequest=registerForActivityResult(ActivityResultContracts.CreateDocument("application/octet-stream")) { uri ->
        val bytes=exportData;val id=exportId;exportData=null;exportId=null
        if(id!=null) executor.execute { try {
            if(uri==null||bytes==null) throw IllegalStateException("Export cancelled")
            contentResolver.openOutputStream(uri)?.use { it.write(bytes) } ?: throw IllegalStateException("Export failed")
            reply(id,JSONObject())
        } catch(error:Exception) { fail(id,error) } }
    }
    private val pads = linkedMapOf<Int, JSONObject>()
    private val permissionAction by lazy { "$packageName.CONTROLLER_USB_PERMISSION" }
    private val audioRequest = registerForActivityResult(ActivityResultContracts.RequestPermission()) { allowed ->
        mediaPermission?.let { if (allowed) it.grant(arrayOf(PermissionRequest.RESOURCE_AUDIO_CAPTURE)) else it.deny() }
        mediaPermission = null
    }
    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == permissionAction) {
                val id = pendingChoice ?: return
                pendingChoice = null
                val device = androidx.core.content.IntentCompat.getParcelableExtra(intent,UsbManager.EXTRA_DEVICE,UsbDevice::class.java)
                if (device != null && usb.hasPermission(device)) executor.execute {
                    try { reply(id, JSONArray().put(info(device))) } catch (error: Exception) { fail(id, error) }
                } else fail(id, IllegalStateException("USB permission denied"))
            } else if (intent?.action == UsbManager.ACTION_USB_DEVICE_DETACHED) {
                val device = androidx.core.content.IntentCompat.getParcelableExtra(intent,UsbManager.EXTRA_DEVICE,UsbDevice::class.java)
                if (device != null && device.deviceId == current?.deviceId) {
                    val deviceId = device.deviceId
                    closeUsb()
                    js("window.DeckivoNative?.disconnect($deviceId)")
                }
            }
        }
    }

    @SuppressLint("SetJavaScriptEnabled") // Trusted app assets only; intercepted host and navigation are allowlisted below.
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        title = getString(R.string.dv_controller_lab)
        web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.allowFileAccess = false
        web.settings.allowContentAccess = false
        web.settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        web.addJavascriptInterface(UsbBridge(), "DeckivoUsb")
        web.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                if (request.url.scheme == "https" && request.url.host == HOST) return false
                if (request.isForMainFrame && request.url.scheme == "https") LinkUi.openLinkOrShowQr(this@ControllerLabActivity, request.url.toString())
                return true
            }
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse {
                val url = request.url
                if (url.scheme != "https" || url.host != HOST || url.path.orEmpty().split('/').any { it == ".." }) return emptyResponse()
                val path = url.path.orEmpty().removePrefix("/").ifEmpty { "index.html" }
                if(path=="media/remteh-gamepad/v20261011/firmware.php") return firmwareResponse(url)
                val mime = when (path.substringAfterLast('.')) {
                    "js" -> "text/javascript"; "css" -> "text/css"; "json" -> "application/json"
                    "png" -> "image/png"; "svg" -> "image/svg+xml"; "mp3" -> "audio/mpeg"; "html" -> "text/html"
                    else -> return emptyResponse()
                }
                return try {
                    WebResourceResponse(mime, "utf-8", 200, "OK", mapOf("Content-Security-Policy" to "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; frame-src 'none'; base-uri 'none'", "X-Content-Type-Options" to "nosniff"), assets.open(path))
                } catch (_: java.io.IOException) { emptyResponse() }
            }
        }
        web.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(view: WebView,callback: ValueCallback<Array<android.net.Uri>>,params: FileChooserParams): Boolean {
                fileCallback?.onReceiveValue(null);fileCallback=callback
                return try { fileRequest.launch(params.createIntent());true } catch(_:ActivityNotFoundException) { callback.onReceiveValue(null);fileCallback=null;false }
            }
            override fun onPermissionRequest(request: PermissionRequest) {
                runOnUiThread {
                    if (request.origin.host != HOST || !request.resources.contains(PermissionRequest.RESOURCE_AUDIO_CAPTURE)) { request.deny(); return@runOnUiThread }
                    if (ContextCompat.checkSelfPermission(this@ControllerLabActivity, android.Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) request.grant(arrayOf(PermissionRequest.RESOURCE_AUDIO_CAPTURE))
                    else { mediaPermission?.deny(); mediaPermission = request; audioRequest.launch(android.Manifest.permission.RECORD_AUDIO) }
                }
            }
        }
        setContentView(web)
        onBackPressedDispatcher.addCallback(this@ControllerLabActivity) {
            if(web.canGoBack()) web.goBack() else {
                web.evaluateJavascript("Promise.resolve(window.DeckivoLabClose?.()).finally(()=>window.DeckivoUsb.request('900000000','finish','{}'))",null)
                handler.postDelayed({ if(!isFinishing) finish() },6000)
            }
        }
        ContextCompat.registerReceiver(this, receiver, IntentFilter(permissionAction).apply { addAction(UsbManager.ACTION_USB_DEVICE_DETACHED) }, ContextCompat.RECEIVER_NOT_EXPORTED)
        val language = resources.configuration.locales[0].language
        web.loadUrl("https://$HOST/?lang=${if (language == "ru") "ru" else "en"}")
    }

    private fun firmwareResponse(url: android.net.Uri): WebResourceResponse {
        return try {
            val query=url.queryParameterNames
            require(query.isEmpty() || (query==setOf("family","version") && query.all { url.getQueryParameters(it).size==1 && url.getQueryParameter(it).orEmpty().matches(Regex("[A-Za-z0-9_.-]{1,40}")) }))
            val remote=java.net.URL("https://remteh.by/media/remteh-gamepad/v20261011/firmware.php"+(url.encodedQuery?.let { "?$it" } ?: ""))
            val c=remote.openConnection() as javax.net.ssl.HttpsURLConnection
            c.instanceFollowRedirects=false;c.connectTimeout=7000;c.readTimeout=7000
            try {
                require(c.responseCode==200)
                val bytes=c.inputStream.use { input ->
                    val output=java.io.ByteArrayOutputStream();val buffer=ByteArray(8192);var total=0
                    while(true) { val n=input.read(buffer);if(n<0)break;total+=n;require(total<=12*1024*1024);output.write(buffer,0,n) };output.toByteArray()
                }
                WebResourceResponse(if(query.isEmpty())"application/json" else "application/octet-stream","utf-8",ByteArrayInputStream(bytes))
            } finally { c.disconnect() }
        } catch(_:Exception) { emptyResponse() }
    }

    private fun emptyResponse() = WebResourceResponse("text/plain", "utf-8", 404, "Not found", emptyMap(), ByteArrayInputStream(ByteArray(0)))
    private fun js(code: String) { if (!closed.get()) handler.post { if (!closed.get()) web.evaluateJavascript(code, null) } }
    private fun reply(id: String, value: Any) = js("window.DeckivoNative?.complete(${JSONObject.quote(id)},$value,null)")
    private fun fail(id: String, error: Exception) = js("window.DeckivoNative?.complete(${JSONObject.quote(id)},null,${JSONObject.quote(error.message ?: "USB operation failed")})")
    private fun supported(d: UsbDevice) = d.vendorId == 0x054c && d.productId in listOf(0x05c4, 0x09cc, 0x0ce6, 0x0df2) && (0 until d.interfaceCount).any { d.getInterface(it).interfaceClass == UsbConstants.USB_CLASS_HID }
    private fun interfaceFor(d: UsbDevice) = (0 until d.interfaceCount).map { d.getInterface(it) }.first { it.interfaceClass == UsbConstants.USB_CLASS_HID }

    private fun collections(d: UsbDevice): JSONArray {
        val active = if (current?.deviceId == d.deviceId) connection else null
        val c = active ?: usb.openDevice(d) ?: throw IllegalStateException("USB permission missing")
        try {
            val iface = interfaceFor(d)
            val descriptor = ByteArray(4096)
            val n = c.controlTransfer(0x81, 6, 0x2200, iface.id, descriptor, descriptor.size, 1500)
            if (n <= 0) throw IllegalStateException("HID descriptor unavailable")
            var i = 0; var report = 0
            val input = linkedSetOf<Int>()
            while (i < n) {
                val prefix = descriptor[i++].toInt() and 255
                if (prefix == 0xfe) { if (i + 1 >= n) break; val size = descriptor[i].toInt() and 255; i += 2 + size; continue }
                val size = if (prefix and 3 == 3) 4 else prefix and 3
                if (i + size > n) break
                val type = (prefix shr 2) and 3; val tag = prefix shr 4
                if (type == 1 && tag == 8 && size == 1) report = descriptor[i].toInt() and 255
                if (type == 0 && tag == 8) input.add(report)
                i += size
            }
            return JSONArray().put(JSONObject().put("inputReports", JSONArray(input.map { JSONObject().put("reportId", it) })))
        } finally { if (active == null) c.close() }
    }

    private fun info(d: UsbDevice) = JSONObject().put("deviceId", d.deviceId).put("vendorId", d.vendorId).put("productId", d.productId).put("productName", d.productName ?: "Sony controller").put("collections", collections(d))

    private inner class UsbBridge {
        @JavascriptInterface
        fun request(id: String, operation: String, payload: String) {
            if (closed.get() || !id.matches(Regex("[0-9]{1,9}")) || payload.length > (if(operation=="saveFile") 18*1024*1024 else 20000)) return
            if (operation == "choose") {
                handler.post { choose(id) }; return
            }
            executor.execute {
                try {
                    val value = JSONObject(payload)
                    when (operation) {
                        "finish" -> handler.post { finish() }
                        "saveFile" -> {
                            val bytes=Base64.decode(value.getString("data"),Base64.DEFAULT);require(bytes.size<=12*1024*1024)
                            val name=value.getString("name").take(100).replace(Regex("[^A-Za-z0-9_.-]"),"_")
                            require(name.endsWith(".json")||name.endsWith(".png")||name.endsWith(".bin")||name.endsWith(".dat"))
                            handler.post {
                                if(exportId!=null) fail(id,IllegalStateException("Export already open"))
                                else { exportData=bytes;exportId=id;saveRequest.launch(name) }
                            }
                        }
                        "granted" -> reply(id, JSONArray(usb.deviceList.values.filter { supported(it) && usb.hasPermission(it) }.map { info(it) }))
                        "open" -> {
                            val d = usb.deviceList.values.firstOrNull { it.deviceId == value.getInt("deviceId") && supported(it) && usb.hasPermission(it) } ?: throw IllegalStateException("USB device unavailable")
                            closeUsb()
                            val c = usb.openDevice(d) ?: throw IllegalStateException("Could not open USB")
                            val iface = interfaceFor(d)
                            if (!c.claimInterface(iface, true)) { c.close(); throw IllegalStateException("USB interface is busy") }
                            current=d;connection=c;hidInterface=iface
                            val metadata=info(d)
                            reply(id, metadata)
                            startReader(d,c,iface)
                        }
                        "close" -> { closeUsb(); reply(id, JSONObject()) }
                        "featureRead", "featureWrite", "outputWrite" -> {
                            val c=connection ?: throw IllegalStateException("USB disconnected")
                            val d=current ?: throw IllegalStateException("USB disconnected")
                            if (value.getInt("deviceId") != d.deviceId) throw IllegalStateException("USB device changed")
                            val report=value.getInt("reportId")
                            require(report in 0..255)
                            val iface=hidInterface ?: throw IllegalStateException("USB disconnected")
                            if (operation == "featureRead") {
                                val data=ByteArray(4096)
                                val n=c.controlTransfer(0xa1,1,(3 shl 8) or report,iface.id,data,data.size,2500)
                                if (n <= 0) throw IllegalStateException("USB feature read failed")
                                reply(id,JSONObject().put("data",Base64.encodeToString(data.copyOf(n),Base64.NO_WRAP)))
                            } else {
                                val body=Base64.decode(value.getString("data"),Base64.DEFAULT)
                                require(body.size <= 4095)
                                val data=byteArrayOf(report.toByte())+body
                                val endpoint=(0 until iface.endpointCount).map { iface.getEndpoint(it) }.firstOrNull { it.direction == UsbConstants.USB_DIR_OUT && it.type == UsbConstants.USB_ENDPOINT_XFER_INT }
                                val n=if (operation == "outputWrite" && endpoint != null) c.bulkTransfer(endpoint,data,data.size,2500) else c.controlTransfer(0x21,9,((if(operation == "featureWrite") 3 else 2) shl 8) or report,iface.id,data,data.size,2500)
                                if (n != data.size) throw IllegalStateException("USB write not confirmed")
                                reply(id,JSONObject())
                            }
                        }
                        else -> throw IllegalArgumentException("Unknown USB operation")
                    }
                } catch (error: Exception) { fail(id,error) }
            }
        }
    }

    private fun choose(id: String) {
        if (pendingChoice != null) { fail(id,IllegalStateException("USB chooser already open"));return }
        val devices=usb.deviceList.values.filter(::supported)
        if (devices.isEmpty()) { fail(id,IllegalStateException(getString(R.string.dv_usb_sony_missing)));return }
        MaterialAlertDialogBuilder(this).setTitle(R.string.dv_usb_choose).setItems(devices.map { it.productName ?: "Sony USB" }.toTypedArray()) { _, index ->
            val d=devices[index]
            if (usb.hasPermission(d)) executor.execute { try { reply(id,JSONArray().put(info(d))) } catch(e:Exception) { fail(id,e) } }
            else {
                pendingChoice=id
                val intent=Intent(permissionAction).setPackage(packageName)
                usb.requestPermission(d,PendingIntent.getBroadcast(this,0,intent,PendingIntent.FLAG_MUTABLE or PendingIntent.FLAG_UPDATE_CURRENT))
            }
        }.setOnCancelListener { fail(id,IllegalStateException("Connection cancelled")) }.show()
    }

    private fun startReader(d: UsbDevice,c: UsbDeviceConnection,iface: UsbInterface) {
        val endpoint=(0 until iface.endpointCount).map { iface.getEndpoint(it) }.firstOrNull { it.direction == UsbConstants.USB_DIR_IN && it.type == UsbConstants.USB_ENDPOINT_XFER_INT } ?: return
        readThread=Thread({
            val buffer=ByteArray(maxOf(endpoint.maxPacketSize,1024))
            while (!closed.get() && connection === c) {
                val n=c.bulkTransfer(endpoint,buffer,buffer.size,250)
                if (n > 1) js("window.DeckivoNative?.input(${d.deviceId},${buffer[0].toInt() and 255},${JSONObject.quote(Base64.encodeToString(buffer.copyOfRange(1,n),Base64.NO_WRAP))})")
            }
        },"Deckivo controller input").also { it.isDaemon=true;it.start() }
    }

    private fun closeUsb() {
        val c=connection
        connection=null
        readThread?.join(400);readThread=null
        hidInterface?.let { c?.releaseInterface(it) }
        c?.close();current=null;hidInterface=null
    }

    private fun pad(event: InputEvent): JSONObject? {
        val device=event.device ?: return null
        if (device.sources and InputDevice.SOURCE_GAMEPAD != InputDevice.SOURCE_GAMEPAD && device.sources and InputDevice.SOURCE_JOYSTICK != InputDevice.SOURCE_JOYSTICK) return null
        return pads.getOrPut(device.id) { JSONObject().put("id",device.name).put("index",pads.size).put("connected",true).put("mapping","standard").put("axes",JSONArray(listOf(0,0,0,0))).put("buttons",JSONArray((0..16).map { JSONObject().put("value",0).put("pressed",false).put("touched",false) })) }
    }
    private fun sendPads() { js("window.DeckivoNative?.gamepads(${JSONArray(pads.values.toList())})") }
    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        val state=pad(event) ?: return super.dispatchKeyEvent(event)
        val code=listOf(KeyEvent.KEYCODE_BUTTON_A,KeyEvent.KEYCODE_BUTTON_B,KeyEvent.KEYCODE_BUTTON_X,KeyEvent.KEYCODE_BUTTON_Y,KeyEvent.KEYCODE_BUTTON_L1,KeyEvent.KEYCODE_BUTTON_R1,KeyEvent.KEYCODE_BUTTON_L2,KeyEvent.KEYCODE_BUTTON_R2,KeyEvent.KEYCODE_BUTTON_SELECT,KeyEvent.KEYCODE_BUTTON_START,KeyEvent.KEYCODE_BUTTON_THUMBL,KeyEvent.KEYCODE_BUTTON_THUMBR,KeyEvent.KEYCODE_DPAD_UP,KeyEvent.KEYCODE_DPAD_DOWN,KeyEvent.KEYCODE_DPAD_LEFT,KeyEvent.KEYCODE_DPAD_RIGHT,KeyEvent.KEYCODE_BUTTON_MODE).indexOf(event.keyCode)
        if (code < 0) return super.dispatchKeyEvent(event)
        val down=event.action == KeyEvent.ACTION_DOWN
        state.getJSONArray("buttons").put(code,JSONObject().put("value",if(down)1 else 0).put("pressed",down).put("touched",down));sendPads();return true
    }
    override fun onGenericMotionEvent(event: MotionEvent): Boolean {
        val state=pad(event) ?: return super.onGenericMotionEvent(event)
        if (event.source and InputDevice.SOURCE_CLASS_JOYSTICK == 0) return super.onGenericMotionEvent(event)
        val axes=listOf(MotionEvent.AXIS_X,MotionEvent.AXIS_Y,MotionEvent.AXIS_Z,MotionEvent.AXIS_RZ).map { event.getAxisValue(it).coerceIn(-1f,1f) }
        state.put("axes",JSONArray(axes))
        listOf(MotionEvent.AXIS_LTRIGGER to 6,MotionEvent.AXIS_RTRIGGER to 7).forEach { (axis,index) -> val v=event.getAxisValue(axis).coerceIn(0f,1f);state.getJSONArray("buttons").put(index,JSONObject().put("value",v).put("pressed",v>.5).put("touched",v>0)) }
        val x=event.getAxisValue(MotionEvent.AXIS_HAT_X);val y=event.getAxisValue(MotionEvent.AXIS_HAT_Y)
        listOf((y<-.5f) to 12,(y>.5f) to 13,(x<-.5f) to 14,(x>.5f) to 15).forEach { (pressed,index) -> state.getJSONArray("buttons").put(index,JSONObject().put("value",if(pressed)1 else 0).put("pressed",pressed).put("touched",pressed)) }
        sendPads();return true
    }
    override fun onResume() { super.onResume();if(::web.isInitialized) js("window.DeckivoLabResume?.()") }
    override fun onPause() {
        super.onPause()
        // System pickers belong to the current test. Keep that authorized USB
        // connection through a file/microphone permission dialog.
        if(fileCallback==null&&exportId==null&&mediaPermission==null&&pendingChoice==null) {
            js("window.DeckivoLabClose?.()")
            handler.postDelayed({ if(!hasWindowFocus()) closeUsb() },6000)
            pads.clear();sendPads()
        }
    }
    override fun onDestroy() {
        closed.set(true);mediaPermission?.deny();fileCallback?.onReceiveValue(null);fileCallback=null;exportData=null;closeUsb();unregisterReceiver(receiver);executor.shutdownNow();handler.removeCallbacksAndMessages(null)
        web.removeJavascriptInterface("DeckivoUsb");web.destroy();super.onDestroy()
    }
    companion object { private const val HOST="appassets.androidplatform.net" }
}
