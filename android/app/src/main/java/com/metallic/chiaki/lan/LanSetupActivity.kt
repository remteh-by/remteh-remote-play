// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.lan

import android.content.Intent
import android.media.MediaCodecList
import android.os.Bundle
import android.text.InputType
import android.util.Base64
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
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
class LanSetupActivity : AppCompatActivity() {
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
        panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(28, 12, 28, 24)
        }
        val scroll = ScrollView(this).apply { addView(panel) }
        setContentView(scroll)
        SafeInsets.apply(scroll)
        label("RemTeh Remote Play ${BuildConfig.VERSION_NAME} · домашняя сеть", 22f)
        label("Обе приставки подключи к домашней сети. На PS5 войди в нужный профиль и включи «Настройки → Система → Дистанционное воспроизведение». Mac для игры не нужен.")
        host = field("IP-адрес PS5", localPrefs.getString("host", "192.168.31.77") ?: "")
        host.inputType = InputType.TYPE_CLASS_PHONE
        button("1. Проверить связь и декодер") { diagnose() }
        button("Профиль OLED: 720p · 60 кадров · 8 Мбит/с") {
            SwitchProfile.apply(Preferences(this))
            status.text = "Профиль применён. H.264, без дополнительных фильтров. Экран работает как тачпад; кнопки PS и Touch доступны поверх игры."
        }
        button("Проверить и настроить Joy-Con") {
            startActivity(Intent(this, ControllerTestActivity::class.java))
        }
        label("2. Привязать свой профиль", 20f)
        label("На PS5 открой WebKit / Payload Manager и дождись ELF Loader. Кнопка ниже отправит помощник из этого APK на твою консоль. Затем введи код из уведомления PS5: он действует 5 минут и один раз. Это не системный код Remote Play.")
        button("Запустить помощник на PS5 с этого Switch") { launchHelper() }
        code = field("Код помощника PS5", "", true)
        button("Получить ID текущего профиля с PS5") { fetchAccount() }
        account = field("Account ID (Base64); можно ввести вручную", "")
        account.isSaveEnabled = false
        code.isSaveEnabled = false
        button("3. Ввести код Remote Play и привязать") {
            val ip = checkedHost() ?: return@button
            val id = account.text.toString().trim()
            if (!LanRules.looksLikeAccountId(id) || runCatching { Base64.decode(id, Base64.DEFAULT).size }.getOrDefault(0) != 8) {
                account.error = "Нужен Account ID из помощника или LinkDev (8 байт в Base64)."
                return@button
            }
            startActivity(Intent(this, RegistActivity::class.java).apply {
                putExtra(RegistActivity.EXTRA_HOST, ip)
                putExtra(RegistActivity.EXTRA_BROADCAST, false)
                putExtra(RegistActivity.EXTRA_ACCOUNT_ID, id)
            })
        }
        status = label("После привязки вернись на главный экран приложения и выбери PS5. Для этой версии достаточно локальной сети; доступ через интернет пока не настроен.")
        button("Перейти к списку консолей") { finish() }
        label("Основа: Chiaki / chiaki-ng Android Extended (AGPL-3.0). Исходники и изменения включены в комплект. Это отдельный клиент, не приложение Sony.")
    }

    private fun label(text: String, size: Float = 16f): TextView = TextView(this).apply {
        this.text = text; textSize = size; setPadding(0, 10, 0, 10); panel.addView(this)
    }

    private fun field(hint: String, value: String, digits: Boolean = false): EditText = EditText(this).apply {
        this.hint = hint; setText(value); isSingleLine = true
        inputType = if (digits) InputType.TYPE_CLASS_NUMBER else InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
        importantForAutofill = View.IMPORTANT_FOR_AUTOFILL_NO
        panel.addView(this)
    }

    private fun button(text: String, action: () -> Unit) = Button(this).apply {
        this.text = text; isAllCaps = false; setOnClickListener { action() }; panel.addView(this)
    }

    private fun checkedHost(): String? {
        val ip = host.text.toString().trim()
        if (!LanRules.isPrivateIpv4(ip)) {
            host.error = "Укажи локальный IPv4, например 192.168.31.77. Без http и порта."
            return null
        }
        localPrefs.edit().putString("host", ip).apply()
        return ip
    }

    private fun diagnose() {
        val ip = checkedHost() ?: return
        if (requestInFlight) return
        requestInFlight = true
        status.text = "Проверяю TCP Remote Play и доступные декодеры…"
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
                    val network = if (samples.isEmpty()) "PS5: порт 9295 недоступен. Проверь питание, IP, Remote Play и изоляцию клиентов Wi-Fi."
                        else "Remote Play отвечает: ${samples.size}/3, TCP ${"%.1f".format(samples.average())} мс. Это проверка доступности, не тест задержки видео."
                    "$network\nДекодер H.264: ${codecs.ifEmpty { "не найден" }}\nОткрытый порт ещё не подтверждает привязку и передачу игры."
                }
                status.text = report
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                status.text = "Проверка не завершена: ${e.message ?: "неизвестная ошибка"}"
            } finally { requestInFlight = false }
        }
    }

    private fun fetchAccount() {
        val ip = checkedHost() ?: return
        val token = code.text.toString().trim()
        if (!LanRules.isEightDigitCode(token)) { code.error = "Введи 8 цифр из уведомления помощника PS5"; return }
        if (requestInFlight) return
        requestInFlight = true
        status.text = "Подключаюсь к помощнику PS5…"
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
                        require(response == 200) { "Помощник ответил HTTP $response. Проверь код и активный профиль; при истечении времени запусти помощник снова." }
                        val bytes = connection.inputStream.use { stream ->
                            val data = ByteArray(4097); var count = 0
                            while (count < data.size) { val n = stream.read(data, count, data.size - count); if (n < 0) break; count += n }
                            require(count <= 4096) { "Слишком большой ответ" }
                            data.copyOf(count)
                        }
                        JSONObject(bytes.toString(Charsets.UTF_8)).also {
                            require(it.optInt("protocol") == 1 && LanRules.looksLikeAccountId(it.optString("accountId"))) { "Неподдерживаемый ответ помощника" }
                        }
                    } finally { connection.disconnect() }
                }
                account.setText(payload.getString("accountId")); code.text.clear()
                status.text = "ID получен. На PS5 открой «Дистанционное воспроизведение → Привязать устройство», затем нажми шаг 3. Профиль PS5 пока не переключай."
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                status.text = e.message ?: "Нет связи с помощником. Запусти ELF на PS5 или введи Account ID вручную."
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
        status.text = "Подключаюсь к ELF Loader PS5…"
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
                status.text = if (running) "Помощник отвечает. Введи код из уведомления PS5 в поле ниже."
                    else "ELF передан, но помощник пока не ответил. Проверь уведомление PS5. Не запускай повторно, если код уже показан."
            } catch (e: Exception) {
                if (e is kotlinx.coroutines.CancellationException) throw e
                status.text = "Не удалось запустить помощник. На PS5 открой WebKit / Payload Manager и проверь ELF Loader (порт 9021). ${e.message ?: ""}"
            } finally { requestInFlight = false }
        }
    }

    override fun onSupportNavigateUp(): Boolean { finish(); return true }
}
