package com.metallic.chiaki.lan

import org.junit.Assert.*
import org.junit.Test

class LanRulesTest {
    @Test fun privateUnicastOnly() {
        listOf("192.168.31.77", "10.0.0.1", "172.16.0.1", "172.31.255.254").forEach { assertTrue(it, LanRules.isPrivateIpv4(it)) }
        listOf("127.0.0.1", "0.0.0.0", "8.8.8.8", "172.32.0.1", "192.168.31.255",
            "192.168.31.0", "192.168.031.77", "localhost", "http://192.168.31.77", "192.168.31.77:80",
            "192.168.31.256", "192.168.31.77\n", "192.168.31.-1", "192.168.31", "::1").forEach { assertFalse(it, LanRules.isPrivateIpv4(it)) }
    }
    @Test fun pinIsDecimalAndKeepsLeadingZeros() {
        assertTrue(LanRules.isEightDigitCode("00000001"))
        listOf("", "1234567", "123456789", "1234567a", "１２３４５６７８", "1234 5678").forEach { assertFalse(LanRules.isEightDigitCode(it)) }
    }
    @Test fun accountIsEightByteBase64NotDisplayName() {
        assertTrue(LanRules.looksLikeAccountId("AQIDBAUGBwg="))
        assertFalse(LanRules.looksLikeAccountId("AQIDBAUGBwg=="))
        assertFalse(LanRules.looksLikeAccountId("PlayerName"))
    }
}
