package com.hyraxlabs.ingest.partner

import com.hyraxlabs.ingest.domain.SupplierRecord

/**
 * Abstraction over a third-party supplier-material partner API.
 *
 * Implementations may be written in Kotlin or Java (see [SampleAlphaPartnerClient]
 * and the Java `LegacyBetaPartnerClient`). Calls model network I/O and are expected
 * to be invoked from a coroutine on an I/O dispatcher.
 */
interface PartnerApiClient {
    /** Stable identifier for this partner, used as [SupplierRecord.partnerSource]. */
    val source: String

    /**
     * Fetches the current batch of supplier records from the partner.
     *
     * @throws PartnerApiException if the partner feed is unavailable or malformed.
     */
    fun fetchRecords(): List<SupplierRecord>
}

/** Raised when a partner feed cannot be retrieved or parsed. */
class PartnerApiException(message: String, cause: Throwable? = null) :
    RuntimeException(message, cause)
