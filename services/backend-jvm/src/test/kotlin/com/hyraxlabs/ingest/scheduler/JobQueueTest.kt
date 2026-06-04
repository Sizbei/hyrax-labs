package com.hyraxlabs.ingest.scheduler

import com.hyraxlabs.ingest.domain.JobStatus
import com.hyraxlabs.ingest.domain.ProcessingJob
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class JobQueueTest {

    @Test
    fun `enqueue then get round-trips a job`() = runTest {
        val queue = JobQueue()
        val job = queue.enqueue(ProcessingJob(partnerSource = "alpha"))
        assertEquals(job, queue.get(job.id))
        assertEquals(1, queue.size())
    }

    @Test
    fun `update applies lifecycle transition atomically`() = runTest {
        val queue = JobQueue()
        val job = queue.enqueue(ProcessingJob(partnerSource = "alpha"))
        queue.update(job.id) { it.running() }
        val done = queue.update(job.id) { it.completed(5) }!!
        assertEquals(JobStatus.COMPLETED, done.status)
        assertEquals(5, done.producedCount)
    }

    @Test
    fun `update of unknown job returns null`() = runTest {
        assertNull(JobQueue().update("missing") { it })
    }

    @Test
    fun `concurrent enqueues are all recorded`() = runTest {
        val queue = JobQueue()
        coroutineScope {
            (1..50).map { i ->
                async { queue.enqueue(ProcessingJob(partnerSource = "p$i")) }
            }.awaitAll()
        }
        assertEquals(50, queue.size())
    }
}
