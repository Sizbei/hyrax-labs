package com.hyraxlabs.ingest.domain

/**
 * A raw, un-normalized material record as returned by a third-party partner API.
 *
 * Field shapes intentionally reflect the messiness of external feeds: quantities
 * and units arrive as free-form strings and the partner-side identifier is opaque.
 * Normalization into [Material] happens in the pipeline layer.
 */
data class SupplierRecord(
    /** Identifier assigned by the originating partner. Not globally unique. */
    val partnerId: String,
    /** Stable id of the partner that produced this record. */
    val partnerSource: String,
    /** Human-readable material name as supplied by the partner. */
    val name: String,
    /** Raw category label from the partner; may be null or non-canonical. */
    val rawCategory: String?,
    /** Quantity as a raw string (partners send "1,200", "1200.0", etc.). */
    val rawQuantity: String?,
    /** Raw unit token (e.g. "kg", "lbs", "tonne"). */
    val rawUnit: String?,
    /** ISO-8601 timestamp string as reported by the partner, if any. */
    val reportedAt: String?,
)
