package com.hyraxlabs.ingest.pipeline

import com.hyraxlabs.ingest.domain.Material
import com.hyraxlabs.ingest.domain.MaterialCategory
import kotlin.test.Test
import kotlin.test.assertEquals

class DeduplicatorTest {

    private val deduplicator = Deduplicator()

    private fun material(key: String, partner: String) = Material(
        canonicalKey = key,
        name = key,
        category = MaterialCategory.METAL,
        quantityKg = 1.0,
        sourcePartner = partner,
        sourcePartnerId = "id",
    )

    @Test
    fun `removes records sharing a canonical key keeping first seen`() {
        val input = listOf(
            material("metal:steel", "alpha"),
            material("metal:steel", "beta"),
            material("polymer:nylon", "beta"),
        )
        val result = deduplicator.deduplicate(input)
        assertEquals(2, result.size)
        assertEquals("alpha", result.first { it.canonicalKey == "metal:steel" }.sourcePartner)
    }

    @Test
    fun `duplicateCount reports number removed`() {
        val input = listOf(
            material("metal:steel", "alpha"),
            material("metal:steel", "beta"),
            material("metal:steel", "gamma"),
        )
        assertEquals(2, deduplicator.duplicateCount(input))
    }

    @Test
    fun `empty input is handled`() {
        assertEquals(emptyList(), deduplicator.deduplicate(emptyList()))
        assertEquals(0, deduplicator.duplicateCount(emptyList()))
    }
}
