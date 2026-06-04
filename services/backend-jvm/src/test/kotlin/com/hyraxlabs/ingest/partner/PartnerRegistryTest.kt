package com.hyraxlabs.ingest.partner

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class PartnerRegistryTest {

    @Test
    fun `of indexes clients by source`() {
        val registry = PartnerRegistry.of(SampleAlphaPartnerClient(), LegacyBetaPartnerClient())
        assertEquals(2, registry.all().size)
        assertTrue(SampleAlphaPartnerClient.SOURCE in registry.sources)
        assertTrue(LegacyBetaPartnerClient.SOURCE in registry.sources)
    }

    @Test
    fun `register is immutable and returns a new registry`() {
        val empty = PartnerRegistry.empty()
        val withAlpha = empty.register(SampleAlphaPartnerClient())
        assertEquals(0, empty.all().size)
        assertEquals(1, withAlpha.all().size)
    }

    @Test
    fun `get returns null for unknown source`() {
        assertNull(PartnerRegistry.empty().get("nope"))
    }
}
