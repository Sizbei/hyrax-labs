package com.hyraxlabs.ingest.scheduler

import com.hyraxlabs.ingest.domain.ProcessingJob
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/**
 * Thread-safe, in-memory record of [ProcessingJob]s and their lifecycle.
 *
 * Concurrent ingestion coroutines enqueue and update jobs here; access is guarded
 * by a coroutine [Mutex] so the queue is safe under structured concurrency without
 * blocking threads. State snapshots are returned as immutable copies.
 */
class JobQueue {

    private val mutex = Mutex()
    private val jobs = mutableMapOf<String, ProcessingJob>()

    suspend fun enqueue(job: ProcessingJob): ProcessingJob = mutex.withLock {
        jobs[job.id] = job
        job
    }

    /** Atomically applies [transform] to the stored job and persists the result. */
    suspend fun update(jobId: String, transform: (ProcessingJob) -> ProcessingJob): ProcessingJob? =
        mutex.withLock {
            val current = jobs[jobId] ?: return@withLock null
            val next = transform(current)
            jobs[next.id] = next
            next
        }

    suspend fun get(jobId: String): ProcessingJob? = mutex.withLock { jobs[jobId] }

    /** Immutable snapshot of all jobs, newest-created first. */
    suspend fun snapshot(): List<ProcessingJob> = mutex.withLock {
        jobs.values.sortedByDescending { it.createdAt }
    }

    suspend fun size(): Int = mutex.withLock { jobs.size }
}
