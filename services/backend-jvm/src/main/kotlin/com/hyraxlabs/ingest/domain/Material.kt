package com.hyraxlabs.ingest.domain

/**
 * A normalized, canonical material record produced by the pipeline.
 *
 * Quantities are always expressed in kilograms and categories are resolved to a
 * known [MaterialCategory]. The [canonicalKey] is used for cross-partner
 * deduplication.
 */
data class Material(
    /** Deterministic key used to detect duplicates across partners. */
    val canonicalKey: String,
    val name: String,
    val category: MaterialCategory,
    /** Quantity normalized to kilograms. */
    val quantityKg: Double,
    val sourcePartner: String,
    val sourcePartnerId: String,
) {
    init {
        require(canonicalKey.isNotBlank()) { "canonicalKey must not be blank" }
        require(quantityKg >= 0.0) { "quantityKg must be non-negative, was $quantityKg" }
    }
}
