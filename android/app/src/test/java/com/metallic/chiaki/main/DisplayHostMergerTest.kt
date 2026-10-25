package com.metallic.chiaki.main

import com.metallic.chiaki.common.*
import com.metallic.chiaki.lib.DiscoveryHost
import com.metallic.chiaki.lib.Target
import org.junit.Assert.*
import org.junit.Test

class DisplayHostMergerTest {
    private val firstMac = "01:02:03:04:05:06"
    private val secondMac = "11:12:13:14:15:16"
    private fun profile(id: Long = 7, mac: String = firstMac) = RegisteredHost(
        id, Target.PS5_1, null, null, null, null, MacAddress(mac), "Test PS5", ByteArray(16), 0, ByteArray(16))
    private fun saved(id: Long = 41, address: String = "192.0.2.10", profileId: Long? = 7) = ManualHost(id, address, profileId)
    private fun live(mac: String? = firstMac, address: String? = "192.0.2.10", state: DiscoveryHost.State = DiscoveryHost.State.READY) = DiscoveryHost(
        state, 9302U, address, null, "00030010", "Test PS5", null, mac?.replace(":", ""), null, null)

    @Test fun liveAndSavedConsoleShareOneCardAndKeepBookmarkActions() {
        val p = profile(); val m = saved()
        val cards = DisplayHostMerger.merge(listOf(m), listOf(p), listOf(live()))
        assertEquals(1, cards.size)
        assertTrue(cards.single() is DiscoveredDisplayHost)
        assertSame(p, cards.single().registeredHost)
        assertEquals(m, cards.single().manualHost)
    }
    @Test fun savedAddressReturnsWhenDiscoveryIsOffOrEmpty() {
        val m = saved()
        val cards = DisplayHostMerger.merge(listOf(m), listOf(profile()), emptyList())
        assertEquals(1, cards.size)
        assertTrue(cards.single() is ManualDisplayHost)
        assertEquals(m, cards.single().manualHost)
    }
    @Test fun changedAddressStillMatchesHardwareIdentity() {
        val cards = DisplayHostMerger.merge(listOf(saved()), listOf(profile()), listOf(live(address="192.0.2.20")))
        assertEquals(1, cards.size)
        assertEquals("192.0.2.20", cards.single().host)
        assertEquals("192.0.2.10", cards.single().manualHost?.host)
    }
    @Test fun differentConsoleWithSameNameAndReusedIpDoesNotReceiveSavedCredentials() {
        val cards = DisplayHostMerger.merge(listOf(saved()), listOf(profile()), listOf(live(mac=secondMac)))
        assertEquals(2, cards.size)
        assertNull(cards.filterIsInstance<DiscoveredDisplayHost>().single().registeredHost)
        assertNotNull(cards.filterIsInstance<ManualDisplayHost>().single().registeredHost)
    }
    @Test fun unregisteredBookmarkCanMergeWithDiscoveryWithoutInventingCredentials() {
        val m = saved(profileId=null)
        val cards = DisplayHostMerger.merge(listOf(m), emptyList(), listOf(live()))
        assertEquals(1, cards.size)
        assertNull(cards.single().registeredHost)
        assertEquals(m, cards.single().manualHost)
    }
    @Test fun duplicateDiscoveryUsesReadyStatusAndKeepsOtherConsoles() {
        val cards = DisplayHostMerger.merge(listOf(saved()), listOf(profile()), listOf(
            live(state=DiscoveryHost.State.STANDBY), live(), live(mac=secondMac,address="192.0.2.11")))
        assertEquals(2, cards.size)
        assertEquals(DiscoveryHost.State.READY, (cards.first() as DiscoveredDisplayHost).discoveredHost.state)
    }
    @Test fun alternateUserRegistrationIsPreservedAndExplicitBookmarkWins() {
        val a = profile(); val b = profile(id=8)
        val cards = DisplayHostMerger.merge(listOf(saved(),saved(id=42,profileId=8)), listOf(a,b), listOf(live()))
        assertEquals(2, cards.size)
        assertEquals(7L, cards.first().registeredHost?.id)
        assertEquals(8L, cards.last().registeredHost?.id)
    }
    @Test fun duplicateSavedEndpointIsOneCardWhileBlankUnknownDevicesStayDistinct() {
        val offline = DisplayHostMerger.merge(listOf(saved(),saved(id=42)), listOf(profile()), emptyList())
        assertEquals(1, offline.size)
        val unknown = DisplayHostMerger.merge(emptyList(),emptyList(),listOf(live(mac=null,address=null),live(mac=null,address=null)))
        assertEquals(2, unknown.size)
    }
}
