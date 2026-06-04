package com.hyraxlabs.ingest.scheduler

import com.hyraxlabs.ingest.domain.Material
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import org.slf4j.LoggerFactory
import java.util.concurrent.atomic.AtomicInteger
import kotlin.time.Duration

/**
 * Coroutine-based scheduler that runs an [IngestionPipeline] cycle on a fixed
 * interval until cancelled.
 *
 * Uses structured concurrency: [start] launches a child coroutine in the supplied
 * [CoroutineScope]; cancelling that scope (or the returned [Job]) stops the
 * schedule cleanly. The schedule loop is cooperative — it checks [isActive] and
 * suspends via [delay] rather than blocking a thread.
 */
class JobScheduler(
    private val scope: CoroutineScope,
    private val pipeline: IngestionPipeline,
) {
    private val log = LoggerFactory.getLogger(JobScheduler::class.java)
    private val cyclesRun = AtomicInteger(0)

    /** Number of completed cycles since the scheduler started. */
    val completedCycles: Int get() = cyclesRun.get()

    /**
     * Starts the recurring schedule. The first cycle runs immediately, then one
     * runs every [interval] until the coroutine is cancelled.
     *
     * @param interval delay between the start of consecutive cycles
     * @param onCycle optional callback invoked with each cycle's results
     * @return the [Job] controlling the schedule
     */
    fun start(interval: Duration, onCycle: (suspend (List<Material>) -> Unit)? = null): Job =
        scope.launch {
            log.info("Scheduler started (interval={})", interval)
            while (isActive) {
                runOnce(onCycle)
                delay(interval)
            }
        }

    /**
     * Runs exactly one cycle. Exposed for one-shot demos and for tests that drive
     * the pipeline deterministically without waiting on the interval.
     */
    suspend fun runOnce(onCycle: (suspend (List<Material>) -> Unit)? = null): List<Material> {
        val cycle = cyclesRun.incrementAndGet()
        log.info("Running ingestion cycle #{}", cycle)
        val results = pipeline.runCycle()
        onCycle?.invoke(results)
        return results
    }
}
