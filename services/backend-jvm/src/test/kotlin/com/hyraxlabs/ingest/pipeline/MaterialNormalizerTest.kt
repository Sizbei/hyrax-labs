package com.hyraxlabs.ingest.pipeline

import com.hyraxlabs.ingest.domain.MaterialCategory
import com.hyraxlabs.ingest.domain.SupplierRecord
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class MaterialNormalizerTest {

    private val normalizer = MaterialNormalizer()

    private fun record(
        quantity: String?,
        unit: String?,
        name: String = "Aluminum Sheet 6061",
        category: String? = "metal",
    ) = SupplierRecord(
        partnerId = "X-1",
        partnerSource = "test",
        name = name,
        rawCategory = category,
        rawQuantity = quantity,
        rawUnit = unit,
        reportedAt = null,
    )

    @Test
    fun `kilograms pass through and strip thousands separators`() {
        val material = normalizer.normalize(record("1,200", "kg"))!!
        assertEquals(1200.0, material.quantityKg, 1e-6)
    }

    @Test
    fun `pounds are converted to kilograms`() {
        val material = normalizer.normalize(record("100", "lbs"))!!
        assertEquals(45.359237, material.quantityKg, 1e-6)
    }

    @Test
    fun `metric tons are converted to kilograms`() {
        val material = normalizer.normalize(record("0.75", "tonne"))!!
        assertEquals(750.0, material.quantityKg, 1e-6)
    }

    @Test
    fun `unparseable quantity yields null`() {
        assertNull(normalizer.normalize(record("n/a", "kg")))
    }

    @Test
    fun `unknown unit yields null`() {
        assertNull(normalizer.normalize(record("10", "furlongs")))
    }

    @Test
    fun `category labels resolve to canonical categories`() {
        assertEquals(MaterialCategory.POLYMER, normalizer.normalize(record("1", "kg", category = "plastic"))!!.category)
        assertEquals(MaterialCategory.TEXTILE, normalizer.normalize(record("1", "kg", category = "fabric"))!!.category)
        assertEquals(MaterialCategory.OTHER, normalizer.normalize(record("1", "kg", category = "mystery"))!!.category)
    }

    @Test
    fun `canonical key is deterministic and category-scoped`() {
        val a = normalizer.normalize(record("1", "kg", name = "Aluminum Sheet 6061"))!!
        val b = normalizer.normalize(record("999", "kg", name = "aluminum  sheet 6061"))!!
        assertEquals(a.canonicalKey, b.canonicalKey)
        assertTrue(a.canonicalKey.startsWith("metal:"))
    }

    @Test
    fun `normalizeAll drops bad rows but keeps good ones`() {
        val results = normalizer.normalizeAll(
            listOf(
                record("100", "kg"),
                record("bad", "kg"),
                record("5", "lbs"),
            ),
        )
        assertEquals(2, results.size)
    }
}
