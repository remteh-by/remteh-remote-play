// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.main

import com.metallic.chiaki.common.*
import com.metallic.chiaki.discovery.serverMac
import com.metallic.chiaki.lib.DiscoveryHost
import java.util.Locale

/** A saved endpoint and its live discovery are one card, without changing Room. */
internal object DisplayHostMerger {
    fun merge(manual: List<ManualHost>, registered: List<RegisteredHost>, discovered: List<DiscoveryHost>): List<DisplayHost> {
        val byId = registered.associateBy { it.id }
        val byMac = registered.associateBy { it.serverMac }
        val saved = manual.distinctBy { it.registeredHost to address(it.host).ifEmpty { "manual:${it.id}" } }
            .map { ManualDisplayHost(it.registeredHost?.let(byId::get), it) }

        // Discovery can report one console through multiple interfaces or states.
        val live = linkedMapOf<String, DiscoveryHost>()
        discovered.forEachIndexed { index, host ->
            val mac = mac(host)
            val endpoint = address(host.hostAddr.orEmpty())
            val key = when {
                mac != null -> "mac:${mac.value}"
                endpoint.isNotEmpty() -> "address:${host.isPS5}:$endpoint"
                else -> "unknown:$index"
            }
            val previous = live[key]
            if (previous == null || rank(host) > rank(previous)) live[key] = host
        }

        val found = live.values.map { host ->
            val mac = mac(host)
            // Prefer the profile selected for the saved endpoint, not an arbitrary
            // other user's registration for the same physical console.
            val bookmark = saved.firstOrNull { mac != null && it.registeredHost?.serverMac == mac }
                ?: saved.firstOrNull { it.registeredHost == null && sameAddress(it.host, host.hostAddr.orEmpty()) }
            DiscoveredDisplayHost(bookmark?.registeredHost ?: mac?.let(byMac::get), host, bookmark?.manualHost)
        }
        val remaining = saved.filter { bookmark ->
            found.none { host ->
                val savedProfile = bookmark.registeredHost
                if (savedProfile != null) host.registeredHost?.id == savedProfile.id
                else host.manualHost?.id == bookmark.manualHost.id
            }
        }
        return found + remaining
    }

    private fun mac(host: DiscoveryHost): MacAddress? = runCatching { host.serverMac }.getOrNull()
    private fun address(host: String) = host.trim().removeSurrounding("[", "]").lowercase(Locale.ROOT)
    private fun sameAddress(a: String, b: String) = address(a).let { it.isNotEmpty() && it == address(b) }
    private fun rank(host: DiscoveryHost) = (if (host.hostAddr.isNullOrBlank()) 0 else 4) + when (host.state) {
        DiscoveryHost.State.READY -> 2
        DiscoveryHost.State.STANDBY -> 1
        else -> 0
    }
}
