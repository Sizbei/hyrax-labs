package com.hyraxlabs.ingest.pipeline

import com.hyraxlabs.ingest.domain.Material

/**
 * Collapses materials that share a [Material.canonicalKey] across partner feeds.
 *
 * Strategy: keep the first occurrence of each canonical key (stable, input-order
 * preserving) and discard later duplicates. Pure function — no shared state — so
 * it is safe to call concurrently from multiple ingestion jobs.
 */
class Deduplicator {

    /** Returns the deduplicated list and preserves first-seen ordering. */
    fun deduplicate(materials: List<Material>): List<Material> =
        materials.distinctBy { it.canonicalKey }

    /** Count of duplicate records that [deduplicate] would remove. */
    fun duplicateCount(materials: List<Material>): Int =
        materials.size - materials.distinctBy { it.canonicalKey }.size
}
