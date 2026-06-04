package com.hyraxlabs.ingest

import com.hyraxlabs.ingest.partner.LegacyBetaPartnerClient
import com.hyraxlabs.ingest.partner.PartnerRegistry
import com.hyraxlabs.ingest.partner.SampleAlphaPartnerClient
import com.hyraxlabs.ingest.pipeline.Deduplicator
import com.hyraxlabs.ingest.pipeline.MaterialNormalizer
import com.hyraxlabs.ingest.scheduler.IngestionPipeline
import com.hyraxlabs.ingest.scheduler.JobQueue
import com.hyraxlabs.ingest.scheduler.JobScheduler
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.runBlocking
import org.slf4j.LoggerFactory

/**
 * Demo entry point for the supplier-material ingestion service.
 *
 * Wires the partner registry, pipeline, job queue and scheduler together, then
 * runs a small number of ingestion cycles and logs the results. All partner data
 * is SYNTHETIC.
 */
private val log = LoggerFactory.getLogger("com.hyraxlabs.ingest.App")

fun main() = runBlocking {
    log.info("Starting Hyrax Labs supplier-material ingestion service (demo mode)")

    // Wire dependencies — one Kotlin partner client, one Java partner client.
    val registry = PartnerRegistry.of(
        SampleAlphaPartnerClient(),
        LegacyBetaPartnerClient(),
    )
    val jobQueue = JobQueue()
    val pipeline = IngestionPipeline(
        registry = registry,
        normalizer = MaterialNormalizer(),
        deduplicator = Deduplicator(),
        jobQueue = jobQueue,
    )

    log.info("Registered partners: {}", registry.sources.joinToString(", "))

    // Run a bounded set of cycles for the demo (a real deployment would schedule
    // these indefinitely via JobScheduler.start(interval)).
    coroutineScope {
        val scheduler = JobScheduler(this, pipeline)
        repeat(DEMO_CYCLES) {
            val materials = scheduler.runOnce { results ->
                log.info("Normalized {} unique materials this cycle:", results.size)
                results.forEach { m ->
                    log.info(
                        "  - {} [{}] {} kg (from {})",
                        m.name, m.category, "%.2f".format(m.quantityKg), m.sourcePartner,
                    )
                }
            }
            check(materials.isNotEmpty()) { "demo cycle produced no materials" }
        }
    }

    log.info("Job summary:")
    jobQueue.snapshot().forEach { job ->
        log.info(
            "  job={} partner={} status={} produced={}",
            job.id.take(8), job.partnerSource, job.status, job.producedCount,
        )
    }
    log.info("Demo complete. All data shown is synthetic.")
}

private const val DEMO_CYCLES = 2
