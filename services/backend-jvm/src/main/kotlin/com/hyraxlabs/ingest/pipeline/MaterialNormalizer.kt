package com.hyraxlabs.ingest.pipeline

import com.hyraxlabs.ingest.domain.Material
import com.hyraxlabs.ingest.domain.MaterialCategory
import com.hyraxlabs.ingest.domain.MaterialUnit
import com.hyraxlabs.ingest.domain.SupplierRecord
import com.hyraxlabs.ingest.partner.QuantityStrings
import org.slf4j.LoggerFactory

/**
 * Maps raw [SupplierRecord]s from partner feeds into canonical [Material]s.
 *
 * Responsibilities:
 *  - parse messy quantity strings (delegating cleanup to the Java [QuantityStrings] util),
 *  - convert all quantities to kilograms,
 *  - resolve free-form category labels to a known [MaterialCategory],
 *  - derive a deterministic [Material.canonicalKey] for cross-partner dedup.
 *
 * Records that cannot be normalized (e.g. unparseable quantity) are dropped and
 * logged rather than throwing, so one bad row never fails an entire batch.
 */
class MaterialNormalizer {

    private val log = LoggerFactory.getLogger(MaterialNormalizer::class.java)

    /** Normalizes a batch, silently skipping records that fail validation. */
    fun normalizeAll(records: List<SupplierRecord>): List<Material> =
        records.mapNotNull { normalize(it) }

    /** Normalizes a single record, returning null if it cannot be canonicalized. */
    fun normalize(record: SupplierRecord): Material? {
        val quantity = parseQuantityKg(record.rawQuantity, record.rawUnit)
        if (quantity == null) {
            log.warn(
                "Dropping record {}:{} — unparseable quantity '{}' '{}'",
                record.partnerSource, record.partnerId, record.rawQuantity, record.rawUnit,
            )
            return null
        }

        val category = resolveCategory(record.rawCategory)
        return Material(
            canonicalKey = canonicalKey(record.name, category),
            name = record.name.trim(),
            category = category,
            quantityKg = quantity,
            sourcePartner = record.partnerSource,
            sourcePartnerId = record.partnerId,
        )
    }

    /** Parses a raw quantity + unit into kilograms, or null when not numeric. */
    private fun parseQuantityKg(rawQuantity: String?, rawUnit: String?): Double? {
        val cleaned = QuantityStrings.clean(rawQuantity)
        val value = cleaned.toDoubleOrNull() ?: return null
        if (value < 0) return null
        return when (MaterialUnit.fromRaw(rawUnit)) {
            MaterialUnit.KILOGRAM -> value
            MaterialUnit.POUND -> value * KG_PER_POUND
            MaterialUnit.METRIC_TON -> value * KG_PER_METRIC_TON
            MaterialUnit.UNKNOWN -> null
        }
    }

    private fun resolveCategory(raw: String?): MaterialCategory =
        when (raw?.trim()?.lowercase()) {
            "metal", "metals" -> MaterialCategory.METAL
            "polymer", "plastic" -> MaterialCategory.POLYMER
            "composite" -> MaterialCategory.COMPOSITE
            "textile", "fabric" -> MaterialCategory.TEXTILE
            else -> MaterialCategory.OTHER
        }

    /**
     * Builds a deterministic key from the material name and category so the same
     * physical material reported by different partners collapses to one key.
     */
    private fun canonicalKey(name: String, category: MaterialCategory): String {
        val slug = name.trim().lowercase().replace(Regex("\\s+"), "-")
        return "${category.name.lowercase()}:$slug"
    }

    private companion object {
        const val KG_PER_POUND = 0.45359237
        const val KG_PER_METRIC_TON = 1000.0
    }
}
