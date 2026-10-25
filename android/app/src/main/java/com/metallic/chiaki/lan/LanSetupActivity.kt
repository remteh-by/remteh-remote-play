// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.lan

import com.metallic.chiaki.R
import android.content.Intent
import com.metallic.chiaki.design.DeckivoUi
import android.media.MediaCodecList
import android.os.Bundle
import android.text.InputType
import android.util.Base64
import android.view.View
import android.widget.*
import com.metallic.chiaki.design.DeckivoActivity
import androidx.lifecycle.lifecycleScope
import com.metallic.chiaki.BuildConfig
import com.metallic.chiaki.common.Preferences
import com.metallic.chiaki.regist.RegistActivity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.InetSocketAddress
import java.net.Socket
import java.net.URL

/** Local setup only. Account ID stays in memory; no PSN login or account activation. */
class LanSetupActivity : DeckivoActivity() {
    private lateinit var host: EditText
    private lateinit var code: EditText
    private lateinit var account: EditText
    private lateinit var status: TextView
    private lateinit var panel: LinearLayout
    private var requestInFlight = false
    private val localPrefs by lazy { getSharedPreferences("remteh_lan", MODE_PRIVATE) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        title = "Switch OLED → PS5"
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        val content = DeckivoUi.screen(this, getString(R.string.dv_setup), getString(R.string.dv_setup_intro))
        panel = DeckivoUi.section(content, getString(R.string.dv_setup_find))
        label(getString(R.string.dv_setup_enable))
        host = field(getString(R.string.dv_ps5_ip), localPrefs.getString("host", "") ?: "")
        host.inputType = InputType.TYPE_CLASS_PHONE
        button(getString(R.string.dv_check_connection)) { diagnose() }
        button(getString(R.string.dv_switch_profile)) {
            SwitchProfile.apply(Preferences(this))
            status.text = getString(R.string.dv_profile_applied)
        }
        button(getString(R.string.dv_controller_check)) {
            startActivity(Intent(this, ControllerTestActivity::class.java))
        }
        panel = DeckivoUi.section(content, getString(R.string.dv_setup_profile))
        label(getString(R.string.dv_helper_intro))
        button(getString(R.string.dv_helper_launch)) { launchHelper() }
        code = field(getString(R.string.dv_helper_code), "", true)
        button(getString(R.string.dv_account_fetch)) { fetchAccount() }
        account = field(getString(R.string.dv_account_manual), "")
        account.isSaveEnabled = false
        code.isSaveEnabled = false
        panel = DeckivoUi.section(content, getString(R.string.dv_setup_finish))
        button(getString(R.string.dv_setup_register)) {
            val ip = checkedHost() ?: return@button
            val id = account.text.toString().trim()
            if (!LanRules.looksLikeAccountId(id) || runCatching { Base64.decode(id, Base64.DEFAULT).size }.getOrDefault(0) != 8) {
                account.error = getString(R.string.dv_account_required)
                return@button
            }
            startActivity(Intent(this, RegistActivity::class.java).apply {
                putExtra(RegistActivity.EXTRA_HOST, ip)
                putExtra(RegistActivity.EXTRA_BROADCAST, false)
                putExtra(RegistActivity.EXTRA_ACCOUNT_ID, id)
            })
        }
        status = label(getString(R.string.dv_setup_done))
        button(getString(R.string.dv_console_list)) { finish() }
        label(getString(R.string.dv_setup_credit))
    }

    private fun label(text: String, size: Float = 15f): TextView = DeckivoUi.label(panel, text, size, size >= 20f)
    private fun field(hint: String, value: String, digits: Boolean = false): EditText = DeckivoUi.field(panel, hint, value, digits)
    private fun button(text: String, action: () -> Unit) = DeckivoUi.button(panel, text, text == getString(R.string.dv_setup_register) || text == getString(R.string.dv_check_connection), action)

    private fun checkedHost(): String? {
        val ip = host.text.toString().trim()
        if (!LanRules.isPrivateIpv4(ip)) {
            host.error = getString(R.string.dv_ip_required)
            return null
        }
        localPrefs.edit().putString("host", ip).apply()
        return ip
    }

    private fun diagnose() {
        val ip = checkedHost() ?: return
        if (requestInFlight) return
        requestInFlight = true
        status.text = "Checking Remote Play TCP and available decoders…"
        lifecycleScope.launch {
            try {
                val report = withContext(Dispatchers.IO) {
                    val samples = (1..3).mapNotNull {
                        runCatching {
                            val start = System.nanoTime()
                            Socket().use { it.connect(InetSocketAddress(ip, 9295), 1500) }
                            (System.nanoTime() - start) / 1_000_000.0
                        }.getOrNull()
                    }
                    val codecs = MediaCodecList(MediaCodecList.REGULAR_CODECS).codecInfos
                        .filter { !it.isEncoder && it.supportedTypes.any { type -> type.equals("video/avc", true) } }
                        .joinToString { it.name }
                    val network = if (samples.isEmpty()) "PS5 port 9295 is unreachable. Check power, IP, Remote Play and Wi-Fi client isolation."
                        else "Remote Play responds: ${samples.size}/3, TCP ${"%.1f".format(samples.average())} ms. This checks connectivity, not video latency."
                    "$network\nH.264 decoder: ${codecs.ifEmpty { "not found" }}\nAn open port does not confirm registration or streaming."
                }
                status.text = report
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                status.text = "Check incomplete: ${e.message ?: "unknown error"}"
            } finally { requestInFlight = false }
        }
    }

    private fun fetchAccount() {
        val ip = checkedHost() ?: return
        val token = code.text.toString().trim()
        if (!LanRules.isEightDigitCode(token)) { code.error = "Enter 8 digits from the PS5 companion notification"; return }
        if (requestInFlight) return
        requestInFlight = true
        status.text = "Connecting to PS5 companion…"
        lifecycleScope.launch {
            try {
                val payload = withContext(Dispatchers.IO) {
                    val connection = URL("http://$ip:38080/v1/account").openConnection(java.net.Proxy.NO_PROXY) as HttpURLConnection
                    try {
                        connection.connectTimeout = 4000; connection.readTimeout = 4000
                        connection.instanceFollowRedirects = false
                        connection.requestMethod = "POST"; connection.doOutput = true
                        connection.setRequestProperty("Content-Type", "text/plain")
                        connection.setRequestProperty("X-RemTeh-Client", "1")
                        connection.setFixedLengthStreamingMode(8)
                        connection.outputStream.use { it.write(token.toByteArray(Charsets.US_ASCII)) }
                        val response = connection.responseCode
                        require(response == 200) { "Companion returned HTTP $response. Check the code and active profile; restart the companion if it expired." }
                        val bytes = connection.inputStream.use { stream ->
                            val data = ByteArray(4097); var count = 0
                            while (count < data.size) { val n = stream.read(data, count, data.size - count); if (n < 0) break; count += n }
                            require(count <= 4096) { "Response too large" }
                            data.copyOf(count)
                        }
                        JSONObject(bytes.toString(Charsets.UTF_8)).also {
                            require(it.optInt("protocol") == 1 && LanRules.looksLikeAccountId(it.optString("accountId"))) { "Unsupported companion response" }
                        }
                    } finally { connection.disconnect() }
                }
                account.setText(payload.getString("accountId")); code.text.clear()
                status.text = "ID received. On PS5, open Remote Play → Link Device, then complete step 3 here. Keep the same PS5 profile active."
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                status.text = e.message ?: "Companion unreachable. Launch its ELF on PS5 or enter Account ID manually."
            } finally { requestInFlight = false }
        }
    }

    private fun helperRunning(ip: String): Boolean {
        val c = URL("http://$ip:38080/v1/status").openConnection(java.net.Proxy.NO_PROXY) as HttpURLConnection
        return try {
            c.connectTimeout = 800; c.readTimeout = 800; c.instanceFollowRedirects = false
            c.responseCode == 200 && c.inputStream.use { stream ->
                val data = ByteArray(513)
                var count = 0
                while (count < data.size) {
                    val n = stream.read(data, count, data.size - count)
                    if (n < 0) break
                    count += n
                }
                count in 1..512 && JSONObject(String(data, 0, count, Charsets.UTF_8)).optInt("protocol") == 1
            }
        } catch (_: Exception) { false } finally { c.disconnect() }
    }

    private fun launchHelper() {
        val ip = checkedHost() ?: return
        if (requestInFlight) return
        requestInFlight = true
        status.text = "Connecting to PS5 ELF Loader…"
        lifecycleScope.launch {
            try {
                val running = withContext(Dispatchers.IO) {
                    if (helperRunning(ip)) true else {
                        Socket().use { socket ->
                            socket.connect(InetSocketAddress(ip, 9021), 3000)
                            assets.open("remteh-pair-helper.elf").use { it.copyTo(socket.getOutputStream()) }
                            socket.shutdownOutput()
                        }
                        var ready = false
                        repeat(5) {
                            if (!ready) { kotlinx.coroutines.delay(400); ready = helperRunning(ip) }
                        }
                        ready
                    }
                }
                status.text = if (running) "Companion ready. Enter the code from the PS5 notification below."
                    else "ELF sent, but the companion has not responded yet. Check PS5 notifications. Do not resend if a code is already displayed."
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                status.text = "Could not start companion. Open WebKit / Payload Manager on PS5 and check ELF Loader (port 9021). ${e.message ?: ""}"
            } finally { requestInFlight = false }
        }
    }

    override fun onSupportNavigateUp(): Boolean { finish(); return true }
}
