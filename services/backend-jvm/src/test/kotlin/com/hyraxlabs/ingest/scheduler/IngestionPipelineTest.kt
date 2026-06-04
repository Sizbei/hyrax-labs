package com.hyraxlabs.ingest.scheduler

import com.hyraxlabs.ingest.domain.JobStatus
import com.hyraxlabs.ingest.domain.SupplierRecord
import com.hyraxlabs.ingest.partner.LegacyBetaPartnerClient
import com.hyraxlabs.ingest.partner.PartnerApiClient
import com.hyraxlabs.ingest.partner.PartnerApiException
import com.hyraxlabs.ingest.partner.PartnerRegistry
import com.hyraxlabs.ingest.partner.SampleAlphaPartnerClient
import com.hyraxlabs.ingest.pipeline.Deduplicator
import com.hyraxlabs.ingest.pipeline.MaterialNormalizer
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class IngestionPipelineTest {

    private fun TestScope.pipeline(registry: PartnerRegistry, queue: JobQueue) = IngestionPipeline(
        registry = registry,
        normalizer = MaterialNormalizer(),
        deduplicator = Deduplicator(),
        jobQueue = queue,
        // Run "I/O" on the test dispatcher so the virtual clock stays in control.
        ioDispatcher = StandardTestDispatcher(testScheduler),
    )

    @Test
    fun `cycle ingests both partners and deduplicates cross-partner overlap`() = runTest {
        val queue = JobQueue()
        val registry = PartnerRegistry.of(SampleAlphaPartnerClient(), LegacyBetaPartnerClient())
        val materials = pipeline(registry, queue).runCycle()

        // The two feeds both report "Aluminum Sheet 6061"; dedup must collapse it.
        val aluminum = materials.filter { it.name.equals("Aluminum Sheet 6061", ignoreCase = true) }
        assertEquals(1, aluminum.size)
        assertTrue(materials.isNotEmpty())

        // Both partners should have completed jobs recorded.
        val jobs = queue.snapshot()
        assertEquals(2, jobs.size)
        assertTrue(jobs.all { it.status == JobStatus.COMPLETED })
    }

    @Test
    fun `a failing partner is isolated and recorded as failed`() = runTest {
        val failing = object : PartnerApiClient {
            override val source = "broken-feed"
            override fun fetchRecords(): List<SupplierRecord> =
                throw PartnerApiException("feed offline")
        }
        val queue = JobQueue()
        val registry = PartnerRegistry.of(SampleAlphaPartnerClient(), failing)
        val materials = pipeline(registry, queue).runCycle()

        // Alpha still produces materials despite the other partner failing.
        assertTrue(materials.isNotEmpty())
        val broken = queue.snapshot().first { it.partnerSource == "broken-feed" }
        assertEquals(JobStatus.FAILED, broken.status)
        assertEquals("feed offline", broken.errorMessage)
    }

    @Test
    fun `an unexpected runtime error in a partner is also isolated`() = runTest {
        // Not a declared PartnerApiException — a stray runtime fault (e.g. a real
        // HTTP client throwing). It must still be contained, not abort the cycle.
        val exploding = object : PartnerApiClient {
            override val source = "exploding-feed"
            override fun fetchRecords(): List<SupplierRecord> =
                throw IllegalStateException("unexpected NPE-style fault")
        }
        val queue = JobQueue()
        val registry = PartnerRegistry.of(SampleAlphaPartnerClient(), exploding)
        val materials = pipeline(registry, queue).runCycle()

        assertTrue(materials.isNotEmpty(), "healthy partner must still yield materials")
        val broken = queue.snapshot().first { it.partnerSource == "exploding-feed" }
        assertEquals(JobStatus.FAILED, broken.status)
        assertEquals("unexpected NPE-style fault", broken.errorMessage)
    }
}
