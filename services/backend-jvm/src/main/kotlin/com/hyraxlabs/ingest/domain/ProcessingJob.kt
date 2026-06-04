package com.hyraxlabs.ingest.domain

import java.time.Instant
import java.util.UUID

/**
 * A unit of asynchronous work scheduled by the pipeline — typically an ingestion
 * cycle for a single partner. Immutable: state transitions return new copies.
 */
data class ProcessingJob(
    val id: String = UUID.randomUUID().toString(),
    val partnerSource: String,
    val status: JobStatus = JobStatus.PENDING,
    val createdAt: Instant = Instant.now(),
    val finishedAt: Instant? = null,
    /** Number of normalized materials produced; populated on completion. */
    val producedCount: Int = 0,
    /** Failure detail when [status] is [JobStatus.FAILED]. */
    val errorMessage: String? = null,
) {
    fun running(): ProcessingJob = copy(status = JobStatus.RUNNING)

    fun completed(producedCount: Int): ProcessingJob =
        copy(status = JobStatus.COMPLETED, producedCount = producedCount, finishedAt = Instant.now())

    fun failed(error: String): ProcessingJob =
        copy(status = JobStatus.FAILED, errorMessage = error, finishedAt = Instant.now())
}
