package com.metallic.chiaki.design

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Color
import androidx.core.net.toUri
import android.widget.ImageView
import android.widget.LinearLayout
import androidx.appcompat.app.AlertDialog
import com.google.zxing.BarcodeFormat
import com.google.zxing.EncodeHintType
import com.google.zxing.qrcode.QRCodeWriter
import com.google.zxing.qrcode.decoder.ErrorCorrectionLevel
import com.metallic.chiaki.R

/** Browser-independent local QR fallback. Console credentials never enter links. */
object LinkUi {
    const val GITHUB_URL = "https://github.com/remteh-by/remteh-remote-play"
    const val REMTEH_URL = "https://remteh.by/?utm_source=deckivo_android&utm_medium=app&utm_campaign=deckivo"

    fun qr(value: String, size: Int = 360): Bitmap {
        require(value.length in 1..2048)
        val bits = QRCodeWriter().encode(value, BarcodeFormat.QR_CODE, size, size,
            mapOf(EncodeHintType.MARGIN to 4, EncodeHintType.ERROR_CORRECTION to ErrorCorrectionLevel.M))
        val pixels = IntArray(size * size) { i -> if (bits[i % size, i / size]) Color.BLACK else Color.WHITE }
        return Bitmap.createBitmap(pixels, size, size, Bitmap.Config.ARGB_8888)
    }

    fun qrView(activity: Activity, value: String): ImageView = ImageView(activity).apply {
        setImageBitmap(qr(value))
        setBackgroundColor(Color.WHITE)
        contentDescription = activity.getString(R.string.dv_scan_phone)
        scaleType = ImageView.ScaleType.FIT_CENTER
        minimumHeight = DeckivoUi.dp(activity, 240)
    }

    fun openLinkOrShowQr(activity: Activity, url: String) {
        require(url.toUri().scheme == "https")
        try { activity.startActivity(Intent(Intent.ACTION_VIEW, url.toUri())) }
        catch (_: ActivityNotFoundException) { showQr(activity, url) }
        catch (_: SecurityException) { showQr(activity, url) }
    }

    fun showQr(activity: Activity, value: String) {
        val panel = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 12, 24, 12)
        }
        panel.addView(qrView(activity, value), LinearLayout.LayoutParams(-1, DeckivoUi.dp(activity, 280)))
        DeckivoUi.label(panel, value, 14f).setTextIsSelectable(true)
        AlertDialog.Builder(activity).setTitle(R.string.dv_scan_phone).setView(panel)
            .setPositiveButton(android.R.string.ok, null).show()
    }
}
