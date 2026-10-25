package com.metallic.chiaki.updates

import org.junit.Assert.*
import org.junit.Test
import java.security.KeyPairGenerator
import java.security.Signature
import java.util.Base64

class PrivateChannelTest {
    @Test fun privateAssetsCannotChangeOriginOrTraverse() {
        val base = "http://10.0.0.10/private/"
        assertTrue(PrivateChannel.sameOriginAsset(base, base + "index.json"))
        assertFalse(PrivateChannel.sameOriginAsset(base, "http://192.168.0.161/private/index.json"))
        assertFalse(PrivateChannel.sameOriginAsset(base, base + "../index.json"))
        assertFalse(PrivateChannel.sameOriginAsset(base, base + "%2e%2e/index.json"))
        assertFalse(PrivateChannel.sameOriginAsset(base, base + "index.json?redirect=1"))
        assertFalse(PrivateChannel.sameOriginAsset("http://example.com/private/", "http://example.com/private/index.json"))
        assertFalse(PrivateChannel.sameOriginAsset("https://user:secret@example.com/private/", "https://example.com/private/index.json"))
        assertTrue(PrivateChannel.sameOriginAsset("https://example.com/private/", "https://example.com/private/index.sig"))
    }

    @Test fun tamperingAndForeignSignersAreRejected() {
        val generator = KeyPairGenerator.getInstance("RSA").apply { initialize(2048) }
        val key = generator.generateKeyPair()
        val payload = "{\"schema\":1,\"packages\":[]}".toByteArray()
        val signer = Signature.getInstance("SHA256withRSA")
        signer.initSign(key.private); signer.update(payload)
        val signature = Base64.getEncoder().encode(signer.sign())
        PrivateChannel.verify(payload, signature, key.public.encoded)
        assertThrows(IllegalArgumentException::class.java) { PrivateChannel.verify(payload + 32.toByte(), signature, key.public.encoded) }
        assertThrows(IllegalArgumentException::class.java) { PrivateChannel.verify(payload, signature, generator.generateKeyPair().public.encoded) }
    }

    @Test fun installedAndOlderVersionsAreNeverSelected() {
        val row = PrivatePackage("android-arm64", "0.5.1", 17, "Deckivo.apk", 100, "a".repeat(64))
        val index = PrivateIndex(1, listOf(row))
        assertEquals(17L, PrivateChannel.choose(index, 16, "0.5.1", 35)?.build)
        assertNull(PrivateChannel.choose(index, 17, "0.5.1", 35))
        assertNull(PrivateChannel.choose(index, 16, "0.6.0", 35))
        assertNull(PrivateChannel.choose(index, 16, "0.5.1", 25))
    }
}
