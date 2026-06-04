package com.hyraxlabs.ingest.partner

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class PartnerClientTest {

    @Test
    fun `kotlin alpha client returns synthetic records tagged with its source`() {
        val client = SampleAlphaPartnerClient()
        val records = client.fetchRecords()
        assertTrue(records.isNotEmpty())
        assertTrue(records.all { it.partnerSource == SampleAlphaPartnerClient.SOURCE })
    }

    @Test
    fun `java legacy client implements the kotlin interface and tags its source`() {
        // Exercises Java -> Kotlin interop: a Java class satisfying a Kotlin interface.
        val client: PartnerApiClient = LegacyBetaPartnerClient()
        assertEquals(LegacyBetaPartnerClient.SOURCE, client.source)
        val records = client.fetchRecords()
        assertTrue(records.isNotEmpty())
        assertTrue(records.all { it.partnerSource == LegacyBetaPartnerClient.SOURCE })
    }

    @Test
    fun `java quantity util cleans separators and rejects garbage`() {
        assertEquals("1200", QuantityStrings.clean("1,200"))
        assertEquals("550.5", QuantityStrings.clean("  550.5 "))
        assertEquals("", QuantityStrings.clean(null))
        assertEquals("", QuantityStrings.clean("   "))
    }
}
