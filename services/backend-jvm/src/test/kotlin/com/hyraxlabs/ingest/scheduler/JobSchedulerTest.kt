package com.hyraxlabs.ingest.scheduler

import com.hyraxlabs.ingest.partner.LegacyBetaPartnerClient
import com.hyraxlabs.ingest.partner.PartnerRegistry
import com.hyraxlabs.ingest.partner.SampleAlphaPartnerClient
import com.hyraxlabs.ingest.pipeline.Deduplicator
import com.hyraxlabs.ingest.pipeline.MaterialNormalizer
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import kotlin.time.Duration.Companion.milliseconds

class JobSchedulerTest {

    private fun TestScope.newPipeline(queue: JobQueue) = IngestionPipeline(
        registry = PartnerRegistry.of(SampleAlphaPartnerClient(), LegacyBetaPartnerClient()),
        normalizer = MaterialNormalizer(),
        deduplicator = Deduplicator(),
        jobQueue = queue,
        ioDispatcher = StandardTestDispatcher(testScheduler),
    )

    @Test
    fun `runOnce executes a single cycle and increments the counter`() = runTest {
        val scheduler = JobScheduler(this, newPipeline(JobQueue()))
        val results = scheduler.runOnce()
        assertTrue(results.isNotEmpty())
        assertEquals(1, scheduler.completedCycles)
    }

    @Test
    fun `start runs repeatedly on interval until cancelled`() = runTest {
        // runTest's virtual clock advances delay() instantly, so this is fast.
        val scheduler = JobScheduler(this, newPipeline(JobQueue()))
        val job = scheduler.start(interval = 10.milliseconds)
        delay(35.milliseconds) // long enough for several cycles on the virtual clock
        job.cancel()
        assertTrue(scheduler.completedCycles >= 3, "expected >=3 cycles, got ${scheduler.completedCycles}")
    }

    @Test
    fun `onCycle callback receives each cycle's results`() = runTest {
        var observed = -1
        val scheduler = JobScheduler(this, newPipeline(JobQueue()))
        scheduler.runOnce { results -> observed = results.size }
        assertTrue(observed > 0)
    }
}
