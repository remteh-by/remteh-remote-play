// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.design

import android.os.Bundle
import com.metallic.chiaki.design.DeckivoActivity
import com.metallic.chiaki.R
import android.content.Intent
import android.net.Uri

/** Open the owner's existing Ko-fi profile; payments are handled by that service. */
class SupportActivity : DeckivoActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = DeckivoUi.screen(this, getString(R.string.dv_support), getString(R.string.dv_support_note))
        val funding = DeckivoUi.section(root, getString(R.string.dv_support))
        DeckivoUi.label(funding, getString(R.string.dv_support_body))
        DeckivoUi.label(funding, getString(R.string.dv_support_status), 16f, true)
        DeckivoUi.button(funding, "Ko-fi · RemTeh ↗", true) {
            runCatching { startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://ko-fi.com/pavelzayats"))) }
        }
        val contribute = DeckivoUi.section(root, getString(R.string.dv_contribute))
        DeckivoUi.label(contribute, getString(R.string.dv_contribute_body))
    }
}
