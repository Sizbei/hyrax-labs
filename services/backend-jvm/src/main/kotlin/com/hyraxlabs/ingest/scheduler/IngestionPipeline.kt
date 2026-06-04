package com.hyraxlabs.ingest.scheduler

import com.hyraxlabs.ingest.domain.Material
import com.hyraxlabs.ingest.domain.ProcessingJob
import com.hyraxlabs.ingest.partner.PartnerApiClient
import com.hyraxlabs.ingest.partner.PartnerApiException
import com.hyraxlabs.ingest.partner.PartnerRegistry
import com.hyraxlabs.ingest.pipeline.Deduplicator
import com.hyraxlabs.ingest.pipeline.MaterialNormalizer
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withContext
import org.slf4j.LoggerFactory

/**
 * Orchestrates a single ingestion cycle: fetch → normalize → deduplicate.
 *
 * Per-partner fetches run concurrently as child coroutines. Each partner gets its
 * own [ProcessingJob] tracked in the [JobQueue], so a failure in one partner feed
 * is isolated and does not abort the others.
 *
 * The [ioDispatcher] used for (blocking) partner I/O is injectable so tests can
 * substitute a deterministic test dispatcher; production uses [Dispatchers.IO].
 */
class IngestionPipeline(
    private val registry: PartnerRegistry,
    private val normalizer: MaterialNormalizer,
    private val deduplicator: Deduplicator,
    private val jobQueue: JobQueue,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) {
    private val log = LoggerFactory.getLogger(IngestionPipeline::class.java)

    /**
     * Runs one full ingestion cycle across all registered partners concurrently
     * and returns the deduplicated, normalized materials.
     */
    suspend fun runCycle(): List<Material> = coroutineScope {
        val perPartner = registry.all().map { client ->
            async(ioDispatcher) { ingestPartner(client) }
        }.awaitAll()

        val combined = perPartner.flatten()
        val deduped = deduplicator.deduplicate(combined)
        log.info(
            "Cycle complete: {} raw normalized, {} after dedup ({} duplicates removed)",
            combined.size, deduped.size, combined.size - deduped.size,
        )
        deduped
    }

    /** Ingests a single partner, recording job lifecycle in the queue. */
    private suspend fun ingestPartner(client: PartnerApiClient): List<Material> {
        val job = jobQueue.enqueue(ProcessingJob(partnerSource = client.source))
        jobQueue.update(job.id) { it.running() }
        return try {
            // Partner I/O is blocking; keep it off the default dispatcher.
            val records = withContext(ioDispatcher) { client.fetchRecords() }
            val materials = normalizer.normalizeAll(records)
            jobQueue.update(job.id) { it.completed(materials.size) }
            log.info("Partner '{}' ingested {} materials", client.source, materials.size)
            materials
        } catch (ex: PartnerApiException) {
            jobQueue.update(job.id) { it.failed(ex.message ?: "partner feed error") }
            log.error("Partner '{}' ingestion failed: {}", client.source, ex.message)
            emptyList()
        }
    }
}
