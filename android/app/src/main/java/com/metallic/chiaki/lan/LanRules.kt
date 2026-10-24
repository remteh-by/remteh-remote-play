// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.lan

/** Numeric private IPv4 only: no DNS lookups, public hosts, redirects or URLs. */
object LanRules {
    fun isPrivateIpv4(input: String): Boolean {
        val parts = input.split('.')
        if (parts.size != 4) return false
        val octets = parts.map {
            if (it.isEmpty() || it.length > 3 || it.any { c -> c !in '0'..'9' } ||
                (it.length > 1 && it[0] == '0')) return false
            it.toIntOrNull()?.takeIf { n -> n in 0..255 } ?: return false
        }
        if (octets[3] == 0 || octets[3] == 255) return false
        return octets[0] == 10 || (octets[0] == 172 && octets[1] in 16..31) ||
            (octets[0] == 192 && octets[1] == 168)
    }

    fun isEightDigitCode(input: String) = input.length == 8 && input.all { it in '0'..'9' }

    // 8 bytes encode to 11 base64 characters followed by ONE padding character.
    fun looksLikeAccountId(input: String) = Regex("[A-Za-z0-9+/]{11}=").matches(input)
}
