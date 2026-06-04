package com.hyraxlabs.ingest.domain

/**
 * The unit of measure a supplier reports a material quantity in.
 * Partner feeds use inconsistent units, so the pipeline normalizes
 * everything to [MaterialUnit.KILOGRAM] downstream.
 */
enum class MaterialUnit {
    KILOGRAM,
    POUND,
    METRIC_TON,
    UNKNOWN;

    companion object {
        /** Lenient parse used when reading free-form partner unit strings. */
        fun fromRaw(raw: String?): MaterialUnit = when (raw?.trim()?.lowercase()) {
            "kg", "kilogram", "kilograms" -> KILOGRAM
            "lb", "lbs", "pound", "pounds" -> POUND
            "t", "ton", "tonne", "metric_ton", "metric ton" -> METRIC_TON
            else -> UNKNOWN
        }
    }
}

/**
 * Broad classification of a supplier material, derived during normalization.
 */
enum class MaterialCategory {
    METAL,
    POLYMER,
    COMPOSITE,
    TEXTILE,
    OTHER
}

/** Lifecycle state of an asynchronous processing job. */
enum class JobStatus {
    PENDING,
    RUNNING,
    COMPLETED,
    FAILED
}
